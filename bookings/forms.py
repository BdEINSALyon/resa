import logging

from bootstrap3_datetime.widgets import DateTimePicker
from dateutil.relativedelta import relativedelta
from django import forms
from django.forms import DateTimeField
from django.utils.translation import ugettext_lazy as _

from bookings.fields import ResourcesField
from bookings.models import BookingOccurrence, Booking, Resource, Slot

log = logging.getLogger(__name__)


class BookingOccurrenceForm(forms.ModelForm):
    class Meta:
        model = BookingOccurrence
        fields = ['start', 'end', 'recurrence_type', 'recurrence_end', 'ignore_impossible']

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

    NONE = 'N'
    DAILY = 'D'
    WEEKLY = 'W'
    BI_WEEKLY = '2W'
    TRI_WEEKLY = '3W'
    QUAD_WEEKLY = '4W'
    MONTHLY = 'M'
    YEARLY = 'Y'

    RECURRENCE_CHOICES = (
        (NONE, _('Aucun')),
        (DAILY, _('Tous les jours')),
        (WEEKLY, _('Toutes les semaines (même jour de la semaine)')),
        (BI_WEEKLY, _('Toutes les deux semaines (même jour de la semaine)')),
        (TRI_WEEKLY, _('Toutes les trois semaines (même jour de la semaine)')),
        (QUAD_WEEKLY, _('Toutes les quatre semaines (même jour de la semaine)')),
        (MONTHLY, _('Tous les mois à la même date')),
        (YEARLY, _('Tous les ans à la même date'))
    )

    recurrence_type = forms.ChoiceField(
        choices=RECURRENCE_CHOICES,
        label=_('Type de périodicité')
    )

    recurrence_end = forms.DateField(
        input_formats=['%d/%m/%Y'],
        widget=DateTimePicker(options=picker_date_options),
        label=_('Date de fin de périodicité'),
        help_text=_('Pris en compte seulement si le type de périodicité est différent de "Aucun".'),
        required=False
    )

    ignore_impossible = forms.BooleanField(
        label=_('Ignorer les dates impossibles'),
        help_text=_(
            'Lorsque cette option est sélectionnée, '
            "les demandes impossibles à satisfaire ne génèrent pas d'erreur. "
            'Pris en compte seulement si le type de périodicité est différent de "Aucun".'
        ),
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
        self.fields['resources'] = ResourcesField(
            label=BookingOccurrence._meta.get_field('resources').verbose_name.capitalize(),
            choices=Resource.objects.filter(available=True),
            occurrence=self.instance
        )
        self.Meta.fields.append('resources')

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

                if recurrence_end < end.date():
                    raise forms.ValidationError(
                        _("La date de fin de périodicité doit se situer après la date de fin !"),
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

                if self.cleaned_data.get('recurrence_type') == BookingOccurrenceForm.NONE:
                    occurrences = []
                    locks = []
                    resources_errors = []

                    errors = []

                    for resource, requested in resources.items():
                        if not resource.is_countable():
                            for occurrence in resource.get_occurrences_period(start, end):
                                if occurrence.id != self.instance.id and occurrence not in occurrences:
                                    occurrences.append(occurrence)
                        else:
                            number_available = resource.count_available(start, end, self.instance)
                            resources_errors.append(resource)
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

                        for lock in resource.get_locks_period(start, end):
                            if lock not in locks:
                                locks.append(lock)

                    occurrences.sort()
                    locks.sort()
                    resources_errors.sort()

                    for conflict in occurrences + locks + resources_errors:
                        errors.append(forms.ValidationError(
                            _('Conflit : %(conflict)s'),
                            code='conflict',
                            params={'conflict': conflict}
                        ))

                    if len(errors) > 0:
                        raise forms.ValidationError(errors)

        if self.cleaned_data.get('recurrence_type') != BookingOccurrenceForm.NONE \
                and not self.cleaned_data.get('recurrence_end'):
            self.add_error(
                'recurrence_end',
                forms.ValidationError(
                    _('Vous devez saisir une date de fin si vous souhaitez ajouter une périodicité.'),
                    code='need-recurrence_end'
                )
            )

        if self.cleaned_data.get('recurrence_type') != BookingOccurrenceForm.NONE \
                and self.cleaned_data.get('start') \
                and self.cleaned_data.get('end') \
                and self.cleaned_data.get('recurrence_end')\
                and self.cleaned_data.get('resources')\
                and not self.cleaned_data.get('ignore_impossible'):

            recurrence_type = self.cleaned_data.get('recurrence_type')
            delta = None
            if recurrence_type == BookingOccurrenceForm.DAILY:
                delta = relativedelta(days=1)
            elif recurrence_type == BookingOccurrenceForm.WEEKLY:
                delta = relativedelta(weeks=1)
            elif recurrence_type == BookingOccurrenceForm.BI_WEEKLY:
                delta = relativedelta(weeks=2)
            elif recurrence_type == BookingOccurrenceForm.TRI_WEEKLY:
                delta = relativedelta(weeks=3)
            elif recurrence_type == BookingOccurrenceForm.QUAD_WEEKLY:
                delta = relativedelta(weeks=4)
            elif recurrence_type == BookingOccurrenceForm.MONTHLY:
                delta = relativedelta(months=1)
            elif recurrence_type == BookingOccurrenceForm.YEARLY:
                delta = relativedelta(years=1)

            start_time = self.cleaned_data.get('start')
            end_time = self.cleaned_data.get('end')
            recurr_end = self.cleaned_data.get('recurrence_end')

            errors = []
            while start_time.date() <= end_time.date() <= recurr_end:
                for resource, count in self.cleaned_data.get('resources').items():
                    if resource.count_available(start_time, end_time) < count:
                        errors.append(forms.ValidationError(
                            _('%(res)s indisponible %(slot)s'),
                            code='conflict',
                            params={
                                'res': resource,
                                'slot': Slot(start=start_time, end=end_time)
                            }
                        ))

                start_time += delta
                end_time += delta

            if len(errors) > 0:
                raise forms.ValidationError(errors)

        print("Cleaned data", self.cleaned_data)
        return self.cleaned_data
