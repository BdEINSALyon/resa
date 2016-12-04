import logging

from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.forms import DateTimeField
from django.utils.translation import ugettext_lazy as _

from bookings.fields import ResourcesField
from bookings.models import BookingOccurrence, Booking, Resource

log = logging.getLogger(__name__)


class BookingOccurrenceForm(forms.ModelForm):
    class Meta:
        model = BookingOccurrence
        fields = ['start', 'end', 'recurrence_type', 'recurrence_end', 'resources']

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

    RECURRENCE_CHOICES = (
        ('N', _('Aucun')),
        ('D', _('Quotidien')),
        ('W', _('Hebdomadaire')),
        ('M', _('Mensuel')),
        ('Y', _('Annuel'))
    )

    recurrence_type = forms.ChoiceField(
        choices=RECURRENCE_CHOICES,
        label=_('Type de récurrence')
    )

    recurrence_end = forms.DateField(
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

    resources = ResourcesField(
        label=BookingOccurrence._meta.get_field('resources').verbose_name.capitalize(),
        choices=Resource.objects.all()
    )

    def __init__(self, *args, **kwargs):
        self.form_booking_id = kwargs.pop("booking_pk", None)
        super(BookingOccurrenceForm, self).__init__(*args, **kwargs)

    def clean_resources(self):
        resources = self.cleaned_data['resources']
        first_cat = next(iter(resources.keys())).category
        errors = []

        for resource in resources.keys():
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

        resources = self.cleaned_data.get('resources')

        if resources:
            if self.cleaned_data.get('start'):
                slot = next(iter(resources.keys())).category.get_slot(self.cleaned_data['start'])
                self.cleaned_data['start'] = slot.start

            if self.cleaned_data.get('end'):
                slot = next(iter(resources.keys())).category.get_slot(self.cleaned_data['end'])
                if self.cleaned_data['end'] != slot.start:
                    self.cleaned_data['end'] = slot.end

            if self.cleaned_data.get('end') and self.cleaned_data.get('recurrence_end'):
                end = self.cleaned_data.get('end')
                recurrence_end = self.cleaned_data.get('recurrence_end')

                if recurrence_end < end:
                    raise forms.ValidationError(
                        _("La date de fin de récurrence doit se situer après la date de fin !"),
                        code='start-recurrence_end-order'
                    )

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

                errors = []

                for resource, requested in resources.items():
                    for occurrence in resource.get_occurrences_period(start, end):
                        if occurrence.id != self.instance.id and occurrence not in occurrences:
                            occurrences.append(occurrence)

                    for lock in resource.get_locks_period(start, end):
                        if lock not in locks:
                            locks.append(lock)

                    number_available = resource.count_available(start, end)
                    if number_available < requested:
                        self.add_error(
                            'resources',
                            forms.ValidationError(
                                _('Seulement %(number)d %(name)s disponible !'),
                                code='not-enough',
                                params={
                                    'number': number_available,
                                    'name': resource.name
                                }
                            )
                        )

                occurrences.sort()
                locks.sort()

                for conflict in occurrences + locks:
                    errors.append(forms.ValidationError(
                        _('Conflit : %(conflict)s'),
                        code='conflict',
                        params={'conflict': conflict}
                    ))

                if len(errors) > 0:
                    raise forms.ValidationError(errors)

        if self.cleaned_data.get('recurrence_type') != 'N' and not self.cleaned_data.get('recurrence_end'):
            self.add_error(
                'recurrence_end',
                forms.ValidationError(
                    _('Vous devez saisir une date de fin si vous souhaitez ajouter une récurrence.'),
                    code='need-recurrence_end'
                )
            )

        return self.cleaned_data
