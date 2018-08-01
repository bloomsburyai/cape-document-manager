import random
from collections import OrderedDict
from typing import List, Dict, Iterable, Optional
from cape_document_manager.document_manager_core import Retriever, Retrievable, Indexable, AUTOFILL, SearchResult, \
    roundrobin
from cape_api_helpers.exceptions import UserException
from cape_api_helpers.text_responses import *
import calendar
from dataclasses import dataclass, field
from itertools import chain
from cytoolz import compose
from uuid import uuid4
from datetime import datetime


@dataclass
class AnnotationAnswer(Indexable):
    annotation_answer_id: str = field(default_factory=compose(str, uuid4))
    # available_getters, left empty to be auto-filled when adding to Index
    user_id: str = field(default=AUTOFILL)
    document_id: str = field(default=AUTOFILL)
    page: int = field(default=AUTOFILL)


@dataclass
class AnnotationQuestion(Indexable):
    canonical: bool = field(default=False)
    annotation_question_id: str = field(default_factory=compose(str, uuid4))
    # available_getters, left empty to be auto-filled when adding to Index
    user_id: str = field(default=AUTOFILL)
    document_id: str = field(default=AUTOFILL)
    page: int = field(default=AUTOFILL)


@dataclass
class Annotation(Retrievable):
    user_id: str = field(default=None)
    page: int = field(default=None)
    document_id: Optional[str] = field(default=None)
    metadata: Dict[str, str] = field(default=dict)
    answers: Dict[str, AnnotationAnswer] = field(default=dict)
    questions: Dict[str, AnnotationQuestion] = field(default=dict)
    created: datetime = field(default_factory=datetime.now)
    modified: datetime = field(default_factory=datetime.now)

    @staticmethod
    def transformer(annotation: 'Annotation') -> Iterable[Indexable]:
        return iter(chain(annotation.questions.values(), annotation.answers.values()))

    @property
    def canonical(self) -> AnnotationQuestion:
        return next(filter(lambda x: x.canonical, self.questions.values()))

    @property
    def not_canonical(self) -> Iterable[AnnotationQuestion]:
        return iter(filter(lambda x: not x.canonical, self.questions.values()))


class AnnotationStore:
    _retriever: Retriever = Retriever('annotationRetriever', transformations=[Annotation.transformer])

    @staticmethod
    def _modify_annotation(modified_annotation: Annotation):
        modified_annotation.modified = datetime.now()
        AnnotationStore._retriever.upsert_document(modified_annotation)

    @staticmethod
    def _get_user_annotation(user_id: str, annotation_id: str) -> Annotation:
        return next(AnnotationStore._retriever.get(UserException(ERROR_ANNOTATION_DOES_NOT_EXIST % annotation_id),
                                                   **{'user_id': user_id, Annotation.unique_id_field(): annotation_id}))

    @staticmethod
    def _get_user_question_annotation(user_id: str, question_id: str) -> Annotation:
        return next(AnnotationStore._retriever.get(
            UserException(ERROR_QUESTION_DOES_NOT_EXIST % question_id), user_id=user_id,
            annotation_question_id=question_id))

    @staticmethod
    def _get_user_answer_annotation(user_id: str, answer_id: str) -> Annotation:
        return next(AnnotationStore._retriever.get(
            UserException(ERROR_ANSWER_DOES_NOT_EXIST % answer_id),
            **{'user_id': user_id, 'annotation_answer_id': answer_id}))

    @staticmethod
    def similar_annotations(user_id: str, similar_query: str,
                            document_ids: List[str] = (), saved_replies: Optional[bool] = None) -> List[dict]:
        """

        :param user_id:
        :param similar_query:
        :param document_ids:
        :param saved_replies: If True only return saved replies (annotations without document_ids),
                              if False only return annotations with document_ids,
                              if None return both
        :return:
        """
        selections_kwargs = [{'user_id': user_id}]

        if saved_replies is True:
            selections_kwargs[0]['document_id'] = None
        elif document_ids:
            selections_kwargs = [{'document_id': document_id, **selection}
                                 for document_id in document_ids
                                 for selection in selections_kwargs]
        elif saved_replies is False:
            selections_kwargs[0]['document_id__ne'] = None

        annotation_results: Iterable[SearchResult] = roundrobin(*(
            AnnotationStore._retriever.retrieve(similar_query, **selection) for selection in selections_kwargs))
        seen = set()
        seen_add = seen.add
        similar_annotations = []
        for annotation_result in annotation_results:
            annotation_obj: Annotation = annotation_result.get_retrievable()
            unique_id = annotation_obj.unique_id
            if unique_id not in seen:
                seen_add(unique_id)
                similar_annotations.append({
                    "answerText": random.choice(list(annotation_obj.answers.values())).content,
                    "confidence": annotation_result.matched_score,
                    "sourceType": "saved_reply" if annotation_obj.document_id is None else "annotation",
                    "sourceId": unique_id,
                    "matchedQuestion": annotation_result.matched_content,
                    "page": annotation_obj.page,
                    "metadata": annotation_obj.metadata,
                })
        return similar_annotations

    @staticmethod
    def get_annotations(user_id: str, search_term: str = None, annotation_ids: List[str] = (),
                        document_ids: List[str] = (), pages: List[int] = (), saved_replies: bool = None) -> List[dict]:
        """
        Get annotations
        :param user_id:
        :param search_term:
        :param annotation_ids:
        :param document_ids:
        :param pages:
        :param saved_replies: If True only return saved replies (annotations without document_ids),
                              if False only return annotations with document_ids,
                              if None return both
        :return:
        """
        selections_kwargs = [{'user_id': user_id, 'phrase': search_term if search_term else '*'}]
        if saved_replies is True:
            selections_kwargs[0]['document_id'] = None
        elif document_ids:
            selections_kwargs = [{'document_id': document_id, **selection}
                                 for document_id in document_ids
                                 for selection in selections_kwargs]
        elif saved_replies is False:
            selections_kwargs[0]['document_id__ne'] = None
        if annotation_ids:
            selections_kwargs = [{Annotation.unique_id_field(): annotation_id, **selection}
                                 for annotation_id in annotation_ids
                                 for selection in selections_kwargs]
        if pages:
            selections_kwargs = [{'page': page, **selection}
                                 for page in pages
                                 for selection in selections_kwargs]
        annotations: Iterable[Annotation] = roundrobin(*(
            AnnotationStore._retriever.get(**selection) for selection in selections_kwargs))
        return list(OrderedDict(
            (annotation.unique_id, {"id": annotation.unique_id,
                                    "canonicalQuestion": annotation.canonical.content,
                                    "answers": [{
                                        "id": answer.annotation_answer_id,
                                        "answer": answer.content
                                    } for answer in annotation.answers.values()],
                                    "paraphraseQuestions": [{
                                        "id": question.annotation_question_id,
                                        "question": question.content
                                    } for question in annotation.not_canonical],
                                    "document_id": annotation.document_id,
                                    "page": annotation.page,
                                    "metadata": annotation.metadata,
                                    "created": calendar.timegm(annotation.created.utctimetuple()),
                                    "modified": calendar.timegm(annotation.modified.utctimetuple()),
                                    }) for annotation in annotations).values())

    @staticmethod
    def create_annotation(user_id: str, question: str, answer: str, document_id: str = None, page: int = None,
                          metadata: dict = None):
        annotation_answer = AnnotationAnswer(content=answer)
        annotation_question = AnnotationQuestion(content=question, canonical=True)
        annotation = Annotation(user_id=user_id, document_id=document_id, page=page,
                                metadata=metadata, answers={annotation_answer.annotation_answer_id: annotation_answer},
                                questions={annotation_question.annotation_question_id: annotation_question})
        AnnotationStore._retriever.upsert_document(annotation)
        return {"annotationId": annotation.unique_id,
                "answerId": annotation_answer.annotation_answer_id}

    @staticmethod
    def delete_annotation(user_id: str, annotation_id: str):
        annotation = AnnotationStore._get_user_annotation(user_id, annotation_id)
        AnnotationStore._retriever.delete_document(annotation)
        return {"annotationId": annotation_id}

    @staticmethod
    def edit_canonical_question(user_id: str, annotation_id: str, question_text: str):
        annotation = AnnotationStore._get_user_annotation(user_id, annotation_id)
        annotation.canonical.content = question_text
        AnnotationStore._modify_annotation(annotation)
        return {"annotationId": annotation_id}

    @staticmethod
    def add_paraphrase_question(user_id: str, annotation_id: str, question_text: str):
        annotation = AnnotationStore._get_user_annotation(user_id, annotation_id)
        annotation_question = AnnotationQuestion(content=question_text)
        annotation.questions[annotation_question.annotation_question_id] = annotation_question
        AnnotationStore._modify_annotation(annotation)
        return {"questionId": annotation_question.annotation_question_id}

    @staticmethod
    def delete_paraphrase_question(user_id: str, question_id: str):
        annotation = AnnotationStore._get_user_question_annotation(user_id, question_id)
        if annotation.canonical.annotation_question_id == question_id:
            raise UserException(ERROR_QUESTION_DOES_NOT_EXIST % question_id)
        del annotation.questions[question_id]
        AnnotationStore._modify_annotation(annotation)
        return {"questionId": question_id}

    @staticmethod
    def edit_paraphrase_question(user_id: str, question_id: str, question_text: str):
        annotation = AnnotationStore._get_user_question_annotation(user_id, question_id)
        if annotation.canonical.annotation_question_id == question_id:
            raise UserException(ERROR_QUESTION_DOES_NOT_EXIST % question_id)
        annotation.questions[question_id].content = question_text
        AnnotationStore._modify_annotation(annotation)
        return {"questionId": question_id}

    @staticmethod
    def add_answer(user_id: str, annotation_id: str, answer: str):
        annotation = AnnotationStore._get_user_annotation(user_id, annotation_id)
        annotation_answer = AnnotationAnswer(content=answer)
        annotation.answers[annotation_answer.annotation_answer_id] = annotation_answer
        AnnotationStore._modify_annotation(annotation)
        return {"answerId": annotation_answer.annotation_answer_id}

    @staticmethod
    def edit_answer(user_id: str, answer_id: str, answer_text: str):
        annotation = AnnotationStore._get_user_answer_annotation(user_id, answer_id)
        annotation.answers[answer_id].content = answer_text
        AnnotationStore._modify_annotation(annotation)
        return {'answerId': answer_id}

    @staticmethod
    def delete_answer(user_id: str, answer_id: str):
        annotation = AnnotationStore._get_user_answer_annotation(user_id, answer_id)
        if len(annotation.answers) < 2:
            raise UserException(ERROR_ANNOTATION_LAST_ANSWER)
        del annotation.answers[answer_id]
        AnnotationStore._modify_annotation(annotation)
        return {'answerId': answer_id}
