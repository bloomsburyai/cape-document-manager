import pytest
from cape_api_helpers.exceptions import UserException
from cape_document_manager.tables import init_db
from cape_document_manager.annotation_store import AnnotationStore
from pprint import pprint
from collections import OrderedDict

LOGIN = 'bla@bla.com'


def test_annotations():
    init_db(reset_database=True)
    question = "What is the meaning of life?"
    answer = "42"
    document_id = "Pizza"
    AnnotationStore.create_annotation(LOGIN, question, answer, document_id)
    annotations = AnnotationStore.get_annotations(LOGIN)
    assert len(annotations) == 1

    annotations = AnnotationStore.get_annotations(LOGIN, document_ids=[document_id])
    assert len(annotations) == 1

    annotation_id = annotations[0]['id']
    annotations = AnnotationStore.get_annotations(LOGIN, annotation_ids=[annotation_id])
    assert len(annotations) == 1
    assert len(annotations[0]['answers']) == 1

    answer_id = AnnotationStore.add_answer(LOGIN, annotation_id, "New answer")['answerId']
    annotations = AnnotationStore.get_annotations(LOGIN, annotation_ids=[annotation_id])
    assert len(annotations[0]['answers']) == 2

    AnnotationStore.edit_answer(LOGIN, answer_id, "Old answer")
    annotations = AnnotationStore.get_annotations(LOGIN, annotation_ids=[annotation_id])
    assert annotations[0]['answers'][1]['answer'] == "Old answer"

    AnnotationStore.delete_answer(LOGIN, answer_id)
    annotations = AnnotationStore.get_annotations(LOGIN, annotation_ids=[annotation_id])
    assert len(annotations[0]['answers']) == 1

    with pytest.raises(UserException):
        AnnotationStore.edit_answer(LOGIN, answer_id, "editing a deleted answer")

    with pytest.raises(UserException):
        AnnotationStore.delete_answer(LOGIN, annotations[0]['answers'][0]['id'])

    AnnotationStore.edit_canonical_question(LOGIN, annotation_id, "What is a new question?")
    annotations = AnnotationStore.get_annotations(LOGIN, annotation_ids=[annotation_id])
    assert annotations[0]['canonicalQuestion'] == "What is a new question?"

    with pytest.raises(UserException):
        AnnotationStore.edit_canonical_question(LOGIN, 'blas', "What is a new question?")

    question_id = AnnotationStore.add_paraphrase_question(LOGIN, annotation_id, "Another question?")['questionId']
    annotations = AnnotationStore.get_annotations(LOGIN, annotation_ids=[annotation_id])
    assert annotations[0]['paraphraseQuestions'][0]['question'] == 'Another question?'

    AnnotationStore.edit_paraphrase_question(LOGIN, question_id, "Yet another question?")
    annotations = AnnotationStore.get_annotations(LOGIN, annotation_ids=[annotation_id])
    assert annotations[0]['paraphraseQuestions'][0]['question'] == 'Yet another question?'

    AnnotationStore.delete_paraphrase_question(LOGIN, question_id)
    annotations = AnnotationStore.get_annotations(LOGIN, annotation_ids=[annotation_id])
    assert len(annotations[0]['paraphraseQuestions']) == 0

    question = "What should I search for?"
    answer = "This."
    document_id = "Pizza"
    AnnotationStore.create_annotation(LOGIN, question, answer, document_id)
    annotations = AnnotationStore.get_annotations(LOGIN, search_term='SEARCH')
    assert len(annotations) == 1
    annotations = AnnotationStore.get_annotations(LOGIN, search_term='what')
    assert len(annotations) == 2
    annotations = AnnotationStore.get_annotations(LOGIN, search_term='this')
    assert len(annotations) == 1

    question = "What document is this in?"
    answer = "Another one."
    document_id = "Doc2"
    AnnotationStore.create_annotation(LOGIN, question, answer, document_id)
    annotations = AnnotationStore.get_annotations(LOGIN, document_ids=["Pizza"])
    assert len(annotations) == 2
    annotations = AnnotationStore.get_annotations(LOGIN, document_ids=["Doc2"])
    assert len(annotations) == 1

    AnnotationStore.delete_annotation(LOGIN, annotation_id)
    annotations = AnnotationStore.get_annotations(LOGIN, annotation_ids=[annotation_id])
    assert len(annotations) == 0

    with pytest.raises(UserException):
        AnnotationStore.edit_canonical_question(LOGIN, annotation_id, "What is a new question?")

    AnnotationStore.create_annotation(LOGIN, "What's the time?", "Bed time", "Night", page=4, metadata={
        'custom': 'testing'
    })
    annotations = AnnotationStore.get_annotations(LOGIN, document_ids=['Night'])
    assert len(annotations) == 1
    assert annotations[0]['page'] == 4
    assert annotations[0]['metadata']['custom'] == 'testing'

    annotations = AnnotationStore.get_annotations(LOGIN, document_ids=['Night'], pages=[1, 2, 3])
    assert len(annotations) == 0
    annotations = AnnotationStore.get_annotations(LOGIN, document_ids=['Night'], pages=[4, 5])
    assert len(annotations) == 1

    annotations_new = AnnotationStore.get_annotations(LOGIN, search_term="bed")
    assert len(annotations_new) == 1 and annotations[0]['id'] == annotations_new[0]['id']
    annotations_new = AnnotationStore.get_annotations(LOGIN, search_term="time")
    assert len(annotations_new) == 1 and annotations[0]['id'] == annotations_new[0]['id']
    annotations_new = AnnotationStore.get_annotations(LOGIN, search_term="98ahf98e")
    assert len(annotations_new) == 0

    AnnotationStore.create_annotation(LOGIN, "What's the time?", "yesterday")
    AnnotationStore.create_annotation(LOGIN, "What is the time", "today")

    # pprint(AnnotationStore.get_annotations(LOGIN))
    # pprint(AnnotationStore.get_annotations(LOGIN, search_term="What's the time?"))
    assert OrderedDict(
        map(lambda x: (x.unique_id, None), AnnotationStore._retriever.get(phrase="What's the time?"))) == OrderedDict(
        map(lambda x: (x.get_retrievable().unique_id, None),
            AnnotationStore._retriever.retrieve(query="What's the time?"))
    )
    assert OrderedDict(
        map(lambda x: (x.unique_id, None), AnnotationStore._retriever.get(phrase="What's the time?"))) == OrderedDict(
        map(lambda x: (x['sourceId'], None),
            AnnotationStore.similar_annotations(LOGIN, similar_query="What's the time?"))
    )
    pprint(AnnotationStore.similar_annotations(LOGIN, similar_query="What's the time?"))


def test_eval():
    init_db(reset_database=True)
    answer = "42"
    document_id = "Pizza"
    AnnotationStore.create_annotation(LOGIN, 'This is a potato bla', answer, document_id)
    AnnotationStore.create_annotation(LOGIN, 'Sandwich.', answer, document_id)
    AnnotationStore.create_annotation(LOGIN, 'Not a potato sandwich', answer, document_id)
    annotations = AnnotationStore.get_annotations(LOGIN)
    pprint(AnnotationStore.similar_annotations(LOGIN, similar_query="This is a potato."))


def test_saved_reply():
    init_db(reset_database=True)
    question = "What's the time, Mr Wolf?"
    answer = "Lunch time!"
    AnnotationStore.create_annotation(LOGIN, question, answer)
    AnnotationStore.create_annotation(LOGIN, question, answer, document_id='bla.txt')
    # return saved replies only
    annotations = AnnotationStore.similar_annotations(LOGIN, question, saved_replies=True)
    assert len(annotations) == 1
    assert annotations[0]["sourceType"] == "saved_reply"
    # return annotations only
    annotations = AnnotationStore.similar_annotations(LOGIN, question, saved_replies=False)
    assert len(annotations) == 1
    assert annotations[0]["sourceType"] == "annotation"
    # return both
    annotations = AnnotationStore.similar_annotations(LOGIN, question, saved_replies=None)
    assert len(annotations) == 2
    assert annotations[0]["sourceType"] != annotations[1]["sourceType"]


if __name__ == '__main__':
    print("Launching single test")
    test_saved_reply()
    print("Done")
