import attr

from federation.utils.network import fetch_content_type


@attr.s
class ImageObject:
    """
    An Image object for AS2 serialization.
    """
    _allowed_types = (
        "image/jpeg",
        "image/png",
        "image/gif",
    )
    url: str = attr.ib()
    type: str = attr.ib(default="Image")
    mediaType: str = attr.ib()

    @mediaType.default
    def cache_media_type(self):
        content_type = fetch_content_type(self.url)
        if content_type in self._allowed_types:
            return content_type
        return ""
