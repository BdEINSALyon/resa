from django.db import models
from django.utils.translation import ugettext_lazy as _


class ResourceCategory(models.Model):
    class Meta:
        verbose_name = _('catégorie de ressource')
        verbose_name_plural = _('catégories de ressource')

    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class Resource(models.Model):
    class Meta:
        verbose_name = _('ressource')
        verbose_name_plural = _('ressources')

    name = models.CharField(max_length=150)
    category = models.ForeignKey(
        ResourceCategory,
        on_delete=models.CASCADE
    )
    available = models.BooleanField()

    def __str__(self):
        return self.name


class PlanningSlot(models.Model):
    class Meta:
        verbose_name = _('créneau')
        verbose_name_plural = _('créneaux')

    MONDAY = 'Mon'
    TUESDAY = 'Tue'
    WEDNESDAY = 'Wed'
    THURSDAY = 'Thu'
    FRIDAY = 'Fri'
    SATURDAY = 'Sat'
    SUNDAY = 'Sun'

    DAYS_OF_WEEK = (
        (MONDAY, _('Lundi')),
        (TUESDAY, _('Mardi')),
        (WEDNESDAY, _('Mercredi')),
        (THURSDAY, _('Jeudi')),
        (FRIDAY, _('Vendredi')),
        (SATURDAY, _('Samedi')),
        (SUNDAY, _('Dimanche'))
    )

    day_of_week = models.CharField(max_length=3, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()


class Planning(models.Model):
    slots = models.ManyToManyField(
        PlanningSlot
    )


class BookingCategory(models.Model):
    class Meta:
        verbose_name = _('catégorie de réservation')
        verbose_name_plural = _('catégories de réservation')

    name = models.CharField(max_length=150)


class Booking(models.Model):
    class Meta:
        verbose_name = _('réservation')
        verbose_name_plural = _('réservations')

    name = models.CharField(max_length=150)
    details = models.TextField()
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE
    )
    category = models.ForeignKey(
        BookingCategory,
        on_delete=models.CASCADE
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
