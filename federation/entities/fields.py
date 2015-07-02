from datetime import datetime

from dirty_validators.basic import Email


class BaseField(object):
    value = None

    def __init__(self, required=False):
        self.required = required

    def __setattr__(self, key, value):
        if key == "value":
            if not value and self.required:
                raise ValueError("Required value")
        return super(BaseField, self).__setattr__(key, value)


class TextField(BaseField):
    """A base field with value."""
    value = ""
    
    def __init__(self, required=False, min_length=None):
        super(TextField, self).__init__(required)
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


class DateTimeField(BaseField):
    """A field with datetime."""
    def __setattr__(self, key, value):
        if key == "value" and value is not None:
            if not isinstance(value, datetime):
                raise ValueError("Value must be a datetime object")
        return super(DateTimeField, self).__setattr__(key, value)
