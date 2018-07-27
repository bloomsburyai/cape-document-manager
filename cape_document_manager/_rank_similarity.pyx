from libc.math cimport log, sqrt, fmax


def rank_similarity(py_match_info, *raw_weights):
    # Usage: pseudo_similarity(matchinfo(table, 'pcnalx'), 1,...)
    # An approximation of the tf-idf cosine similarity that computes norms based on term intersection only
    # raw_weights is an array of weights per column
    cdef:
        unsigned int *match_info
        bytes _match_info_buf = bytes(py_match_info)
        char *match_info_buf = _match_info_buf
        int term_count, col_count, initial_position, initial_row_col
        double total_docs, term_frequency, docs_with_hits, idf, tfidf_doc, tfidf_query, score, col_weight
        double pseudo_norm_doc = 0.0
        double norm_query = 0.0
        double component_sum = 0.0

    match_info = <unsigned int *> match_info_buf
    term_count = match_info[0]
    col_count = match_info[1]
    total_docs = match_info[2]
    initial_position = 3 + col_count + col_count

    for col in range(col_count):
        col_weight = <double> raw_weights[col]
        if col_weight == 0.0:
            continue
        for term in range(term_count):
            initial_row_col = initial_position + 3 * (col + term * col_count)
            term_frequency = match_info[initial_row_col]
            # hits_in_all_docs = match_info[initial_row_col+1]
            docs_with_hits = match_info[initial_row_col + 2]
            #'pseudo' cosine similarity, because we only have a few available components
            idf = log(total_docs / (1 + docs_with_hits))
            tfidf_doc = term_frequency * idf
            tfidf_query = idf  #because term_frequency=1 since repeated terms are not grouped
            component_sum += tfidf_doc * tfidf_query * col_weight
            pseudo_norm_doc += tfidf_doc * tfidf_doc * col_weight
            norm_query += tfidf_query * tfidf_query * col_weight

    if pseudo_norm_doc ==0.0:
        pseudo_norm_doc = norm_query

    if component_sum == 0.0:  #weights ignored all the columns
        score = 0.0
    else:
        score = component_sum / (sqrt(norm_query) * sqrt(pseudo_norm_doc))

    return -1 * score

def register_rank_functions(database):
    database.register_function(rank_similarity, 'rank_similarity')
