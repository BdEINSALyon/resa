from bootstrap3_datetime.widgets import DateTimePicker
from django import forms

from bookings.models import BookingOccurrence


class BookingOccurrenceForm(forms.ModelForm):
    class Meta:
        picker_options = {
            "format": "DD/MM/YYYY HH:mm",
            "sideBySide": True,
            "calendarWeeks": True,
            "toolbarPlacement": 'top',
            "showTodayButton": True,
            "showClear": True,
            "showClose": True,
        }
        model = BookingOccurrence
        fields = ['start', 'end']
        widgets = {
            'start': DateTimePicker(
                options=picker_options
            ),
            'end': DateTimePicker(
                options=picker_options
            ),
        }
