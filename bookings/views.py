from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView

from bookings.models import ResourceCategory, Resource


class ResourceCategoryCalendarView(ListView):
    template_name = 'bookings/resource_category_calendar.html'

    def get_queryset(self):
        category = get_object_or_404(ResourceCategory, id=self.kwargs['id'])
        return Resource.objects.filter(category=category)


class AllResourcesView(ListView):
    model = Resource


class AllResourceCategoriesView(ListView):
    template_name = 'bookings/all_resource_categories.html'
    context_object_name = 'resource_category_list'
    model = ResourceCategory
