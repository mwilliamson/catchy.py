from catchy.httpcacher import HttpCacher
from catchy.directorycacher import DirectoryCacher, xdg_directory_cacher
from catchy.status import CacheMiss


__all__ = [
    "HttpCacher",
    "DirectoryCacher",
    "xdg_directory_cacher",
    "NoCachingStrategy"
]


# TODO: eurgh, what a horrible name
class NoCachingStrategy(object):
    def fetch(self, cache_id, build_dir):
        return CacheMiss()
    
    def put(self, cache_id, build_dir):
        pass

