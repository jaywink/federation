def decode_if_bytes(text):
    try:
        return text.decode("utf-8")
    except AttributeError:
        return text


def encode_if_text(text):
    try:
        return bytes(text, encoding="utf-8")
    except TypeError:
        return text
