from bootstrap3_datetime.widgets import DateTimePicker
from django import forms

from bookings.models import BookingOccurrence


class BookingOccurrenceForm(forms.ModelForm):
    class Meta:
        model = BookingOccurrence
        fields = ['start', 'end']
        widgets = {
            'start': DateTimePicker(
                options={
                    "format": "DD/MM/YYYY HH:mm"
                }
            ),
            'end': DateTimePicker(
                options={
                    "format": "DD/MM/YYYY HH:mm"
                }
            ),
        }

