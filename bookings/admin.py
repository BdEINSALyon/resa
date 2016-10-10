from django.contrib import admin
from .models import Resource, ResourceCategory, Planning, PlanningSlot, BookingCategory, Booking


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = 'name',
    list_display_links = 'name',
    search_fields = 'name',

admin.site.register(ResourceCategory)
admin.site.register(Planning)
admin.site.register(PlanningSlot)
admin.site.register(BookingCategory)
admin.site.register(Booking)
