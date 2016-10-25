import logging

from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.utils.translation import ugettext_lazy as _

from bookings.models import BookingOccurrence, Booking, Resource

log = logging.getLogger(__name__)


class BookingOccurrenceForm(forms.ModelForm):
    class Meta:
        picker_options = {
            "format": "DD/MM/YYYY HH:mm",
            "sideBySide": True,
            "calendarWeeks": True,
            "widgetPositioning": {
                "vertical": "top"
            },
        }
        model = BookingOccurrence
        fields = ['start', 'end', 'resources']
        widgets = {
            'start': DateTimePicker(
                options=picker_options
            ),
            'end': DateTimePicker(
                options=picker_options
            ),
        }

    def __init__(self, *args, **kwargs):
        self.form_booking_id = kwargs.pop("booking_pk", None)
        super(BookingOccurrenceForm, self).__init__(*args, **kwargs)
        self.fields['resources'].queryset = Resource.objects.order_by('category', 'name')

    def clean_resources(self):
        resources = self.cleaned_data['resources']
        first_cat = resources.first().category

        for resource in resources.all():
            if resource.category != first_cat:
                raise forms.ValidationError(_('Toutes les ressources doivent être de la même catégorie'))

        return resources

    def clean(self):
        if self.form_booking_id is not None:
            booking = Booking.objects.get(pk=self.form_booking_id)
            self.cleaned_data['booking'] = booking
            self.instance.booking = booking
        if self.cleaned_data.get('resources'):
            occurrences = []
            for resource in self.cleaned_data['resources'].all():
                for occurrence in resource.get_occurrences_period(self.cleaned_data['start'], self.cleaned_data['end']):
                    if occurrence.id != self.instance.id and occurrence not in occurrences:
                        occurrences.append(occurrence)

            occurrences.sort()

            for occurrence in occurrences:
                self.add_error(None, 'Conflit : ' + str(occurrence))

        return super(BookingOccurrenceForm, self).clean()
