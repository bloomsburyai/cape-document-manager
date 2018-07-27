from peewee import fn
from cape_document_manager.tables import database

import pyximport

importers = pyximport.install()

from cape_document_manager._rank_similarity import register_rank_functions

pyximport.uninstall(*importers)
register_rank_functions(database)


def rank_similarity(cls):
    return fn.rank_similarity(fn.matchinfo(cls._meta.entity, 'pcnalx'), 1.0,
                              0.0)  # we ignore the null 'identifier' column


