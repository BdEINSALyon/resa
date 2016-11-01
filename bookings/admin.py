from django.contrib import admin
from .models import Resource, ResourceCategory, BookingCategory, Booking, BookingOccurrence, ResourceLock


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = 'name', 'category', 'available'
    list_editable = 'available',
    list_display_links = 'name',
    search_fields = 'name',
    list_filter = 'category', 'available'
    ordering = 'category', 'name'

admin.site.register(ResourceCategory)
admin.site.register(BookingCategory)
admin.site.register(BookingOccurrence)
admin.site.register(Booking)
admin.site.register(ResourceLock)
