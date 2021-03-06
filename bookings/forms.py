import datetime as dt
import logging

from bootstrap3_datetime.widgets import DateTimePicker
from dateutil.relativedelta import relativedelta
from django import forms
from django.forms import DateTimeField
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from bookings.fields import ResourcesField
from bookings.models import BookingOccurrence, Booking, Resource, Slot, ResourceLock, ResourceCategory

log = logging.getLogger(__name__)


class BookingOccurrenceForm(forms.ModelForm):
    class Meta:
        model = BookingOccurrence
        fields = ['start', 'end', 'recurrence_type', 'recurrence_end']

    picker_options = {
        "format": "DD/MM/YYYY HH:mm",
        "sideBySide": True,
        "calendarWeeks": True,
        "widgetPositioning": {
            "vertical": "top"
        },
        "locale": "fr",
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
        self.form_booking_id = kwargs.pop('booking_pk', None)
        booking = get_object_or_404(Booking, pk=self.form_booking_id)

        resource = (kwargs.get('initial', None)
                    and kwargs.get('initial').get('resources')
                    and kwargs.get('initial').get('resources')[0]) \
                   or (kwargs.get('instance', None)
                       and kwargs.get('instance').resources.first())

        super(BookingOccurrenceForm, self).__init__(*args, **kwargs)

        resources = Resource.objects.filter(available=True)
        if resource:
            resources = resources.filter(category=resource.category)

        if booking.contact_asso:
            resources = resources.exclude(category__type=ResourceCategory.STUDENT)
        else:
            resources = resources.exclude(category__type=ResourceCategory.ASSO)

        self.fields['resources'] = ResourcesField(
            label=BookingOccurrence._meta.get_field('resources').verbose_name.capitalize(),
            choices=resources,
            occurrence=self.instance
        )

        self.Meta.fields.append('resources')

    def clean_resources(self):
        resources = self.cleaned_data['resources']
        first_cat = next(iter(resources.keys())).category
        errors = []

        for resource, quantity in resources.items():
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
            if quantity < 0:
                errors.append(forms.ValidationError(
                    _('La quantité doit être un nombre positif'),
                    code='negative-quantity'
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
            first_resource = next(iter(resources.keys()))

            if self.cleaned_data.get('start'):
                if self.cleaned_data.get('start').time() < first_resource.category.day_start:
                    self.add_error('start', forms.ValidationError(
                        _('La réservation ne peut pas commencer avant %(time)s pour la catégorie %(cat)s'),
                        code='too_early',
                        params={
                            'time': first_resource.category.day_start,
                            'cat': first_resource.category
                        }
                    ))
            if self.cleaned_data.get('start'):
                slot = first_resource.category.get_slot(self.cleaned_data['start'])
                self.cleaned_data['start'] = slot.start

            if self.cleaned_data.get('end'):
                end = first_resource.category.day_end
                if end == dt.time(0, 0):
                    end = dt.time(23, 59, 59)

                form_end = self.cleaned_data.get('end').time()
                if form_end == dt.time(0, 0):
                    form_end = dt.time(23, 59, 59)

                if form_end > end:
                    self.add_error('end', forms.ValidationError(
                        _('La réservation ne peut pas se terminer après %(time)s pour la catégorie %(cat)s'),
                        code='too_late',
                        params={
                            'time': first_resource.category.day_end,
                            'cat': first_resource.category
                        }
                    ))
            if self.cleaned_data.get('end'):
                slot = first_resource.category.get_slot(self.cleaned_data['end'])
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

                recurrence_type = self.cleaned_data.get('recurrence_type')

                # Recurrence type as None should only exist when updating occurrence.
                if recurrence_type is None or recurrence_type == BookingOccurrenceForm.NONE:
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
                            if number_available < requested:
                                resources_errors.append(resource)
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

        if self.cleaned_data.get('recurrence_type') \
                and self.cleaned_data.get('recurrence_type') != BookingOccurrenceForm.NONE \
                and not self.cleaned_data.get('recurrence_end'):
            self.add_error(
                'recurrence_end',
                forms.ValidationError(
                    _('Vous devez saisir une date de fin si vous souhaitez ajouter une périodicité.'),
                    code='need-recurrence_end'
                )
            )

        return self.cleaned_data


class BookingOccurrenceUpdateForm(BookingOccurrenceForm):
    class Meta(BookingOccurrenceForm.Meta):
        fields = ['start', 'end', 'resources']

    recurrence_end = None
    recurrence_type = None

    def clean(self):
        return super(BookingOccurrenceUpdateForm, self).clean()


class BookingFormForm(forms.Form):
    class Meta:
        fields = []

    def __init__(self, booking, *args, **kwargs):
        self.booking = booking
        super(BookingFormForm, self).__init__(*args, **kwargs)

        resource_requires_form = Resource.objects.filter(category__booking_form=True)

        queryset = (BookingOccurrence
                    .objects
                    .filter(booking=booking)
                    .filter(resources__in=resource_requires_form)
                    .distinct()
                    .order_by('start'))

        self.fields['occurrence'] = forms.ModelChoiceField(
            queryset=queryset,
            required=True,
            label='',
        )
        self.Meta.fields.append('occurrence')


class ResourceLockForm(forms.ModelForm):
    class Meta:
        model = ResourceLock
        fields = ['start', 'end', 'reason', 'resources']

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

        if len(errors) > 0:
            raise forms.ValidationError(errors)

        return resources

    def clean(self):
        current = None
        if self.instance.id is not None:
            current = self.instance

        super(ResourceLockForm, self).clean()

        resources = self.cleaned_data.get('resources')

        if resources:
            first_resource = resources.first()

            if self.cleaned_data.get('start'):
                if self.cleaned_data.get('start').time() < first_resource.category.day_start:
                    self.add_error('start', forms.ValidationError(
                        _('Le verrou ne peut pas commencer avant %(time)s pour la catégorie %(cat)s'),
                        code='too_early',
                        params={
                            'time': first_resource.category.day_start,
                            'cat': first_resource.category
                        }
                    ))
            if self.cleaned_data.get('start'):
                slot = first_resource.category.get_slot(self.cleaned_data['start'])
                self.cleaned_data['start'] = slot.start

            if self.cleaned_data.get('end'):
                end = first_resource.category.day_end
                if end == dt.time(0, 0):
                    end = dt.time(23, 59, 59)

                form_end = self.cleaned_data.get('end').time()
                if form_end == dt.time(0, 0):
                    form_end = dt.time(23, 59, 59)

                if form_end > end:
                    self.add_error('end', forms.ValidationError(
                        _('Le verrou ne peut pas se terminer après %(time)s pour la catégorie %(cat)s'),
                        code='too_late',
                        params={
                            'time': first_resource.category.day_end,
                            'cat': first_resource.category
                        }
                    ))
            if self.cleaned_data.get('end'):
                slot = first_resource.category.get_slot(self.cleaned_data['end'])
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
                resources_errors = []

                errors = []

                for resource in resources.all():
                    for occurrence in resource.get_occurrences_period(start, end):
                        if occurrence.id != self.instance.id and occurrence not in occurrences:
                            occurrences.append(occurrence)

                    for lock in resource.get_locks_period(start, end):
                        if lock not in locks and lock != current:
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

        return self.cleaned_data
