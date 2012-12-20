import os
import tempfile
import shutil
import errno

import requests

from catchy.tarballs import extract_gzipped_tarball, create_gzipped_tarball_from_dir
import catchy.filelock


class HttpCacher(object):
    def __init__(self, base_url, key):
        self._base_url = base_url
        self._key = key
        
    def fetch(self, cache_id, build_dir):
        url = self._url_for_cache_id(cache_id)
        with tempfile.NamedTemporaryFile() as local_tarball:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                local_tarball.write(response.content)
                local_tarball.flush()
                os.mkdir(build_dir)
                extract_gzipped_tarball(local_tarball.name, build_dir, strip_components=1)
                
                return CacheHit()
            
        return CacheMiss()
    
    def put(self, cache_id, build_dir):
        url = "{0}?key={1}".format(self._url_for_cache_id(cache_id), self._key)
        with tempfile.NamedTemporaryFile() as local_tarball:
            create_gzipped_tarball_from_dir(build_dir, local_tarball.name)
            requests.put(url, local_tarball.read())
        
    def _url_for_cache_id(self, cache_id):
        return "{0}/{1}.tar.gz".format(self._base_url.rstrip("/"), cache_id)


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


class CacheHit(object):
    cache_hit = True

    
class CacheMiss(object):
    cache_hit = False
    
    
def _mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as error:
        if error.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
