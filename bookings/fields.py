from django import forms
from django.core.exceptions import ValidationError

from bookings.models import Resource
from bookings.widgets import ResourcesWidget


class ResourcesField(forms.Field):
    widget = ResourcesWidget

    def __init__(self, choices, *args, **kwargs):
        super(ResourcesField, self).__init__(*args, **kwargs)
        self.widget.choices = self.choices = choices

    def clean(self, value):
        if len(value) == 0:
            raise ValidationError(_('Vous devez sélectionner au moins une ressource.'))
        return super(ResourcesField, self).clean(value)

    def to_python(self, counts):
        print('ResourcesField to_python', counts)
        resource_counts = {}
        for pk, count in counts.items():
            resource = Resource.objects.get(pk=pk)
            resource_counts[resource] = count

        return resource_counts
