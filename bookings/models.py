from django.db import models
from django.utils.translation import ugettext_lazy as _


class BookingOwner(models.Model):
    class Meta:
        verbose_name = _('propriétaire de réservation')
        verbose_name_plural = _('propriétaires de réservation')

    name = models.CharField(max_length=150, verbose_name=_('nom'))
    barcode = models.CharField(max_length=20, verbose_name=_('code barre'))

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
        verbose_name=_('catégorie parente')
    )

    def __str__(self):
        return self.name


class Resource(models.Model):
    class Meta:
        verbose_name = _('ressource')
        verbose_name_plural = _('ressources')

    name = models.CharField(max_length=150, verbose_name=_('nom'))
    category = models.ForeignKey(
        ResourceCategory,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('catégorie')
    )
    available = models.BooleanField(verbose_name=_('disponible'))
    granularity = models.PositiveIntegerField(verbose_name=_('granularité'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class BookingCategory(models.Model):
    class Meta:
        verbose_name = _('catégorie de réservation')
        verbose_name_plural = _('catégories de réservation')

    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class Booking(models.Model):
    class Meta:
        verbose_name = _('réservation')
        verbose_name_plural = _('réservations')

    name = models.CharField(max_length=150, verbose_name=_('nom'))
    details = models.TextField(verbose_name=_('détails'))
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        verbose_name=_('ressource')
    )
    category = models.ForeignKey(
        BookingCategory,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('catégorie de réservation')
    )
    owner = models.ForeignKey(
        BookingOwner,
        on_delete=models.CASCADE,
        null=True,
        verbose_name=_('propriétaire')
    )


class BookingPlan(models.Model):
    class Meta:
        pass

    start = models.DateField(verbose_name=_('date de début'))
    end = models.DateField(verbose_name=_('date de fin'))
    is_valid = models.BooleanField(default=True, verbose_name=_('valide'))

    DAILY = 'DA'
    WEEKLY = 'WE1'
    ONE_WEEK_OVER_TWO = 'WE2'
    ONE_WEEK_OVER_THREE = 'WE3'
    ONE_WEEK_OVER_FOUR = 'WE4'
    ONE_WEEK_OVER_FIVE = 'WE5'
    MONTHLY = 'MO'
    YEARLY = 'YE'

    PERIODICITY_CHOICES = (
        (DAILY, _('chaque jour')),
        (WEEKLY, _('chaque semaine')),
        (ONE_WEEK_OVER_TWO, _('une semaine sur deux')),
        (ONE_WEEK_OVER_THREE, _('une semaine sur trois')),
        (ONE_WEEK_OVER_FOUR, _('une semaine sur quatre')),
        (ONE_WEEK_OVER_FIVE, _('une semaine sur cinq')),
        (MONTHLY, _('chaque mois')),
        (YEARLY, _('chaque année'))
    )

    periodicity = models.CharField(max_length=4, choices=PERIODICITY_CHOICES, null=True, verbose_name=_('périodicité'))


class LocationTime(models.Model):
    start = models.TimeField(verbose_name=_('heure de début'))
    end = models.TimeField(verbose_name=_('heure de fin'))


class RessourceLock(models.Model):
    start = models.DateTimeField(verbose_name=_('date de début'))
    end = models.DateTimeField(verbose_name=_('date de fin'))
