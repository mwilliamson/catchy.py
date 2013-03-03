import os
import shutil
import errno
import subprocess

import locket

from catchy.status import CacheHit, CacheMiss


class DirectoryCacher(object):
    def __init__(self, cacher_dir):
        self._cacher_dir = cacher_dir
    
    def fetch(self, cache_id, target):
        return self._cache_entry(cache_id).fetch(target)
            
    def put(self, cache_id, source):
        return self._cache_entry(cache_id).put(source)
    
    def _cache_entry(self, cache_id):
        return CacheEntry(os.path.join(self._cacher_dir, cache_id))


class CacheEntry(object):
    def __init__(self, path):
        self._path = path
        
    def fetch(self, target):
        if self._has_value():
            _copy(self._path, target)
            return CacheHit()
        else:
            return CacheMiss()
    
    def put(self, source):
        if not self._has_value():
            try:
                with self._lock():
                    try:
                        # Remove anything in the cache in case of prior failures
                        _delete_dir(self._path)
                        _copy(source, self._path)
                        open(self._cache_indicator(), "w").write("")
                    except:
                        _delete_dir(self._path)
                        raise
            except locket.LockError:
                # Somebody else is writing to the cache, so do nothing
                pass
    
    def _has_value(self):
        return os.path.exists(self._cache_indicator())
        
    def _cache_indicator(self):
        return "{0}.cached".format(self._path)
    
    def _lock(self):
        _mkdir_p(os.path.dirname(self._path))
        lock_path = "{0}.lock".format(self._path)
        # raise immediately if the lock already exists
        return locket.lock_file(lock_path, timeout=0)
        


def xdg_directory_cacher(name):
    return DirectoryCacher(xdg_cache_dir(name))
    

def xdg_cache_dir(name):
    xdg_cache_home = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    return os.path.join(xdg_cache_home, name)

    
def _mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as error:
        if error.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def _copy(source, destination):
    if os.path.isdir(source):
        _copy_dir(source, destination)
    else:
        _copy_file(source, destination)

def _copy_dir(source, destination):
    # TODO: should be pure Python, but there isn't a stdlib function
    # that allows the destination to already exist
    subprocess.check_call(["cp", "-rT", source, destination])
    
def _copy_file(source, destination):
    shutil.copyfile(source, destination)


def _delete_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
