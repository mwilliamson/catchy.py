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
        if self._in_cache(cache_id):
            path = self._cache_entry_path(cache_id)
            self._copy(path, target)
            return CacheHit()
        else:
            return CacheMiss()
            
    def put(self, cache_id, source):
        if not self._in_cache(cache_id):
            try:
                with self._cache_lock(cache_id):
                    cache_dir = self._cache_entry_path(cache_id)
                    try:
                        self._copy(source, cache_dir)
                        open(self._cache_indicator(cache_id), "w").write("")
                    except:
                        shutil.rmtree(cache_dir)
                        raise
            except locket.LockError:
                # Somebody else is writing to the cache, so do nothing
                pass
    
    def _in_cache(self, cache_id):
        return os.path.exists(self._cache_indicator(cache_id))
    
    def _cache_entry_path(self, cache_id):
        return os.path.join(self._cacher_dir, cache_id)
        
    def _cache_indicator(self, cache_id):
        return os.path.join(self._cacher_dir, "{0}.built".format(cache_id))

    def _cache_lock(self, cache_id):
        _mkdir_p(self._cacher_dir)
        lock_path = os.path.join(self._cacher_dir, "{0}.lock".format(cache_id))
        # raise immediately if the lock already exists
        return locket.lock_file(lock_path, timeout=0)

    def _copy(self, source, destination):
        if os.path.isdir(source):
            self._copy_dir(source, destination)
        else:
            self._copy_file(source, destination)

    def _copy_dir(self, source, destination):
        # TODO: should be pure Python, but there isn't a stdlib function
        # that allows the destination to already exist
        subprocess.check_call(["cp", "-rT", source, destination])
        
    def _copy_file(self, source, destination):
        shutil.copyfile(source, destination)


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
