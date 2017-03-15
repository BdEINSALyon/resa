from django.contrib import admin

from .models import Resource, ResourceCategory, BookingCategory, Booking, BookingOccurrence, ResourceLock, Recurrence, \
    OccurrenceResourceCount, Place, Paragraph


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = 'name', 'category', 'available', 'number', 'place', 'booking_fee', 'guarantee'
    list_editable = 'available', 'number', 'place', 'booking_fee', 'guarantee'
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


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = 'name',
    list_display_links = 'name',
    ordering = 'name',
    search_fields = 'name',


@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = 'name', 'parent', 'day_start', 'day_end', 'granularity', 'booking_form'
    list_editable = 'parent', 'day_start', 'day_end', 'granularity', 'booking_form'
    list_display_links = 'name',
    search_fields = 'name',


@admin.register(BookingCategory)
class BookingCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(BookingOccurrence)
class BookingOccurrenceAdmin(admin.ModelAdmin):
    pass


@admin.register(Recurrence)
class RecurrenceAdmin(admin.ModelAdmin):
    pass


@admin.register(OccurrenceResourceCount)
class OccurrenceResourceCountAdmin(admin.ModelAdmin):
    list_display = 'occurrence', 'resource', 'count'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = 'reason', 'category', 'contact_asso', 'contact_first_name', 'contact_last_name'
    search_fields = 'reason', 'details', 'contact_asso', 'contact_first_name', 'contact_last_name'
    list_filter = 'category',
    list_editable = 'category', 'contact_asso', 'contact_first_name', 'contact_last_name'


@admin.register(Paragraph)
class ParagraphAdmin(admin.ModelAdmin):
    list_display = 'title', 'order', 'category'
    search_fields = 'title', 'content'
    list_filter = 'category',
    list_editable = 'order', 'category'
