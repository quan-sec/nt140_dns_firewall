import time

cache = {}  # domain:type -> (response, expire_time)

def get(domain_type):
    if domain_type in cache:
        response, expire = cache[domain_type]
        if time.time() < expire:
            return response
        else:
            del cache[domain_type]
    return None

def put(domain_type, response, ttl):
    expire_time = time.time() + ttl
    cache[domain_type] = (response, expire_time)
