import logging

from bootstrap3_datetime.widgets import DateTimePicker
from django import forms

from bookings.models import BookingOccurrence, Booking

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

    def clean(self):
        if self.form_booking_id is not None:
            booking = Booking.objects.get(pk=self.form_booking_id)
            self.cleaned_data['booking'] = booking
            self.instance.booking = booking

        occurrences = []
        for resource in self.cleaned_data['resources'].all():
            for occurrence in resource.get_occurrences_period(self.cleaned_data['start'], self.cleaned_data['end']):
                if occurrence.id != self.instance.id and occurrence not in occurrences:
                    occurrences.append(occurrence)

        occurrences.sort()

        for occurrence in occurrences:
            self.add_error(None, 'Conflit : ' + str(occurrence))

        return super(BookingOccurrenceForm, self).clean()
