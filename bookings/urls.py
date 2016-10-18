from django.conf.urls import url

from bookings.views import ResourceCategoryDayView, AllResourcesView, AllResourceCategoriesView

urlpatterns = [
    url(r'^resource-category/$', AllResourceCategoriesView.as_view(), name='all-resource-categories'),
    url(r'^resource-category/(?P<id>[0-9]+)$', ResourceCategoryDayView.as_view(), name='resource-category-calendar'),
    url(r'^resource/$', AllResourcesView.as_view(), name='all-resources'),
    url(r'^resource/(?P<id>[0-9]+)$', AllResourcesView.as_view(), name='resource'),
]
