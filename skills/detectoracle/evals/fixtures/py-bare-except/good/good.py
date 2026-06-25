def process(data):
    try:
        result = data["key"]
        return result
    except KeyError:
        return None
