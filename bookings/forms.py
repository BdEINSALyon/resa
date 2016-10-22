from django import forms

from bookings.models import Booking, Resource, BookingCategory, BookingOccurrence


class BookingOccurrenceForm(forms.ModelForm):
    class Meta:
        model = BookingOccurrence
        fields = ['start', 'end']

    start = forms.SplitDateTimeField(
        label=BookingOccurrence._meta.get_field('start').verbose_name.capitalize()
    )

    end = forms.SplitDateTimeField(
        label=BookingOccurrence._meta.get_field('end').verbose_name.capitalize()
    )

