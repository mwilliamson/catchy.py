import os
import tempfile

import requests

from catchy.status import CacheHit, CacheMiss
from catchy.tarballs import extract_gzipped_tarball, create_gzipped_tarball_from_dir


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
