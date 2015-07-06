from dateutil.tz import tzlocal, tzutc
from lxml import etree


def ensure_timezone(dt, tz=None):
    """
    Make sure the datetime <dt> has a timezone set, using timezone <tz> if it
    doesn't. <tz> defaults to the local timezone.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz or tzlocal())
    else:
        return dt


class EntityConverter(object):

    def __init__(self, entity):
        self.entity = entity
        self.entity_type = entity.__class__.__name__.lower()

    def struct_to_xml(self, node, struct):
        """
        Turn a list of dicts into XML nodes with tag names taken from the dict
        keys and element text taken from dict values. This is a list of dicts
        so that the XML nodes can be ordered in the XML output.
        """
        for obj in struct:
            for k, v in obj.items():
                etree.SubElement(node, k).text = v

    def convert_to_xml(self):
        if hasattr(self, "%s_to_xml" % self.entity_type):
            method_name = "%s_to_xml" % self.entity_type
            return getattr(self, method_name)()

    def format_dt(cls, dt):
        """
        Format a datetime in the way that D* nodes expect.
        """
        return ensure_timezone(dt).astimezone(tzutc()).strftime(
            '%Y-%m-%d %H:%M:%S %Z'
        )

    def post_to_xml(self):
        req = etree.Element("status_message")
        self.struct_to_xml(req, [
            {'raw_message': self.entity.raw_content},
            {'guid': self.entity.guid},
            {'diaspora_handle': self.entity.handle},
            {'public': 'true' if self.entity.public else 'false'},
            {'created_at': self.format_dt(self.entity.created_at)}
        ])
        return req
