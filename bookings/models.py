from django.db import models


class ResourceCategory(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class Resource(models.Model):
    name = models.CharField(max_length=150)
    category = models.ForeignKey(
        ResourceCategory,
        on_delete=models.CASCADE
    )
    available = models.BooleanField()

    def __str__(self):
        return self.name


class PlanningSlot(models.Model):
    MONDAY = 'Mon'
    TUESDAY = 'Tue'
    WEDNESDAY = 'Wed'
    THURSDAY = 'Thu'
    FRIDAY = 'Fri'
    SATURDAY = 'Sat'
    SUNDAY = 'Sun'

    DAYS_OF_WEEK = (
        (MONDAY, 'Lundi'),
        (TUESDAY, 'Mardi'),
        (WEDNESDAY, 'Mercredi'),
        (THURSDAY, 'Jeudi'),
        (FRIDAY, 'Vendredi'),
        (SATURDAY, 'Samedi'),
        (SUNDAY, 'Dimanche')
    )

    day_of_week = models.CharField(max_length=3, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()


class Planning(models.Model):
    slots = models.ManyToManyField(
        PlanningSlot
    )


class BookingCategory(models.Model):
    name = models.CharField(max_length=150)


class Booking(models.Model):
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
