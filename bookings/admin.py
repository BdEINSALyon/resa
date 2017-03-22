from django.contrib import admin

from .models import Resource, ResourceCategory, Booking, BookingOccurrence, ResourceLock, Recurrence, \
    OccurrenceResourceCount, Place, Paragraph
from .forms import ResourceLockForm


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = 'name', 'category', 'available', 'number', 'place', 'booking_fee', 'guarantee', 'public'
    list_editable = 'available', 'number', 'place', 'booking_fee', 'guarantee', 'public'
    list_display_links = 'name',
    search_fields = 'name',
    list_filter = 'category', 'available'
    ordering = 'category', 'name'


@admin.register(ResourceLock)
class ResourceLockAdmin(admin.ModelAdmin):
    form = ResourceLockForm
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
    list_display = 'name', 'day_start', 'day_end', 'granularity', 'booking_form', 'public'
    list_editable = 'day_start', 'day_end', 'granularity', 'booking_form', 'public'
    list_display_links = 'name',
    search_fields = 'name',


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
    list_display = 'title', 'order_form', 'order_public', 'category'
    search_fields = 'title', 'content'
    list_filter = 'category',
    list_editable = 'order_form', 'order_public', 'category'
