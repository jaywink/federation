from datetime import datetime

from dirty_validators.basic import Email


class BaseField(object):
    def __init__(self, required=False, default=None):
        self.required = required
        self.value = default

    def __setattr__(self, key, value):
        if key == "value":
            if not value and self.required:
                raise ValueError("Required value")
        return super(BaseField, self).__setattr__(key, value)


class TextField(BaseField):
    """A base field with value."""
    def __init__(self, min_length=None, *args, **kwargs):
        super(TextField, self).__init__(*args, **kwargs)
        self.min_length = min_length

    def __setattr__(self, key, value):
        if key == "value":
            if self.min_length and (not value or len(value) < self.min_length):
                raise ValueError("Minimum lenght is %s" % self.min_length)
        return super(TextField, self).__setattr__(key, value)


class GUIDField(TextField):
    """A GUID field."""
    min_length = 16


class HandleField(TextField):
    """A field with a handle, ie username@domain.tld."""
    validator = Email()

    def __setattr__(self, key, value):
        if key == "value" and not self.validator.is_valid(value):
            raise ValueError("Handle is not valid")
        return super(HandleField, self).__setattr__(key, value)


class BooleanField(BaseField):
    """A boolean field."""
    value = False

    def __setattr__(self, key, value):
        if key == "value":
            if not isinstance(value, bool):
                raise ValueError("Value must be True or False")
        return super(BooleanField, self).__setattr__(key, value)


class IntegerField(BaseField):
    """An integer field."""
    def __setattr__(self, key, value):
        if key == "value":
            if not isinstance(value, int) and value is not None:
                raise ValueError("Value must be an int")
        return super(IntegerField, self).__setattr__(key, value)


class DateTimeField(BaseField):
    """A field with datetime."""
    def __setattr__(self, key, value):
        if key == "value" and value is not None:
            if not isinstance(value, datetime):
                raise ValueError("Value must be a datetime object")
        return super(DateTimeField, self).__setattr__(key, value)


class ListField(BaseField):
    """A field where value is a list of something."""
    def __init__(self, type_of=None, *args, **kwargs):
        self.type_of = type_of
        super(ListField, self).__init__(*args, **kwargs)

    def __setattr__(self, key, value):
        if key == "value" and value is not None:
            if not isinstance(value, list):
                raise ValueError("Value must be a list object")
        return super(ListField, self).__setattr__(key, value)

    def append(self, obj):
        if self.type_of and not isinstance(obj, self.type_of):
            raise ValueError("Value must be a %s object" % self.type_of.__name__)
        return self.value.append(obj)
