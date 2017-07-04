def decode_if_bytes(text):
    try:
        return text.decode("utf-8")
    except AttributeError:
        return text
