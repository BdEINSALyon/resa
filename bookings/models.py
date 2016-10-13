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
    resource = models.ManyToManyField(
        Resource,
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


class BookingOccurrence(models.Model):
    class Meta:
        verbose_name = _('occurrence de réservation')
        verbose_name_plural = _('occurrences de réservation')

    start = models.DateTimeField(verbose_name=_('date et heure de début'))
    end = models.DateTimeField(verbose_name=_('date et heure de fin'))
    is_valid = models.BooleanField(default=True, verbose_name=_('valide'))
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE
    )


class RessourceLock(models.Model):
    class Meta:
        verbose_name = _('verrou de ressource')
        verbose_name_plural = _('verrous de ressource')

    start = models.DateTimeField(verbose_name=_('date de début'))
    end = models.DateTimeField(verbose_name=_('date de fin'))
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE
    )
