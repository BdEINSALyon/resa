from django.conf.urls import url
from django.views.generic import TemplateView

from bookings.views import ResourceCategoryDayView, BookingDetailView, BookingOccurrenceCreateView, BookingUpdateView, \
    BookingOccurrenceUpdateView, BookingOccurrenceDeleteView

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='bookings/home.html'), name='home'),
    url(r'^resource-category/(?P<id>[0-9]+)$', ResourceCategoryDayView.as_view(), name='resource-category-day'),
    url(r'^booking/(?P<pk>[0-9]+)$', BookingDetailView.as_view(), name='booking-details'),
    url(r'^booking/(?P<pk>[0-9]+)/edit$', BookingUpdateView.as_view(), name='booking-update'),
    url(r'^booking/(?P<booking_pk>[0-9]+)/occurrence/new$',
        BookingOccurrenceCreateView.as_view(),
        name='occurrence-new'),
    url(r'^booking/(?P<booking_pk>[0-9]+)/occurrence/(?P<pk>[0-9]+)$',
        BookingOccurrenceUpdateView.as_view(),
        name='occurrence-edit'),
    url(r'^booking/(?P<booking_pk>[0-9]+)/occurrence/(?P<pk>[0-9]+)/delete$',
        BookingOccurrenceDeleteView.as_view(),
        name='occurrence-delete'),
]
