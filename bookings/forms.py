import logging

from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.forms import DateTimeField
from django.utils.translation import ugettext_lazy as _

from bookings.models import BookingOccurrence, Booking, Resource

log = logging.getLogger(__name__)


class BookingOccurrenceForm(forms.ModelForm):
    class Meta:
        model = BookingOccurrence
        fields = ['start', 'end', 'resources', 'recursion_type']
        widgets = {
            'resources': forms.SelectMultiple(
                attrs={'size': 10}
            ),
        }

    picker_options = {
        "format": "DD/MM/YYYY HH:mm",
        "sideBySide": True,
        "calendarWeeks": True,
        "widgetPositioning": {
            "vertical": "top"
        },
    }

    picker_date_options = picker_options.copy()
    picker_date_options['format'] = 'DD/MM/YYYY'

    RECURSION_CHOICES = (
        ('N', _('Aucun')),
        ('D', _('Quotidien')),
        ('W', _('Hebdomadaire')),
        ('M', _('Mensuel')),
        ('Y', _('Annuel'))
    )

    recursion_type = forms.ChoiceField(
        choices=RECURSION_CHOICES,
        label=_('Type de récurrence')
    )

    recursion_end = forms.DateField(
        input_formats=['%d/%m/%Y'],
        widget=DateTimePicker(options=picker_date_options),
        label=_('Date de fin de récurrence'),
        help_text=_('Pris en compte seulement si le type de récurrence est différent de "Aucun"'),
        required=False
    )

    start = DateTimeField(
        input_formats=['%d/%m/%Y %H:%M'],
        widget=DateTimePicker(options=picker_options),
        label=BookingOccurrence._meta.get_field('start').verbose_name.capitalize()
    )

    end = DateTimeField(
        input_formats=['%d/%m/%Y %H:%M'],
        widget=DateTimePicker(options=picker_options),
        label=BookingOccurrence._meta.get_field('end').verbose_name.capitalize()
    )

    def __init__(self, *args, **kwargs):
        self.form_booking_id = kwargs.pop("booking_pk", None)
        super(BookingOccurrenceForm, self).__init__(*args, **kwargs)
        self.fields['resources'].queryset = Resource.objects.all()

    def clean_resources(self):
        resources = self.cleaned_data['resources']
        first_cat = resources.first().category
        errors = []

        for resource in resources.all():
            if resource.category != first_cat:
                errors.append(forms.ValidationError(
                    _('Toutes les ressources doivent être de la même catégorie'),
                    code='not-same-category'
                ))
            if not resource.available:
                errors.append(forms.ValidationError(
                    _("%(res)s n'est pas disponible"),
                    code='not-available',
                    params={'res': str(resource)}
                ))

        if len(errors) > 0:
            raise forms.ValidationError(errors)

        return resources

    def clean(self):
        if self.form_booking_id is not None:
            booking = Booking.objects.get(pk=self.form_booking_id)
            self.cleaned_data['booking'] = booking
            self.instance.booking = booking

        super(BookingOccurrenceForm, self).clean()

        if self.cleaned_data.get('resources'):
            if self.cleaned_data.get('start'):
                slot = self.cleaned_data.get('resources').first().category.get_slot(self.cleaned_data['start'])
                self.cleaned_data['start'] = slot.start

            if self.cleaned_data.get('end'):
                slot = self.cleaned_data.get('resources').first().category.get_slot(self.cleaned_data['end'])
                if self.cleaned_data['end'] != slot.start:
                    self.cleaned_data['end'] = slot.end

            if self.cleaned_data.get('start') and self.cleaned_data.get('end'):
                start = self.cleaned_data.get('start')
                end = self.cleaned_data.get('end')

                if end < start:
                    raise forms.ValidationError(
                        _("Le début doit être avant la fin !"),
                        code='start-end-order'
                    )

                occurrences = []
                locks = []

                for resource in self.cleaned_data['resources'].all():
                    for occurrence in resource.get_occurrences_period(start, end):
                        if occurrence.id != self.instance.id and occurrence not in occurrences:
                            occurrences.append(occurrence)

                    for lock in resource.get_locks_period(start, end):
                        if lock not in locks:
                            locks.append(lock)

                occurrences.sort()
                locks.sort()

                errors = []

                for conflict in occurrences + locks:
                    errors.append(forms.ValidationError(
                        _('Conflit : %(conflict)s'),
                        code='conflict',
                        params={'conflict': conflict}
                    ))

                if len(errors) > 0:
                    raise forms.ValidationError(errors)

        if self.cleaned_data.get('recursion_type') != 'N' and not self.cleaned_data.get('recursion_end'):
            self.add_error(
                'recursion_end',
                forms.ValidationError(
                    _('Vous devez saisir une date de fin si vous souhaitez ajouter une récurrence.')
                )
            )

        return self.cleaned_data
