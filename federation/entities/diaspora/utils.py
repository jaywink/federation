# -*- coding: utf-8 -*-
import inspect

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


def format_dt(dt):
    """
    Format a datetime in the way that D* nodes expect.
    """
    return ensure_timezone(dt).astimezone(tzutc()).strftime(
        '%Y-%m-%d %H:%M:%S %Z'
    )


def struct_to_xml(node, struct):
    """
    Turn a list of dicts into XML nodes with tag names taken from the dict
    keys and element text taken from dict values. This is a list of dicts
    so that the XML nodes can be ordered in the XML output.
    """
    for obj in struct:
        for k, v in obj.items():
            etree.SubElement(node, k).text = v


def get_base_attributes(entity):
    """Build a dict of attributes of an entity.

    Returns attributes and their values, ignoring any properties, functions and anything that starts
    with an underscore.
    """
    attributes = {}
    cls = entity.__class__
    for attr, _ in inspect.getmembers(cls, lambda o: not isinstance(o, property) and not inspect.isroutine(o)):
        if not attr.startswith("_"):
            attributes[attr] = getattr(entity, attr)
    return attributes
