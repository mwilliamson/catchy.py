import os
import contextlib

from nose.tools import istest, assert_equals, assert_false

from catchy import DirectoryCacher
from catchy.tempdir import create_temporary_dir
from catchy.directorycacher import xdg_cache_dir


test = istest
_cache_id = "c05c2cbd1aa1e3865adba215210a7a82b52ccf90"


@test
def fetch_returns_cache_miss_if_cache_directory_is_empty():
    with _create_directory_cacher() as cacher, _create_target_dir() as target:
        result = cacher.fetch(_cache_id, target)
        assert_equals(False, result.cache_hit)


@test
def fetch_does_not_create_target_dir_if_cache_directory_is_empty():
    with _create_directory_cacher() as cacher, _create_target_dir() as target:
        result = cacher.fetch(_cache_id, target)
        assert_false(os.path.exists(target))


@test
def put_makes_cache_entry_available_for_fetch():
    with _create_directory_cacher() as cacher, _create_target_dir() as target:
        with create_temporary_dir() as temp_dir:
            open(os.path.join(temp_dir, "README"), "w").write("Out of memory and time")
            cacher.put(_cache_id, temp_dir)
            
        cacher.fetch(_cache_id, target)
        fetched_file_path = os.path.join(target, "README")
        fetched_file_contents = open(fetched_file_path).read()
        assert_equals("Out of memory and time", fetched_file_contents)


@test
def xdg_cache_dir_uses_dot_cache_if_env_var_not_set():
    original_value = os.environ.pop("XDG_CACHE_HOME", None)
    try:
        cache_dir = xdg_cache_dir("blah")
        assert_equals(os.path.expanduser("~/.cache/blah"), cache_dir)
    finally:
        if original_value is not None:
            os.environ["XDG_CACHE_HOME"] = original_value

@test
def xdg_cache_dir_uses_xdg_cache_home_env_var_if_set():
    original_value = os.environ.pop("XDG_CACHE_HOME", None)
    try:
        os.environ["XDG_CACHE_HOME"] = "/tmp/some/cache"
        cache_dir = xdg_cache_dir("blah")
        assert_equals(os.path.expanduser("/tmp/some/cache/blah"), cache_dir)
    finally:
        if original_value is None:
            del os.environ["XDG_CACHE_HOME"]
        else:
            os.environ["XDG_CACHE_HOME"] = original_value

@contextlib.contextmanager
def _create_directory_cacher():
    with create_temporary_dir() as temp_dir:
        yield DirectoryCacher(temp_dir)


@contextlib.contextmanager
def _create_target_dir():
    with create_temporary_dir() as temp_dir:
        yield os.path.join(temp_dir, "target")
