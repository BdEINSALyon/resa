from django.conf.urls import url
from django.views.generic import TemplateView

from bookings.views.bookings import BookingDetailView, BookingUpdateView, BookingDeleteView, BookingCreateView
from bookings.views.occurrences import BookingOccurrenceCreateView, BookingOccurrenceUpdateView, \
    BookingOccurrenceDeleteView
from bookings.views.other import ResourceCategoryDayView, SearchResultsListView, \
    CountableOccurrencesList, BookingFormView
from bookings.views.api_va import api_va

urlpatterns = [
    url(r'^home$', TemplateView.as_view(template_name='bookings/home.html'), name='home'),
    url(r'^resource-category/(?P<id>[0-9]+)$', ResourceCategoryDayView.as_view(), name='resource-category-day'),
    url(r'^form/(?P<pk>[0-9]+)$', BookingFormView.as_view(), name='booking-form'),
    url(r'^booking/(?P<pk>[0-9]+)$', BookingDetailView.as_view(), name='booking-details'),
    url(r'^booking/(?P<pk>[0-9]+)/edit$', BookingUpdateView.as_view(), name='booking-update'),
    url(r'^booking/(?P<pk>[0-9]+)/delete$', BookingDeleteView.as_view(), name='booking-delete'),
    url(r'^booking/new$', BookingCreateView.as_view(), name='booking-new'),
    url(r'^booking/(?P<booking_pk>[0-9]+)/occurrence/new$',
        BookingOccurrenceCreateView.as_view(),
        name='occurrence-new'),
    url(r'^booking/(?P<booking_pk>[0-9]+)/occurrence/(?P<pk>[0-9]+)$',
        BookingOccurrenceUpdateView.as_view(),
        name='occurrence-edit'),
    url(r'^booking/(?P<booking_pk>[0-9]+)/occurrence/(?P<pk>[0-9]+)/delete$',
        BookingOccurrenceDeleteView.as_view(),
        name='occurrence-delete'),
    url(r'^search$',
        SearchResultsListView.as_view(),
        name='search'),
    url(r'^occurrences$',
        CountableOccurrencesList.as_view(),
        name='occurrences_filter'),
    url(r'^api/va/(?P<va_key>c[0-9]+)$',
        api_va,
        name='occurrences_filter'),
    url(r'^help$', TemplateView.as_view(template_name='bookings/help.html'), name='help')
]
