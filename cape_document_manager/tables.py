# Copyright 2018 BLEMUNDSBURY AI LIMITED
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from cape_document_manager.document_manager_settings import DB_CONFIG
from scout.models import database, Index, Attachment, BlobData, Document, Metadata, IndexDocument
from scout.search import DocumentSearch

from cape_document_manager.rank_similarity import rank_similarity

_TABLES = [Attachment, BlobData, Document, Metadata, Index, IndexDocument]


def init_db(reset_database=False):
    """Create and/or initialize database"""
    if not database.is_closed():
        database.close()
    database.init(DB_CONFIG['DATABASE'], pragmas=DB_CONFIG['PRAGMAS'])
    database.connect()
    if reset_database:
        database.drop_tables(_TABLES, safe=True)
    database.create_tables(_TABLES)


init_db()


def get_rank_expression(self, ranking):
    if ranking == 'rank_similarity':
        return rank_similarity(Document)
    else:
        return self._get_rank_expression(ranking)


DocumentSearch._get_rank_expression = DocumentSearch.get_rank_expression
DocumentSearch.get_rank_expression = get_rank_expression
