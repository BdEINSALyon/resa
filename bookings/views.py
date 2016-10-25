import calendar
import datetime as dt
import logging

import dateutil.parser
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic.base import ContextMixin

from bookings.forms import BookingOccurrenceForm
from bookings.models import ResourceCategory, Resource, Booking, BookingOccurrence

log = logging.getLogger(__name__)


class ResourceCategoryDayView(ListView):
    template_name = 'bookings/resource_category_day.html'
    context_object_name = 'resource_list'
    category = None

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(ResourceCategory, pk=kwargs['id'])
        return super(ResourceCategoryDayView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
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
        date = dt.date(day=day, month=month, year=year)
        context['date'] = date

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
        for slot in self.category.get_slots(date):
            line = {
                'slot': slot
            }
            cells = []
            for resource in resources:
                occurrence = slot.get_occurrence(occurrences[resource.id])
                if occurrence is not None:
                    if already_seen_occurrences.get(resource.id) is None:
                        already_seen_occurrences[resource.id] = []

                    if occurrence not in already_seen_occurrences[resource.id]:
                        already_seen_occurrences[resource.id].append(occurrence)

                        cells.append({
                            'type': 'start',
                            'rowspan': self.get_number_of_slots_for_occurrence(occurrence, date),
                            'occurrence': occurrence
                        })

                    else:
                        cells.append({
                            'type': 'continue'
                        })
                else:
                    cells.append({
                        'type': 'free',
                        'resource': resource
                    })
            line['cells'] = cells
            lines.append(line)

        context['lines'] = lines

        return context

    def get_number_of_slots_for_occurrence(self, occurrence, date):
        count = 0
        for slot in self.category.get_slots(date):
            if occurrence.contains_slot(slot):
                count += 1

        return count


class BaseBookingView(ContextMixin):
    booking = None

    def get_context_data(self, **kwargs):
        context = super(BaseBookingView, self).get_context_data(**kwargs)
        page = self.request.GET.get('occ_page', 1)

        occurrences = self.booking.get_occurrences()
        paginator = Paginator(occurrences, 10)

        try:
            occurrences = paginator.page(page)
        except EmptyPage:
            occurrences = paginator.page(paginator.num_pages)

        context['occurrences'] = occurrences
        return context


class BookingDetailView(DetailView, BaseBookingView):
    model = Booking
    template_name = 'bookings/booking_detail.html'
    booking = None

    def dispatch(self, request, *args, **kwargs):
        self.booking = get_object_or_404(Booking, pk=self.kwargs['pk'])
        return super(BookingDetailView, self).dispatch(request, *args, **kwargs)

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return super(BookingDetailView, self).get(request, *args, **kwargs)


class BookingOccurrenceCreateView(CreateView, BaseBookingView):
    form_class = BookingOccurrenceForm
    template_name = 'bookings/occurrence_new.html'
    decorators = [login_required, permission_required('bookings.add_bookingoccurrence')]
    booking = None
    object = None
    start = None
    end = None
    initial_resource = None

    def get_success_url(self):
        return reverse('bookings:booking-details', kwargs={'pk': self.booking.id})

    def dispatch(self, request, *args, **kwargs):
        self.booking = get_object_or_404(Booking, pk=self.kwargs['booking_pk'])
        try:
            self.initial_resource = get_object_or_404(Resource, pk=int(request.GET.get('resource')))
        except TypeError:
            pass

        start = request.GET.get('start')
        end = request.GET.get('end')

        if start is not None:
            self.start = dateutil.parser.parse(start)

        if end is not None:
            self.end = dateutil.parser.parse(end)

        return super(BookingOccurrenceCreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BookingOccurrenceCreateView, self).get_context_data(**kwargs)
        context['booking'] = self.booking

        return context

    def get_form(self, *args, form_class=BookingOccurrenceForm):
        if form_class is BookingOccurrenceForm:
            return form_class(*args, booking_pk=self.booking.id, initial={
                'start': self.start,
                'end': self.end,
                'resources': [self.initial_resource]
            })

        return form_class(*args)

    @method_decorator(decorators)
    def post(self, request, *args, **kwargs):
        form = self.get_form(request.POST)

        if form.is_valid():
            form.save()

            messages.success(request, _('Occurrence créée avec succès'))
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    @method_decorator(decorators)
    def get(self, request, *args, **kwargs):
        return super(BookingOccurrenceCreateView, self).get(request, *args, **kwargs)


class BookingOccurrenceUpdateView(UpdateView, BaseBookingView):
    model = BookingOccurrence
    form_class = BookingOccurrenceForm
    template_name = 'bookings/occurrence_edit.html'
    decorators = [login_required, permission_required('bookings.change_bookingoccurrence')]
    booking = None

    def dispatch(self, request, *args, **kwargs):
        self.booking = get_object_or_404(Booking, pk=self.kwargs['booking_pk'])
        return super(BookingOccurrenceUpdateView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('bookings:booking-details', kwargs={'pk': str(self.kwargs.get('booking_pk'))})

    def get_context_data(self, **kwargs):
        context = super(BookingOccurrenceUpdateView, self).get_context_data(**kwargs)
        context['booking'] = self.booking
        context['current_occurrence'] = self.get_object()

        return context

    @method_decorator(decorators)
    def get(self, request, *args, **kwargs):
        return super(BookingOccurrenceUpdateView, self).get(request, *args, **kwargs)

    @method_decorator(decorators)
    def post(self, request, *args, **kwargs):
        return super(BookingOccurrenceUpdateView, self).post(request, *args, **kwargs)


class BookingUpdateView(UpdateView, BaseBookingView):
    model = Booking
    template_name = 'bookings/booking_edit.html'
    fields = ['reason', 'details', 'category', 'owner']
    decorators = [login_required, permission_required('bookings.change_booking')]
    booking = None

    def dispatch(self, request, *args, **kwargs):
        self.booking = get_object_or_404(Booking, pk=self.kwargs['pk'])
        return super(BookingUpdateView, self).dispatch(request, *args, **kwargs)

    @method_decorator(decorators)
    def get(self, request, *args, **kwargs):
        return super(BookingUpdateView, self).get(request, *args, **kwargs)

    @method_decorator(decorators)
    def post(self, request, *args, **kwargs):
        return super(BookingUpdateView, self).post(request, *args, **kwargs)


class BookingOccurrenceDeleteView(DeleteView, BaseBookingView):
    model = BookingOccurrence
    decorators = [login_required, permission_required('bookings.delete_bookingoccurrence')]
    booking = None
    template_name = 'bookings/occurrence_delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.booking = get_object_or_404(Booking, pk=self.kwargs['booking_pk'])
        return super(BookingOccurrenceDeleteView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BookingOccurrenceDeleteView, self).get_context_data(**kwargs)
        context['booking'] = self.booking

        return context

    def get_success_url(self):
        return reverse_lazy('bookings:booking-details', kwargs={'pk': str(self.booking.pk)})

    @method_decorator(decorators)
    def get(self, request, *args, **kwargs):
        return super(BookingOccurrenceDeleteView, self).get(request, *args, **kwargs)

    @method_decorator(decorators)
    def delete(self, request, *args, **kwargs):
        return super(BookingOccurrenceDeleteView, self).delete(request, *args, **kwargs)


class BookingDeleteView(DeleteView, BaseBookingView):
    model = Booking
    decorators = [login_required, permission_required('bookings.delete_booking')]
    booking = None
    template_name = 'bookings/booking_delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.booking = self.get_object()
        return super(BookingDeleteView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BookingDeleteView, self).get_context_data(**kwargs)
        context['booking'] = self.booking

        return context

    def get_success_url(self):
        return reverse_lazy('bookings:home')

    @method_decorator(decorators)
    def get(self, request, *args, **kwargs):
        return super(BookingDeleteView, self).get(request, *args, **kwargs)

    @method_decorator(decorators)
    def delete(self, request, *args, **kwargs):
        return super(BookingDeleteView, self).delete(request, *args, **kwargs)


class BookingCreateView(CreateView):
    model = Booking
    fields = ['reason', 'details', 'category', 'owner']
    template_name = 'bookings/booking_new.html'
    decorators = [login_required, permission_required('bookings.add_booking')]
    start = None
    end = None
    booking = None
    resource_id = None

    def get_success_url(self):
        return reverse('bookings:occurrence-new', kwargs={'booking_pk': self.booking.pk}) \
               + '?start=' + str(self.start.isoformat()) \
               + '&end=' + str(self.end.isoformat())\
               + '&resource=' + str(self.resource_id)

    def dispatch(self, request, *args, **kwargs):
        self.resource_id = str(self.request.GET.get('resource'))

        start = self.request.GET.get('start')
        end = self.request.GET.get('end')

        if start is not None:
            self.start = dateutil.parser.parse(start)
        else:
            self.start = dt.datetime.now()

        if end is not None:
            self.end = dateutil.parser.parse(end)
        else:
            self.end = self.start

        return super(BookingCreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BookingCreateView, self).get_context_data(**kwargs)
        context['start'] = self.start
        context['end'] = self.end
        context['resource_id'] = self.resource_id

        return context

    @method_decorator(decorators)
    def post(self, request, *args, **kwargs):
        form = self.get_form()

        if form.is_valid():
            self.booking = form.save()

            messages.success(request, _('Réservation créée avec succès'))
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    @method_decorator(decorators)
    def get(self, request, *args, **kwargs):
        return super(BookingCreateView, self).get(request, *args, **kwargs)
