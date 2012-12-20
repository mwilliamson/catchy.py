import os
import tempfile
import shutil
import errno

import requests

from catchy.tarballs import extract_gzipped_tarball, create_gzipped_tarball_from_dir
import catchy.filelock
from catchy.httpcacher import HttpCacher


class DirectoryCacher(object):
    def __init__(self, cacher_dir):
        self._cacher_dir = cacher_dir
    
    def fetch(self, cache_id, build_dir):
        if self._in_cache(cache_id):
            shutil.copytree(self._cache_dir(cache_id), build_dir)
            return CacheHit()
        else:
            return CacheMiss()
            
    def put(self, cache_id, build_dir):
        if not self._in_cache(cache_id):
            try:
                with self._cache_lock(cache_id):
                    shutil.copytree(build_dir, self._cache_dir(cache_id))
                    open(self._cache_indicator(cache_id), "w").write("")
            except catchy.filelock.FileLockException:
                # Somebody else is writing to the cache, so do nothing
                pass
    
    def _in_cache(self, cache_id):
        return os.path.exists(self._cache_indicator(cache_id))
    
    def _cache_dir(self, cache_id):
        return os.path.join(self._cacher_dir, cache_id)
        
    def _cache_indicator(self, cache_id):
        return os.path.join(self._cacher_dir, "{0}.built".format(cache_id))

    def _cache_lock(self, cache_id):
        _mkdir_p(self._cacher_dir)
        lock_path = os.path.join(self._cacher_dir, "{0}.lock".format(cache_id))
        # raise immediately if the lock already exists
        return catchy.filelock.FileLock(lock_path, timeout=0)
        
    def _release_cache_lock(self, cache_id):
        self._lock(cache_id).release()
        
    def _lock(self, cache_id):
        return FileLock(lock_path)

# TODO: eurgh, what a horrible name
class NoCachingStrategy(object):
    def fetch(self, cache_id, build_dir):
        return CacheMiss()
    
    def put(self, cache_id, build_dir):
        pass

    
    
def _mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as error:
        if error.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
