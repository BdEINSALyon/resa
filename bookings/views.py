import datetime as dt

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

        resources = self.get_queryset()
        day = int(self.request.GET.get('day', dt.date.today().day))
        month = int(self.request.GET.get('month', dt.date.today().month))
        year = int(self.request.GET.get('year', dt.date.today().year))

        context['date'] = dt.date(day=day, month=month, year=year)

        occurrences = {}

        for resource in resources:
            occurrences[resource.id] = []
            for occurrence in resource.get_occurrences(year=year, month=month, day=day):
                occurrences[resource.id].append(occurrence)

        context['occurrences'] = occurrences
        return context


class AllResourcesView(ListView):
    model = Resource

