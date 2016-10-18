from django.conf.urls import url
from django.views.generic import TemplateView

from bookings.views import ResourceCategoryDayView, AllResourcesView

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='bookings/home.html'), name='home'),
    url(r'^resource-category/(?P<id>[0-9]+)$', ResourceCategoryDayView.as_view(), name='resource-category-calendar'),
    url(r'^resource/$', AllResourcesView.as_view(), name='all-resources'),
    url(r'^resource/(?P<id>[0-9]+)$', AllResourcesView.as_view(), name='resource'),
]
