import os

THIS_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__)))
SPLITTER_WORDS_PER_CHUNK = int(os.getenv('CAPE_SPLITTER_WORDS_PER_CHUNK', int(5e2)))
SPLITTER_WORDS_OVERLAP_BEFORE = int(os.getenv('CAPE_SPLITTER_WORDS_OVERLAP_BEFORE', int(5e1)))
SPLITTER_WORDS_OVERLAP_AFTER = int(os.getenv('CAPE_SPLITTER_WORDS_OVERLAP_AFTER', int(5e1)))
LOCAL_UNPICKLING_LRU_CACHE_MAX_SIZE = int(os.getenv('CAPE_LOCAL_UNPICKLING_LRU_CACHE_MAX_SIZE', int(5e4)))

DB_CONFIG = {
    # 'DATABASE': ':memory:',
    'DATABASE': os.getenv('CAPE_SQLITE_PATH', os.path.join(THIS_FOLDER, 'storage', 'bla.sqlite')),
    'PRAGMAS': {
        'journal_mode': os.getenv('CAPE_SQLITE_JOURNAL_MODE', 'wal'),
        'cache_size': int(os.getenv('CAPE_SQLITE_CACHE_SIZE', -1024 * 64))  # -kibibytes
    }
}
