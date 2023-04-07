import json
from datetime import timedelta
from pyld import jsonld

try:
    from federation.utils.django import get_redis
    cache = get_redis() or {}
    EXPIRATION = int(timedelta(weeks=4).total_seconds())
except:
    cache = {}


# This is required to workaround a bug in pyld that has the Accept header
# accept other content types. From what I understand, precedence handling
# is broken
# from https://github.com/digitalbazaar/pyld/issues/133
# cacheing loosely inspired by https://github.com/digitalbazaar/pyld/issues/70
def get_loader(*args, **kwargs):
    requests_loader = jsonld.requests_document_loader(*args, **kwargs)

    def loader(url, options={}):
        key = f'ld_cache:{url}'
        try:
            return json.loads(cache[key])
        except KeyError:
            options['headers']['Accept'] = 'application/ld+json'
            doc = requests_loader(url, options)
            if isinstance(cache, dict):
                cache[key] = json.dumps(doc)
            else:
                cache.set(key, json.dumps(doc), ex=EXPIRATION)
            return doc

    return loader


jsonld.set_document_loader(get_loader())
