import calendar
import datetime as dt
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from bookings.forms import BookingOccurrenceForm
from bookings.models import ResourceCategory, Resource, Booking, BookingOccurrence

log = logging.getLogger(__name__)


def get_occurrence_for_slot(occurrences, slot):
    for occurrence in occurrences:
        if occurrence.contains_slot(slot):
            return occurrence

    return None


class ResourceCategoryDayView(ListView):
    template_name = 'bookings/resource_category_day.html'
    context_object_name = 'resource_list'

    def get_queryset(self):
        self.category = get_object_or_404(ResourceCategory, id=self.kwargs['id'])
        return Resource.objects.filter(category=self.category)

    def get_context_data(self, **kwargs):
        context = super(ResourceCategoryDayView, self).get_context_data(**kwargs)

        # Category
        context['category'] = self.category

        # Date
        day = int(self.request.GET.get('day', dt.date.today().day))
        month = int(self.request.GET.get('month', dt.date.today().month))
        year = int(self.request.GET.get('year', dt.date.today().year))
        while month > 12:
            year += 1
            month -= 12
        self.date = dt.date(day=day, month=month, year=year)
        context['date'] = self.date

        context['today'] = dt.date.today()

        # Month calendar
        cal = calendar.Calendar()
        days_in_month = cal.itermonthdates(year, month)
        weeks = []
        week_index = 0
        for month_day in days_in_month:
            weeks.append([])
            weeks[week_index].append(month_day)
            if month_day.weekday() == 6:
                week_index += 1
        context['weeks'] = weeks

        # Booking occurrences
        occurrences = {}
        resources = self.get_queryset()
        for resource in resources:
            occurrences[resource.id] = []
            for occurrence in resource.get_occurrences(year=year, month=month, day=day):
                occurrences[resource.id].append(occurrence)

        lines = []
        already_seen_occurrences = {}
        for slot in self.category.get_slots(self.date):
            line = {
                'slot': slot
            }
            cells = []
            for resource in resources:
                occurrence = get_occurrence_for_slot(occurrences[resource.id], slot)
                if occurrence is not None:
                    if already_seen_occurrences.get(resource.id) is None:
                        already_seen_occurrences[resource.id] = []

                    if occurrence not in already_seen_occurrences[resource.id]:
                        already_seen_occurrences[resource.id].append(occurrence)

                        cells.append({
                            'type': 'start',
                            'rowspan': self.get_number_of_slots_for_occurrence(occurrence),
                            'occurrence': occurrence
                        })

                    else:
                        cells.append({
                            'type': 'continue'
                        })
                else:
                    cells.append({
                        'type': 'free'
                    })
            line['cells'] = cells
            lines.append(line)

        context['lines'] = lines

        return context

    def get_number_of_slots_for_occurrence(self, occurrence):
        count = 0
        for slot in self.category.get_slots(self.date):
            if occurrence.contains_slot(slot):
                count += 1

        return count


class BookingDetailView(DetailView):
    model = Booking
    template_name = 'bookings/booking_detail.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return super(BookingDetailView, self).get(request, *args, **kwargs)


class BookingOccurrenceCreateView(CreateView):
    form_class = BookingOccurrenceForm
    template_name = 'bookings/occurrence_new.html'
    decorators = [login_required, permission_required('bookings.add_bookingoccurrence')]

    def get_context_data(self, **kwargs):
        context = super(BookingOccurrenceCreateView, self).get_context_data(**kwargs)
        context['booking'] = get_object_or_404(Booking, pk=self.kwargs['booking_pk'])

        return context

    @method_decorator(decorators)
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            occurrence = form.save()
            booking = get_object_or_404(Booking, pk=self.kwargs['booking_pk'])
            occurrence.booking = booking
            occurrence.save()

            messages.success(request, 'Occurrence created successfully')
            return redirect('bookings:booking-details', pk=booking.pk)

    @method_decorator(decorators)
    def get(self, request, *args, **kwargs):
        return super(BookingOccurrenceCreateView, self).get(request, *args, **kwargs)


class BookingOccurrenceUpdateView(UpdateView):
    model = BookingOccurrence
    form_class = BookingOccurrenceForm
    template_name = 'bookings/occurrence_edit.html'
    decorators = [login_required, permission_required('bookings.add_bookingoccurrence')]

    def get_success_url(self):
        return reverse('bookings:booking-details', kwargs={'pk': str(self.kwargs.get('booking_pk'))})

    def get_context_data(self, **kwargs):
        context = super(BookingOccurrenceUpdateView, self).get_context_data(**kwargs)
        context['booking'] = get_object_or_404(Booking, pk=self.kwargs['booking_pk'])

        return context

    @method_decorator(decorators)
    def get(self, request, *args, **kwargs):
        return super(BookingOccurrenceUpdateView, self).get(request, *args, **kwargs)

    @method_decorator(decorators)
    def post(self, request, *args, **kwargs):
        return super(BookingOccurrenceUpdateView, self).post(request, *args, **kwargs)


class BookingUpdateView(UpdateView):
    model = Booking
    template_name = 'bookings/booking_edit.html'
    fields = ['reason', 'details', 'resources', 'category', 'owner']

    decorators = [login_required, permission_required('bookings.change_booking')]

    @method_decorator(decorators)
    def get(self, request, *args, **kwargs):
        return super(BookingUpdateView, self).get(request, *args, **kwargs)

    @method_decorator(decorators)
    def post(self, request, *args, **kwargs):
        return super(BookingUpdateView, self).post(request, *args, **kwargs)
