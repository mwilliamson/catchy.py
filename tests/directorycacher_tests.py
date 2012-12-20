import contextlib

from nose.tools import istest, assert_equals

from catchy import DirectoryCacher
from catchy.tempdir import create_temporary_dir


test = istest
_cache_id = "c05c2cbd1aa1e3865adba215210a7a82b52ccf90"


@test
def fetch_returns_cache_miss_if_cache_directory_is_empty():
    with _create_directory_cacher() as cacher, create_temporary_dir() as temp_dir:
        result = cacher.fetch(_cache_id, temp_dir)
        assert_equals(False, result.cache_hit)


@contextlib.contextmanager
def _create_directory_cacher():
    with create_temporary_dir() as temp_dir:
        yield DirectoryCacher(temp_dir)
