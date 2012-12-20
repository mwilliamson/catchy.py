from catchy.httpcacher import HttpCacher
from catchy.directorycacher import DirectoryCacher
from catchy.status import CacheMiss


__all__ = ["HttpCacher", "DirectoryCacher", "NoCachingStrategy"]


# TODO: eurgh, what a horrible name
class NoCachingStrategy(object):
    def fetch(self, cache_id, build_dir):
        return CacheMiss()
    
    def put(self, cache_id, build_dir):
        pass

