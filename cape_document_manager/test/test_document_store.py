import pytest
from cape_api_helpers.exceptions import UserException
from cape_document_manager.tables import init_db
from cape_document_manager.document_store import DocumentStore, DocumentRecord, DocumentChunk
from pprint import pprint

_DOCUMENT_TEXTS = [

    'The Normans (Norman: Nourmands; French: Normands; Latin: Normanni) were the people who in '
    'the 10th and 11th centuries gave their name to Normandy, a region in France. They were '
    'descended from Norse ("Norman" comes from "Norseman") raiders and pirates from Denmark, '
    'Iceland and Norway who, under their leader Rollo, agreed to swear fealty to King Charles '
    'III of West Francia. Through generations of assimilation and mixing with the native '
    'Frankish and Roman-Gaulish populations, their descendants would gradually merge with the '
    'Carolingian-based cultures of West Francia. The distinct cultural and ethnic identity of '
    'the Normans emerged initially in the first half of the 10th century, and it continued to '
    'evolve over the succeeding centuries.',

    "The Amazon rainforest (Portuguese: Floresta Amazônica or Amazônia; Spanish: Selva Amazónica, "
    "Amazonía or usually Amazonia; French: Forêt amazonienne; Dutch: Amazoneregenwoud), also known in "
    "English as Amazonia or the Amazon Jungle, is a moist broadleaf forest that covers most of the "
    "Amazon basin of South America. This basin encompasses 7,000,000 square kilometres (2,700,000 sq "
    "mi), of which 5,500,000 square kilometres (2,100,000 sq mi) are covered by the rainforest. This "
    "region includes territory belonging to nine nations. The majority of the forest is contained "
    "within Brazil, with 60% of the rainforest, followed by Peru with 13%, Colombia with 10%, and with "
    "minor amounts in Venezuela, Ecuador, Bolivia, Guyana, Suriname and French Guiana. States or "
    "departments in four nations contain \"\n Amazonas\" in their names. The Amazon represents over "
    "half of the planet's remaining rainforests, and comprises the largest and most biodiverse tract of "
    "tropical rainforest in the world, with an estimated 390 billion individual trees divided into "
    "16,000 species.",

    """The Victoria and Albert Museum (often abbreviated as the V&A), London, is the world's largest 
    museum of decorative arts and design, housing a permanent collection of over 4.5 million objects. It was 
    founded in 1852 and named after Queen Victoria and Prince Albert. The V&A is located in the Brompton district 
    of the Royal Borough of Kensington and Chelsea, in an area that has become known as "Albertopolis" because of 
    its association with Prince Albert, the Albert Memorial and the major cultural institutions with which he was 
    associated. These include the Natural History Museum, the Science Museum and the Royal Albert Hall. The 
    museum is a non-departmental public body sponsored by the Department for Culture, Media and Sport. Like other 
    national British museums, entrance to the museum has been free since 2001.""",

    """one plus one makes two""",

    """The Apollo program, also known as Project Apollo, was the third United States human spaceflight 
    program carried out by the National Aeronautics and Space Administration (NASA), which accomplished landing 
    the first humans on the Moon from 1969 to 1972. First conceived during Dwight D. Eisenhower's administration 
    as a three-man spacecraft to follow the one-man Project Mercury which put the first Americans in space, 
    Apollo was later dedicated to President John F. Kennedy's national goal of "landing a man on the Moon and 
    returning him safely to the Earth" by the end of the 1960s, which he proposed in a May 25, 1961, address to 
    Congress. Project Mercury was followed by the two-man Project Gemini (1962–66). The first manned flight of 
    Apollo was in 1968.""",

    """European Union law is a body of treaties and legislation, such as Regulations and Directives, 
    which have direct effect or indirect effect on the laws of European Union member states. The three sources of 
    European Union law are primary law, secondary law and supplementary law. The main sources of primary law are 
    the Treaties establishing the European Union. Secondary sources include regulations and directives which are 
    based on the Treaties. The legislature of the European Union is principally composed of the European 
    Parliament and the Council of the European Union, which under the Treaties may establish secondary law to 
    pursue the objective set out in the Treaties.""",

    """Oxygen is a chemical element with symbol O and atomic number 8. It is a member of the chalcogen 
    group on the periodic table and is a highly reactive nonmetal and oxidizing agent that readily forms 
    compounds (notably oxides) with most elements. By mass, oxygen is the third-most abundant element in the 
    universe, after hydrogen and helium. At standard temperature and pressure, two atoms of the element bind to 
    form dioxygen, a colorless and odorless diatomic gas with the formula O. 2. Diatomic oxygen gas constitutes 
    20.8% of the Earth's atmosphere. However, monitoring of atmospheric oxygen levels show a global downward 
    trend, because of fossil-fuel burning. Oxygen is the most abundant element by mass in the Earth's crust as 
    part of oxide compounds such as silicon dioxide, making up almost half of the crust's mass.""",

    """The plague disease, caused by Yersinia pestis, is enzootic (commonly present) in populations of 
    fleas carried by ground rodents, including marmots, in various areas including Central Asia, Kurdistan, 
    Western Asia, Northern India and Uganda. Nestorian graves dating to 1338–39 near Lake Issyk Kul in Kyrgyzstan 
    have inscriptions referring to plague and are thought by many epidemiologists to mark the outbreak of the 
    epidemic, from which it could easily have spread to China and India. In October 2010, medical geneticists 
    suggested that all three of the great waves of the plague originated in China. In China, the 13th century 
    Mongol conquest caused a decline in farming and trading. However, economic recovery had been observed at the 
    beginning of the 14th century. In the 1330s a large number of natural disasters and plagues led to widespread 
    famine, starting in 1331, with a deadly plague arriving soon after. Epidemics that may have included plague 
    killed an estimated 25 million Chinese and other Asians during the 15 years before it reached Constantinople 
    in 1347.""",

    """The role of teacher is often formal and ongoing, carried out at a school or other place of 
    formal education. In many countries, a person who wishes to become a teacher must first obtain specified 
    professional qualifications or credentials from a university or college. These professional qualifications 
    may include the study of pedagogy, the science of teaching. Teachers, like other professionals, may have to 
    continue their education after they qualify, a process known as continuing professional development. Teachers 
    may use a lesson plan to facilitate student learning, providing a course of study which is called the 
    curriculum.""",
]

_LOGIN = 'bla@bla.com'


@pytest.fixture()
def reset_db():
    init_db(reset_database=True)


def test_create_and_delete(reset_db):
    created1 = DocumentStore.create_document(_LOGIN, 'first doc', 'test', _DOCUMENT_TEXTS[0])
    assert created1 == {'documentId': 'dd5c8526091ce0e937a062da23833808b4e54d9ce41cdc101173265b6a718bbd'}
    assert DocumentStore.get_documents(_LOGIN) == DocumentStore.get_documents(_LOGIN,
                                                                              document_ids=[created1['documentId']])

    created = DocumentStore.create_document(_LOGIN, 'first doc', 'test', _DOCUMENT_TEXTS[-1], document_id='bla.txt')
    assert created == {'documentId': 'bla.txt'}
    assert len(DocumentStore.get_documents(_LOGIN)) == 2
    assert DocumentStore.get_documents(_LOGIN, document_ids=[created['documentId']])[0]['text'] == _DOCUMENT_TEXTS[-1]

    with pytest.raises(UserException):  # same document_id
        DocumentStore.create_document(_LOGIN, 'first docs', 'test', _DOCUMENT_TEXTS[1], document_id='bla.txt')
    with pytest.raises(UserException):  # same auto generated document_id
        DocumentStore.create_document(_LOGIN, 'first docs', 'test', _DOCUMENT_TEXTS[0])
    with pytest.raises(UserException):  # does not exist
        DocumentStore.delete_document('bla', 'bla')
    deleted = DocumentStore.delete_document(_LOGIN, 'bla.txt')
    assert deleted['documentId'] == 'bla.txt'
    assert DocumentStore.get_documents(_LOGIN) == DocumentStore.get_documents(_LOGIN,
                                                                              document_ids=[created1['documentId']])
    with pytest.raises(UserException):  # already deleted
        DocumentStore.delete_document(_LOGIN, 'bla.txt')
    deleted = DocumentStore.delete_document(_LOGIN, created1['documentId'])
    assert deleted['documentId'] == created1['documentId']
    assert len(DocumentStore.get_documents(_LOGIN)) == 0


def test_simple_search(reset_db):
    for idx, doc_text in enumerate(_DOCUMENT_TEXTS):
        DocumentStore.create_document(_LOGIN, 'Title of doc %d' % idx, 'test', doc_text)

    assert len(DocumentStore.get_documents(_LOGIN)) == 9
    assert len(DocumentStore.get_documents(_LOGIN, search_term='normans')) == 1
    assert len(DocumentStore.get_documents(_LOGIN, search_term='f80q35jf98')) == 0
    assert DocumentStore.get_documents(_LOGIN, search_term='one')[0]['text'] == _DOCUMENT_TEXTS[3]

def test_chunk_search(reset_db):
    get_embeddings_function = len #in prod this would be the embedding generation function

    #Insert document in DB
    for idx, doc_text in enumerate(_DOCUMENT_TEXTS):
        DocumentStore.create_document(_LOGIN, 'Title of doc %d' % idx, 'test', doc_text,
                                      get_embedding=get_embeddings_function)


    # Get the search results of chunks, with a single SQL query,
    # do this if all you need is the number of results and/or text content and/or confidence scores
    matched_results = list(DocumentStore.search_chunks(_LOGIN, 'who were the normans?'))
    assert len(matched_results) == 8
    assert " were descended from Norse " in matched_results[0].matched_content

    assert matched_results[0].matched_score > matched_results[1].matched_score
    assert matched_results[1].matched_score > 0.0

    # Reader workers can make an extra SQL query to retrieve the fields of DocumentChunk as strings
    # {'chunk_idx': '0',
    # 'document_id': 'dd5c8526091ce0e937a062da23833808b4e54d9ce41cdc101173265b6a718bbd',
    # 'embedding': '742',
    # 'number_of_words': '113',
    # 'overlap_after': '',  #empty because there is no text after this chunk
    # 'overlap_before': '', #empty because there is no text before this chunk
    # 'text_span': '[0, 742]',
    # 'unique_id': "('bla@bla.com', "
    #              "'dd5c8526091ce0e937a062da23833808b4e54d9ce41cdc101173265b6a718bbd')",
    # 'user_id': 'bla@bla.com'}
    fields = matched_results[0].get_indexable_string_fields()
    assert fields['embedding'] == str(len(matched_results[0].matched_content)) # in prod would be string of an array

    # Only if absolutely necessary but should not be used when machine reading
    # you can retrieve the full DocumentRecord object
    # which includes all chunks, this is "slow" as we are unpickling from the DB
    document_record : DocumentRecord = matched_results[0].get_retrievable()
    assert document_record.unique_id == str((document_record.user_id,document_record.document_id))
    assert document_record.text == _DOCUMENT_TEXTS[0]
    assert isinstance(next(iter(document_record.chunks.values())),DocumentChunk)
    assert len(document_record.chunks) == 1

    # pprint(document_record)

def test_exact_match(reset_db):
    #Insert document in DB
    for idx, doc_text in enumerate(_DOCUMENT_TEXTS):
        DocumentStore.create_document(_LOGIN, 'Title of doc %d' % idx, 'test', doc_text)

    #exact match is expected to return a perfect score
    matched_results = list(DocumentStore.search_chunks(_LOGIN, 'one plus one makes two'))
    assert matched_results[0].matched_content == 'one plus one makes two'
    assert matched_results[0].matched_score == 1.0

    #close match is expected when the punctuation and trailing spaces are removed
    matched_results = list(DocumentStore.search_chunks(_LOGIN, ' one ,plus+ one makes two !!'))
    assert matched_results[0].matched_content == 'one plus one makes two'
    assert matched_results[0].matched_score == 0.99


if __name__ == '__main__':
    print("Launching single test")
    test_create_and_delete(reset_db())
    print("Done")
