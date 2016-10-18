import datetime as dt
import logging

from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

log = logging.getLogger(__name__)


class BookingOwner(models.Model):
    class Meta:
        verbose_name = _('propriétaire de réservation')
        verbose_name_plural = _('propriétaires de réservation')

    name = models.CharField(max_length=150, verbose_name=_('nom'))
    barcode = models.CharField(max_length=20, verbose_name=_('code barre'), blank=True)

    def __str__(self):
        return self.name


class ResourceCategory(models.Model):
    class Meta:
        verbose_name = _('catégorie de ressource')
        verbose_name_plural = _('catégories de ressource')

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

    def get_absolute_url(self):
        return reverse('bookings:resource-category-calendar', kwargs={'id': str(self.id)})

    def __str__(self):
        return self.name

    def get_slots(self):
        time = dt.datetime.combine(dt.date.today(), self.day_start)
        end = dt.datetime.combine(dt.date.today(), self.day_end)

        # Allow midnight for end of day
        if self.day_end == dt.time(0, 0):
            end += dt.timedelta(days=1)

        delta = dt.timedelta(minutes=self.granularity)

        slots = []

        # Allow 23:59:59 for end of day
        while time + delta <= end + dt.timedelta(seconds=1):
            slots.append({
                'start': time.time(),
                'end': (time + delta).time()
            })
            time += delta

        return slots


class Resource(models.Model):
    class Meta:
        verbose_name = _('ressource')
        verbose_name_plural = _('ressources')

    name = models.CharField(max_length=150, verbose_name=_('nom'))
    category = models.ForeignKey(
        ResourceCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('catégorie')
    )
    available = models.BooleanField(verbose_name=_('disponible'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('bookings:resource', kwargs={'id': str(self.id)})

    def __str__(self):
        return self.name

    def get_occurrences(self, year=dt.date.today().year, month=dt.date.today().month, day=dt.date.today().day):
        occurrences = BookingOccurrence.objects.filter(booking__resources__exact=self)
        log.error(occurrences)


class BookingCategory(models.Model):
    class Meta:
        verbose_name = _('catégorie de réservation')
        verbose_name_plural = _('catégories de réservation')

    name = models.CharField(max_length=150, verbose_name=_('nom'))

    def __str__(self):
        return self.name


class Booking(models.Model):
    class Meta:
        verbose_name = _('réservation')
        verbose_name_plural = _('réservations')

    reason = models.CharField(max_length=150, verbose_name=_('raison'))
    details = models.TextField(verbose_name=_('détails'), blank=True)
    resources = models.ManyToManyField(
        Resource,
        verbose_name=_('ressource')
    )
    category = models.ForeignKey(
        BookingCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('catégorie de réservation')
    )
    owner = models.ForeignKey(
        BookingOwner,
        on_delete=models.CASCADE,
        null=True,
        verbose_name=_('propriétaire')
    )

    def __str__(self):
        return _('Réservation par %(owner)s pour %(reason)s') % {
            'owner': self.owner.name,
            'reason': self.reason
        }


class BookingOccurrence(models.Model):
    class Meta:
        verbose_name = _('occurrence de réservation')
        verbose_name_plural = _('occurrences de réservation')

    start = models.DateTimeField(verbose_name=_('date et heure de début'))
    end = models.DateTimeField(verbose_name=_('date et heure de fin'))
    is_valid = models.BooleanField(default=True, verbose_name=_('valide'))
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        verbose_name=_('réservation')
    )

    def __str__(self):
        return _('%(booking)s du %(start)s au %(end)s') % {
            'booking': self.booking,
            'start': self.start,
            'end': self.end
        }


class ResourceLock(models.Model):
    class Meta:
        verbose_name = _('verrou de ressource')
        verbose_name_plural = _('verrous de ressource')

    start = models.DateTimeField(verbose_name=_('date de début'))
    end = models.DateTimeField(verbose_name=_('date de fin'))
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        verbose_name=_('ressource')
    )

    def __str__(self):
        return _('Verrou du %(start)s au %(end)s.') % {'start': self.start, 'end': self.end}
