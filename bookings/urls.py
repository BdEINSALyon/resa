from django.conf.urls import url
from django.views.generic import TemplateView

from bookings.views import ResourceCategoryDayView, BookingDetailView

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='bookings/home.html'), name='home'),
    url(r'^resource-category/(?P<id>[0-9]+)$', ResourceCategoryDayView.as_view(), name='resource-category-day'),
    url(r'^booking/(?P<pk>[0-9]+)$', BookingDetailView.as_view(), name='booking-details'),
]
