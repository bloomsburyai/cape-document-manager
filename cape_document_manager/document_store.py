from typing import List, Dict, Iterable, Optional, Tuple, Any, Callable, Generator

from cape_splitter.splitter_core import Splitter

from cape_document_manager.document_manager_core import Retriever, Retrievable, Indexable, AUTOFILL, SearchResult
from cape_api_helpers.exceptions import UserException
from cape_api_helpers.text_responses import *
import calendar
from dataclasses import dataclass, field
from itertools import chain
from datetime import datetime
from hashlib import sha256

from cape_document_manager.document_manager_settings import SPLITTER_WORDS_PER_CHUNK, SPLITTER_WORDS_OVERLAP_BEFORE, \
    SPLITTER_WORDS_OVERLAP_AFTER


@dataclass
class DocumentChunk(Indexable):
    chunk_idx: int
    overlap_before: str
    overlap_after: str
    text_span: Tuple[int, int]
    number_of_words: int
    # Auto-filled on post_init()
    embedding: Any = field(default=None)
    # available_getters, left empty to be auto-filled when adding to Index
    user_id: str = field(default=AUTOFILL)
    document_id: str = field(default=AUTOFILL)


@dataclass
class DocumentRecord(Retrievable):
    user_id: str = field(default=None)
    document_id: Optional[str] = field(default=None)
    title: Optional[str] = field(default=None)
    origin: Optional[str] = field(default=None)
    text: Optional[str] = field(default=None)
    document_type: Optional[str] = field(default=None)
    created: datetime = field(default_factory=datetime.now)
    chunks: Dict[int, DocumentChunk] = field(default=dict)
    get_embedding: Callable[[str], Any] = field(default=len)

    def __post_init__(self):
        self.unique_id = str((self.user_id, self.document_id))
        spl = Splitter(["document_id"], [self.text], words_per_group=SPLITTER_WORDS_PER_CHUNK,
                       max_overlap_before=SPLITTER_WORDS_OVERLAP_BEFORE,
                       max_overlap_after=SPLITTER_WORDS_OVERLAP_AFTER)
        self.chunks = {
            group.idx:
                DocumentChunk(chunk_idx=group.idx, content=group.text, overlap_before=group.overlap_before,
                              overlap_after=group.overlap_after, text_span=group.text_span,
                              number_of_words=group.number_of_words,
                              embedding=self.get_embedding(group.overlap_before + group.text + group.overlap_after))
            for doc_id in spl.document_groups
            for group in spl.document_groups[doc_id]
        }

    @staticmethod
    def transformer(document: 'DocumentRecord') -> Iterable[DocumentChunk]:
        return document.chunks.values()


class DocumentStore:
    _retriever: Retriever = Retriever('documentRetriever', transformations=[DocumentRecord.transformer])

    @staticmethod
    def create_document(user_id: str, title: str, origin: str, text: str, document_type: str = 'text',
                        document_id: Optional[str] = None, replace=False, get_embedding=None):
        if document_id is None:
            document_id = sha256(text.encode('utf-8')).hexdigest()
        fields = dict(user_id=user_id, title=title, document_id=document_id, origin=origin, text=text,
                      document_type=document_type)
        if get_embedding is not None:
            fields['get_embedding'] = get_embedding
        document = DocumentRecord(**fields)
        if not replace:
            docs = DocumentStore._retriever.get(**{DocumentRecord.unique_id_field(): document.unique_id})
            if list(docs):
                raise UserException(ERROR_DOCUMENT_ALREADY_EXISTS % document_id)
        DocumentStore._retriever.upsert_document(document)
        return {"documentId": document.document_id}

    @staticmethod
    def _get_user_document(user_id: str, document_id: str) -> DocumentRecord:
        return next(DocumentStore._retriever.get(UserException(ERROR_DOCUMENT_DOES_NOT_EXIST % document_id),
                                                 **{'user_id': user_id, 'document_id': document_id}))

    @staticmethod
    def delete_document(user_id: str, document_id: str):
        document = DocumentStore._get_user_document(user_id, document_id)
        DocumentStore._retriever.delete_document(document)
        return {'documentId': document_id}

    @staticmethod
    def get_documents(user_id: str, search_term: str = None, document_ids: List[str] = ()):
        selections_kwargs = [{'user_id': user_id, 'phrase': search_term if search_term else '*'}]
        if document_ids:
            selections_kwargs = [{'document_id': document_id, **selection}
                                 for document_id in document_ids
                                 for selection in selections_kwargs]
        docs: Iterable[DocumentRecord] = chain.from_iterable(
            DocumentStore._retriever.get(**selection) for selection in selections_kwargs)
        return [{"id": doc.document_id,
                 "title": doc.title,
                 "origin": doc.origin,
                 "text": doc.text,
                 "type": doc.document_type,
                 "created": calendar.timegm(doc.created.utctimetuple()),
                 } for doc in docs]

    @staticmethod
    def search_chunks(user_id: str, query: str, document_ids: List[str] = ()) -> Generator[SearchResult, None, None]:
        selections_kwargs = [{'user_id': user_id}]
        if document_ids:
            selections_kwargs = [{'document_id': document_id, **selection}
                                 for document_id in document_ids
                                 for selection in selections_kwargs]
        search_results: Iterable[SearchResult] = chain.from_iterable(
            DocumentStore._retriever.retrieve(query=query, **selection) for selection in selections_kwargs)
        yield from search_results
