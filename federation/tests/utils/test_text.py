from federation.utils.text import decode_if_bytes, encode_if_text


def test_decode_if_bytes():
    assert decode_if_bytes(b"foobar") == "foobar"
    assert decode_if_bytes("foobar") == "foobar"


def test_encode_if_text():
    assert encode_if_text(b"foobar") == b"foobar"
    assert encode_if_text("foobar") == b"foobar"
