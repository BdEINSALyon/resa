from django import forms

from bookings.models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['reason', 'details', 'resources', 'category', 'owner']

    reason = forms.CharField(disabled=True)
    details = forms.CharField(disabled=True, widget=forms.Textarea)
    resources = forms.MultipleChoiceField(disabled=True)
    category = forms.ChoiceField(widget=forms.Select(attrs={'disabled': 'disabled'}))
