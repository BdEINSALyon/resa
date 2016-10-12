from django.contrib import admin
from .models import Resource, ResourceCategory, BookingCategory, Booking, BookingOwner, BookingPlan, LocationTime, RessourceLock


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = 'name',
    list_display_links = 'name',
    search_fields = 'name',

admin.site.register(ResourceCategory)
admin.site.register(BookingOwner)
admin.site.register(BookingCategory)
admin.site.register(Booking)
admin.site.register(BookingPlan)
admin.site.register(LocationTime)
admin.site.register(RessourceLock)
