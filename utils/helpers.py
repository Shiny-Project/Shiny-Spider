import pydash


def get(data, key):
    return pydash.objects.get(data, key)

def get_text(data, key):
    result = get(data, key)
    if result is not None:
        return result.get_text()
    return ''