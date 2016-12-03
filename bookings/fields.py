from django.forms import Field
from django.utils.encoding import smart_text

from bookings.widgets import ResourcesWidget


class ResourcesField(Field):
    widget = ResourcesWidget

    def __init__(self, choices, *args, **kwargs):
        super(ResourcesField, self).__init__(required=False, *args, **kwargs)
        self.widget.choices = choices

    def clean(self, value):
        print('ResourcesField clean', value)
        return super(ResourcesField, self).clean(value)

    def to_python(self, value):
        print('ResourcesField to_python', value)
        return smart_text(value)
