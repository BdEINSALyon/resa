import datetime as dt
import logging

from django.contrib.humanize.templatetags.humanize import naturalday
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

log = logging.getLogger(__name__)


class Slot:
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __str__(self):
        return _('de %(start)s à %(end)s') % {
            'start': self.start,
            'end': self.end
        }

    def __eq__(self, other):
        return self.start == other.start and self.end == other.end

    def __hash__(self, *args, **kwargs):
        return hash((self.start, self.end))

    def get_period(self, periods):
        for period in periods:
            if period.contains_slot(self):
                return period

        return None

    def get_periods(self, periods):
        found_periods = []
        for period in periods:
            if period.contains_slot(self) and period not in found_periods:
                found_periods.append(period)

        return found_periods if len(found_periods) > 0 else None


class ResourceCategory(models.Model):
    class Meta:
        verbose_name = _('catégorie de ressource')
        verbose_name_plural = _('catégories de ressource')
        ordering = ['name']

    name = models.CharField(max_length=150, verbose_name=_('nom'))
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('catégorie parente')
    )
    day_start = models.TimeField(verbose_name=_('début de journée'))
    day_end = models.TimeField(verbose_name=_('fin de journée'))
    granularity = models.PositiveIntegerField(verbose_name=_('granularité'), help_text=_('en minutes'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('bookings:resource-category-day', kwargs={'id': str(self.id)})

    def __str__(self):
        return self.name

    def get_slots(self, date):
        time = dt.datetime.combine(date, self.day_start)
        end = dt.datetime.combine(date, self.day_end)

        # Allow midnight for end of day
        if self.day_end == dt.time(0, 0):
            end += dt.timedelta(days=1)

        delta = dt.timedelta(minutes=self.granularity)

        slots = []

        # Allow 23:59:59 for end of day
        while time + delta <= end + dt.timedelta(seconds=1):
            slots.append(Slot(time, time + delta))
            time += delta

        return slots

    def get_slot(self, datetime):
        time = dt.datetime.combine(datetime.date(), self.day_start)
        end = dt.datetime.combine(datetime.date(), self.day_end)

        # Allow midnight for end of day
        if self.day_end == dt.time(0, 0):
            end += dt.timedelta(days=1)

        delta = dt.timedelta(minutes=self.granularity)

        # Allow 23:59:59 for end of day
        while time + delta <= end + dt.timedelta(seconds=1):
            slot = Slot(time, time + delta)
            if slot.start <= datetime < slot.end:
                return slot
            time += delta


class Place(models.Model):
    class Meta:
        verbose_name = _('lieu')
        verbose_name_plural = _('lieux')

    name = models.CharField(max_length=150, verbose_name=_('nom'))


class Resource(models.Model):
    class Meta:
        verbose_name = _('ressource')
        verbose_name_plural = _('ressources')
        ordering = ['category', 'name']

    name = models.CharField(max_length=150, verbose_name=_('nom'))
    description = models.CharField(max_length=500, blank=True, verbose_name=_('description'))
    category = models.ForeignKey(
        ResourceCategory,
        on_delete=models.CASCADE,
        verbose_name=_('catégorie')
    )
    available = models.BooleanField(verbose_name=_('disponible'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    number = models.PositiveIntegerField(verbose_name=_('quantité'), default=1)

    place = models.ForeignKey(
        to=Place,
        on_delete=models.SET_NULL,
        null=True,
        default=None
    )

    booking_fee = models.PositiveIntegerField(
        verbose_name=_('frais de location'),
        default=0,
        help_text=_('en centimes')
    )
    guarantee = models.PositiveIntegerField(
        verbose_name=_('caution'),
        default=0,
        help_text=_('en centimes')
    )

    def is_countable(self):
        return self.number > 1

    def count_available(self, start_p, end_p, occurrence=None):
        occurrences = self.get_occurrences_period(start_p, end_p)
        booked_count = 0

        for occ in occurrences:
            if occ == occurrence:
                continue
            for booking in occ.bookings.filter(resource__exact=self):
                print(booking)
                booked_count += booking.count

        return self.number - booked_count

    def __str__(self):
        return self.name + ' - ' + self.category.name

    def get_occurrences(self, year=dt.date.today().year, month=dt.date.today().month, day=dt.date.today().day):
        return (BookingOccurrence.objects
                .filter(resources__exact=self)
                .filter(start__year__lte=year)
                .filter(end__year__gte=year)
                .filter(start__month__lte=month)
                .filter(end__month__gte=month)
                .filter(start__day__lte=day)
                .filter(end__day__gte=day))

    def get_locks(self, year=dt.date.today().year, month=dt.date.today().month, day=dt.date.today().day):
        return (ResourceLock.objects
                .filter(resources__exact=self)
                .filter(start__year__lte=year)
                .filter(end__year__gte=year)
                .filter(start__month__lte=month)
                .filter(end__month__gte=month)
                .filter(start__day__lte=day)
                .filter(end__day__gte=day))

    def get_occurrences_period(self, start_p, end_p):
        return BookingOccurrence.objects\
            .filter(resources__exact=self)\
            .filter((Q(start__lte=start_p) & Q(end__gte=end_p))  # Commence avant et finit après la période
                    | (Q(start__lte=start_p) & Q(end__lte=end_p) & Q(end__gt=start_p))  # Commence avant et finit pendant
                    | (Q(start__gte=start_p) & Q(start__lt=end_p) & Q(end__gte=end_p))  # Commence pendant et finit après
                    | (Q(start__gte=start_p) & Q(start__lt=end_p) & Q(end__lte=end_p) & Q(end__gt=start_p)))  # Commence et finit pendant

    def get_locks_period(self, start_p, end_p):
        return ResourceLock.objects\
            .filter(resources__exact=self)\
            .filter((Q(start__lte=start_p) & Q(end__gte=end_p))  # Commence avant et finit après la période
                    | (Q(start__lte=start_p) & Q(end__lte=end_p) & Q(end__gt=start_p))  # Commence avant et finit pendant
                    | (Q(start__gte=start_p) & Q(start__lt=end_p) & Q(end__gte=end_p))  # Commence pendant et finit après
                    | (Q(start__gte=start_p) & Q(start__lt=end_p) & Q(end__lte=end_p) & Q(end__gt=start_p)))  # Commence et finit pendant

    def get_occurrence(self, year=dt.date.today().year, month=dt.date.today().month, day=dt.date.today().day,
                       hour=dt.datetime.now().hour, minute=dt.datetime.now().minute):
        return (self.get_occurrences(year=year, month=month, day=day)
                .filter(start__hour__lte=hour)
                .filter(end__hour__gte=hour)
                .filter(start__minute__lte=minute)
                .filter(end__minute__gte=minute)
                .first())


class BookingCategory(models.Model):
    class Meta:
        verbose_name = _('catégorie de réservation')
        verbose_name_plural = _('catégories de réservation')
        ordering = ['name']

    name = models.CharField(max_length=150, verbose_name=_('nom'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Booking(models.Model):
    class Meta:
        verbose_name = _('réservation')
        verbose_name_plural = _('réservations')
        ordering = ['created_at']

    reason = models.CharField(max_length=150, verbose_name=_('raison'))
    details = models.TextField(verbose_name=_('détails'), blank=True)
    category = models.ForeignKey(
        BookingCategory,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('catégorie de réservation')
    )
    owner = models.CharField(max_length=100, blank=True, verbose_name=_('propriétaire'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return _('%(owner)s - %(reason)s') % {
            'reason': self.reason,
            'owner': self.owner
        }

    def get_absolute_url(self):
        return reverse('bookings:booking-details', kwargs={'pk': str(self.id)})

    def get_occurrences(self):
        return self.bookingoccurrence_set.all()


class StartEndPeriod(models.Model):
    class Meta:
        abstract = True
        ordering = ['start', 'end']

    start = models.DateTimeField(verbose_name=_('date et heure de début'))
    end = models.DateTimeField(verbose_name=_('date et heure de fin'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def str_dates(self):
        if self.start.date() == self.end.date():
            return _('%(date)s de %(start)s à %(end)s') % {
                'date': naturalday(self.start.date(), 'd/m/Y'),
                'start': self.start.time().strftime('%H:%M'),
                'end': self.end.time().strftime('%H:%M')
            }

        else:
            return _('%(start_date)s %(start_time)s - %(end_date)s %(end_time)s') % {
                'start_date': naturalday(self.start, 'd/m/Y'),
                'start_time': self.start.strftime('(%H:%M)'),
                'end_date': naturalday(self.end, 'd/m/Y'),
                'end_time': self.end.strftime('(%H:%M)'),
            }

    def contains_slot(self, slot):
        return slot.start >= self.start and slot.end <= self.end

    def __le__(self, other):
        return self.start <= other.start

    def __lt__(self, other):
        return self.start < other.start


class StartEndResources(StartEndPeriod):
    class Meta:
        abstract = True

    resources = models.ManyToManyField(
        Resource,
        verbose_name=_('ressources')
    )

    def resources_names(self):
        total_count = self.get_resources_count()
        count = 5
        queryset = self.resources.all()[:count]
        resources = [r.name for r in queryset]
        if total_count > count:
            resources.append('...')

        return resources

    def get_resources_count(self):
        return self.resources.count()


class Recurrence(models.Model):
    class Meta:
        verbose_name = _('périodicité')
        verbose_name_plural = _('périodicités')

    def __str__(self):
        return str(self.id)


class BookingOccurrence(StartEndResources):
    class Meta:
        verbose_name = _('occurrence de réservation')
        verbose_name_plural = _('occurrences de réservation')

    is_valid = models.BooleanField(default=True, verbose_name=_('valide'))
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        verbose_name=_('réservation'),
        null=True
    )
    recurrence = models.ForeignKey(
        Recurrence,
        on_delete=models.CASCADE,
        verbose_name=_('périodicité'),
        null=True,
        default=None
    )

    resources = models.ManyToManyField(
        Resource,
        verbose_name=_('ressources'),
        through='OccurrenceResourceCount'
    )

    def __str__(self):
        dates = self.str_dates()
        resources = ', '.join([r.name for r in self.resources.all()])

        return _('%(booking)s (%(resources)s) ' + dates) % {
            'booking': self.booking,
            'resources': resources
        }

    def get_resources_count(self):
        return sum(map(lambda x: x.count, self.bookings.all()))

    def get_slots(self):
        time = self.start
        end = self.end

        delta = dt.timedelta(minutes=self.resources.first().category.granularity)

        slots = []

        # Allow 23:59:59 for end of day
        while time + delta <= end + dt.timedelta(seconds=1):
            slots.append(Slot(time, time + delta))
            time += delta

        return slots


class OccurrenceResourceCount(models.Model):
    occurrence = models.ForeignKey(
        to=BookingOccurrence,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    resource = models.ForeignKey(
        to=Resource,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    count = models.IntegerField(
        default=1,
        blank=True
    )


class ResourceLock(StartEndResources):
    class Meta:
        verbose_name = _('verrou de ressource')
        verbose_name_plural = _('verrous de ressource')

    reason = models.CharField(max_length=150)

    def __str__(self):
        dates = self.str_dates()
        resources = ', '.join([r.name for r in self.resources.all()])

        return _('[Verrou] %(reason)s (%(resources)s) ' + dates) % {
            'resources': resources,
            'reason': self.reason
        }
