from django import forms

from bookings.models import Booking, Resource, BookingCategory


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['reason', 'details', 'resources', 'category', 'owner']

    reason = forms.CharField(
        disabled=True,
        label=Booking._meta.get_field('reason').verbose_name.capitalize()
    )

    owner = forms.CharField(
        disabled=True,
        label=Booking._meta.get_field('owner').verbose_name.capitalize()
    )

    details = forms.CharField(
        disabled=True,
        widget=forms.Textarea,
        label=Booking._meta.get_field('details').verbose_name.capitalize()
    )

    resources = forms.ModelMultipleChoiceField(
        disabled=True,
        queryset=Resource.objects.all(),
        label=Booking._meta.get_field('resources').verbose_name.capitalize()
    )

    category = forms.ModelChoiceField(
        disabled=True,
        queryset=BookingCategory.objects.all(),
        label=Booking._meta.get_field('category').verbose_name.capitalize()
    )
