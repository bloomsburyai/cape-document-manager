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


