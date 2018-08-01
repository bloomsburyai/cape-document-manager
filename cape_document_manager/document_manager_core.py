import re
from typing import List, Callable, Iterable, Dict, Any, Union, Generator, Optional
from peewee import ModelSelect, JOIN, fn
from hashlib import sha256
import pickle
import zlib
from dataclasses import dataclass, field, asdict
from uuid import uuid4
from cytoolz import compose
from cape_document_manager.tables import Index, database, BlobData, Metadata, IndexDocument, Attachment, Document, \
    DocumentSearch
from functools import lru_cache
from cape_document_manager.document_manager_settings import LOCAL_UNPICKLING_LRU_CACHE_MAX_SIZE
from itertools import cycle, islice

AUTOFILL = "AUTO_FILL"
_MAX_RETRIEVER_SCORE = 0.98
_CASE_INVARIANT_NO_PUNCTUATION_SCORE = 0.99
_NON_WORD_CHARS = re.compile('[^0-9a-zA-Z\s]')


def roundrobin(*iterables):
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    num_active = len(iterables)
    nexts = cycle(iter(it).__next__ for it in iterables)
    while num_active:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            # Remove the iterator we just exhausted from the cycle.
            num_active -= 1
            nexts = cycle(islice(nexts, num_active))


@dataclass
class Retrievable:
    unique_id: str = field(default_factory=compose(str, uuid4))

    def dumps(self) -> bytes:
        return zlib.compress(pickle.dumps(self, pickle.HIGHEST_PROTOCOL), 9)

    @staticmethod
    def loads(value: bytes) -> Any:
        return pickle.loads(zlib.decompress(value))

    @staticmethod
    def unique_id_field() -> str:
        return 'unique_id'


@dataclass
class Indexable:
    """All the fields of this object will be converted to str(), content will be indexed."""
    content: str


Transformer = Callable[[Retrievable], Iterable[Indexable]]


@dataclass
class SearchResult:
    original_query: str
    matched_content: str
    matched_score: float  # higher is better
    _scout_result: Document

    def __post_init__(self):
        # since retriever does stemming and tokenizing we want to return perfect score for 'perfect' matches
        if self.original_query == self.matched_content:
            self.matched_score = 1.0
        elif re.sub(_NON_WORD_CHARS, "", self.original_query.lower().strip()).strip() == re.sub(_NON_WORD_CHARS
                , "", self.matched_content.lower().strip()).strip():
            self.matched_score = _CASE_INVARIANT_NO_PUNCTUATION_SCORE

    def get_retrievable(self) -> Retrievable:
        return Retriever._local_loading_cache(self._scout_result.attachments[0].hash, _HiddenState(self._scout_result))

    def get_indexable_string_fields(self) -> dict:
        return self._scout_result.get_metadata()


@dataclass
class _HiddenState:
    state: Any

    def __hash__(self):
        return hash(None)

    def __eq__(self, other: '_HiddenState'):
        return True


class Retriever():
    """Use Scout as a retriever.
    This implementation is meant to demonstrate how to integrate the document manager with retrieval.
    Integrations will typically use the existing Full text search or a new specialized one.
    """

    def __init__(self, name: str, transformations: List[Transformer]):
        """Initialize new retriever with the transformation functions where retrieval will be applied."""
        self.transformations = transformations
        self.name = name
        self.indexes = [Index.get_or_create(name=f'{name}-{idx}')[0] for idx, _ in enumerate(self.transformations)]

    @staticmethod
    @lru_cache(maxsize=LOCAL_UNPICKLING_LRU_CACHE_MAX_SIZE)
    def _local_loading_cache(unique_hash: str, result: _HiddenState) -> Retrievable:
        "Cache objects being unpickled"
        return Retrievable.loads(result.state.attachments[0].blob.data)

    @staticmethod
    def _unique_everseen(results: Iterable[Indexable]) -> Generator[Retrievable, None, None]:
        "List unique elements, preserving order. Remember all elements ever seen."
        seen = set()
        seen_add = seen.add
        for result in results:
            unique_hash = result.attachments[0].hash
            if unique_hash not in seen:
                seen_add(unique_hash)
                yield Retriever._local_loading_cache(unique_hash, _HiddenState(result))

    def _indexable_object_to_dict(self, indexable_object: Indexable, original_object: Retrievable) -> Dict:
        indexable_object_dict = {}
        for key, value in asdict(indexable_object).items():
            if value == AUTOFILL:
                value = getattr(original_object, key)
            if value is None:  # elif would cause errors since original object can have None values
                value = ''
            indexable_object_dict[key] = value
        return indexable_object_dict

    def _searchable_keys(self, keys: Dict[str, str]):
        return {key: (val if val is not None else '') for key, val in keys.items()}

    def upsert_document(self, original_object: Retrievable):
        self.delete_document(original_object)
        original_content_bytes = original_object.dumps()
        content_hash = sha256(original_content_bytes).hexdigest()
        with database.atomic():
            BlobData.get_or_create(hash=content_hash, data=original_content_bytes)
            for transformation in self.transformations:
                for indexable_chunk in transformation(original_object):
                    indexable_dict = self._indexable_object_to_dict(indexable_chunk, original_object)
                    for current_index in self.indexes:
                        document = current_index.index(
                            **{Retrievable.unique_id_field(): original_object.unique_id},
                            **indexable_dict)
                        Attachment.get_or_create(document=document, filename=content_hash, hash=content_hash,
                                                 mimetype='application/octet-stream')

    def _get_docids(self, original_object_or_id: Union[Retrievable, str]) -> ModelSelect:
        unique_id = original_object_or_id if isinstance(original_object_or_id, str) else original_object_or_id.unique_id
        where_clause = (Metadata.key == Retrievable.unique_id_field()) & (
                Metadata.value == unique_id)
        return Metadata.select(Metadata.document_id).where(where_clause).join(
            IndexDocument, on=(IndexDocument.document_id == Metadata.document_id)).where(
            IndexDocument.index << self.indexes)

    def delete_document(self, original_object_or_unique_id: Union[Retrievable, str]):
        with database.atomic():
            doc_ids = self._get_docids(original_object_or_unique_id)  # cached after 1st execution
            rows_deleted = IndexDocument.delete().where(IndexDocument.document_id << doc_ids).execute()
            if not rows_deleted:
                return
            Attachment.delete().where(Attachment.document_id << doc_ids).execute()
            Document.delete().where(Document.docid << doc_ids).execute()
            Metadata.delete().where(Metadata.document_id << doc_ids).execute()
            BlobData.delete().where(
                BlobData.hash << (BlobData
                                  .select(BlobData.hash)
                                  .join(Attachment, on=(BlobData.hash == Attachment.hash), join_type=JOIN.LEFT_OUTER)
                                  .group_by(BlobData)
                                  .having(fn.Count(Attachment.hash) == 0)
                                  )).execute()

    def _query_to_phrase(self, query: str):
        """Proxy a retriever by making a sqllite full-text search with optional tokens."""
        return '"' + '" OR "'.join(re.sub(_NON_WORD_CHARS, "", query.lower().strip()).split()) + '"'

    def retrieve(self, query: str, limit: Optional[int] = None, **keys) -> Generator[SearchResult, None, None]:
        yield from (
            SearchResult(
                original_query=query,
                matched_content=result.content,
                matched_score=result.score * -_MAX_RETRIEVER_SCORE,
                _scout_result=result)
            for result in
            DocumentSearch().search(phrase=self._query_to_phrase(query), index=self.indexes, ranking='rank_similarity',
                                    **self._searchable_keys(keys)).limit(limit))

    def get(self, exception_to_raise_on_empty=None, **keys) -> Generator[Retrievable, None, None]:
        for key, value in keys.items():
            if value is None:
                keys[key] = ''
        if 'phrase' not in keys:
            keys['phrase'] = '*'
        elif keys['phrase'] != '*':
            keys['phrase'] = self._query_to_phrase(keys['phrase'])
        results = DocumentSearch().search(index=self.indexes, ranking='rank_similarity', **self._searchable_keys(keys))
        if exception_to_raise_on_empty is not None and len(results) == 0:
            raise exception_to_raise_on_empty
        yield from Retriever._unique_everseen(results)
