from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from bookings.models import ResourceCategory, Resource


class ResourceCategoryDayView(ListView):
    template_name = 'bookings/resource_category_calendar.html'
    context_object_name = 'resource_list'

    def get_queryset(self):
        self.category = get_object_or_404(ResourceCategory, id=self.kwargs['id'])
        return Resource.objects.filter(category=self.category)

    def get_context_data(self, **kwargs):
        context = super(ResourceCategoryDayView, self).get_context_data(**kwargs)
        context['category'] = self.category
        return context


class AllResourcesView(ListView):
    model = Resource

