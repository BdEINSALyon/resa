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


@admin.register(ResourceLock)
class ResourceLockAdmin(admin.ModelAdmin):
    list_display = 'reason', 'start', 'end'
    list_display_links = 'reason',
    search_fields = 'reason',
    date_hierarchy = 'start'
    list_filter = 'resources',
    filter_horizontal = 'resources',


@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = 'name', 'parent', 'day_start', 'day_end', 'granularity'
    list_editable = 'parent', 'day_start', 'day_end', 'granularity'
    list_display_links = 'name',
    search_fields = 'name',


@admin.register(BookingCategory)
class BookingCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(BookingOccurrence)
class BookingOccurrenceAdmin(admin.ModelAdmin):
    pass


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = 'reason', 'category', 'owner'
    search_fields = 'reason', 'details', 'owner'
    list_filter = 'category',
    list_editable = 'category', 'owner'
