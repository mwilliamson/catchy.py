import os
import functools

import staticserver
from nose.tools import istest, assert_equals, assert_false

import catchy
from catchy.tempdir import create_temporary_dir
from catchy.tarballs import create_gzipped_tarball_from_dir

_cache_id = "c05c2cbd1aa1e3865adba215210a7a82b52ccf90"

def test(func):
    @functools.wraps(func)
    def run_test():
        with create_temporary_dir() as temp_dir:
            cacher_dir = os.path.join(temp_dir, "www-root")
            os.mkdir(cacher_dir)
            with _start_http_server(cacher_dir) as server:
                build_dir = os.path.join(temp_dir, "build")
                base_url = "http://localhost:{0}/".format(port)
                test_runner = TestRunner(build_dir, base_url, cacher_dir)
                func(test_runner)
    
    return istest(run_test)

@test
def fetch_returns_cache_miss_if_http_server_returns_404(test_runner):
    result = test_runner.cacher.fetch(_cache_id, test_runner.build_dir)
    assert_equals(False, result.cache_hit)

@test
def fetch_does_not_create_build_dir_if_http_server_returns_404(test_runner):
    test_runner.cacher.fetch(_cache_id, test_runner.build_dir)
    assert_false(os.path.exists(test_runner.build_dir))     

@test
def fetch_returns_cache_hit_if_http_server_returns_200(test_runner):
    test_runner.cache_put(_cache_id, {"README": "Out of memory and time"})
    result = test_runner.cacher.fetch(_cache_id, test_runner.build_dir)
    assert_equals(True, result.cache_hit)
    
@test
def fetch_downloads_and_extracts_tarball_from_http_server(test_runner):
    test_runner.cache_put(_cache_id, {"README": "Out of memory and time"})
    test_runner.cacher.fetch(_cache_id, test_runner.build_dir)
    fetched_file_path = os.path.join(test_runner.build_dir, "README")
    fetched_file_contents = open(fetched_file_path).read()
    assert_equals("Out of memory and time", fetched_file_contents)
    
@test
def put_uploads_gzipped_tarball_to_http_server(test_runner):
    with create_temporary_dir() as temp_dir:
        open(os.path.join(temp_dir, "README"), "w").write("Out of memory and time")
        test_runner.cacher.put(_cache_id, temp_dir)
        
    test_runner.cacher.fetch(_cache_id, test_runner.build_dir)
    fetched_file_path = os.path.join(test_runner.build_dir, "README")
    fetched_file_contents = open(fetched_file_path).read()
    assert_equals("Out of memory and time", fetched_file_contents)


@test
def contents_are_merged_if_target_directory_already_exists(test_runner):
    os.mkdir(test_runner.build_dir)
    open(os.path.join(test_runner.build_dir, "hello"), "w").write("Hello there!")
    
    with create_temporary_dir() as temp_dir:
        open(os.path.join(temp_dir, "README"), "w").write("Out of memory and time")
        test_runner.cacher.put(_cache_id, temp_dir)
        
    test_runner.cacher.fetch(_cache_id, test_runner.build_dir)
    assert_equals(
        "Out of memory and time",
        _read_file(os.path.join(test_runner.build_dir, "README"))
    )
    assert_equals(
        "Hello there!",
        _read_file(os.path.join(test_runner.build_dir, "hello"))
    )


@test
def symlinks_are_not_converted_to_ordinary_files_when_passing_through_cache(test_runner):
    with create_temporary_dir() as temp_dir:
        open(os.path.join(temp_dir, "README"), "w").write("Out of memory and time")
        os.symlink("README", os.path.join(temp_dir, "README-sym"))
        test_runner.cacher.put(_cache_id, temp_dir)
    
    target = test_runner.build_dir
    test_runner.cacher.fetch(_cache_id, test_runner.build_dir)
    with open(os.path.join(target, "README"), "w") as actual_file:
        actual_file.write("Wahoo!")
    fetched_file_path = os.path.join(target, "README-sym")
    fetched_file_contents = open(fetched_file_path).read()
    assert_equals("Wahoo!", fetched_file_contents)


def _start_http_server(base_dir):
    return staticserver.start(port=port, root=base_dir, key=staticserver_key)

staticserver_key = "4f015d188778f73315b3f628cee26ed6080c2e5f"
port = 50080

class TestRunner(object):
    def __init__(self, build_dir, base_url, cacher_dir):
        self.build_dir = build_dir
        self.cacher = catchy.HttpCacher(base_url, staticserver_key)
        self._cacher_dir = cacher_dir
        
    def cache_put(self, cache_id, files):
        with create_temporary_dir() as temp_dir:
            tarball_dir = os.path.join(temp_dir, cache_id)
            tarball_name = "{0}.tar.gz".format(cache_id)
            tarball_path = os.path.join(self._cacher_dir, tarball_name)
            
            _write_files(tarball_dir, files)
            
            create_gzipped_tarball_from_dir(tarball_dir, tarball_path)

def _write_files(root, files):
    for filename, contents in files.iteritems():
        path = os.path.join(root, filename)
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        open(path, "w").write(contents)


def _read_file(path):
    with open(path) as f:
        return f.read()
