import calendar
import datetime as dt
import logging
import re
from collections import defaultdict

from html import escape

import dateutil.parser
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.views.generic.base import ContextMixin

from bookings.forms import BookingOccurrenceForm, BookingOccurrenceUpdateForm, BookingFormForm
from bookings.models import ResourceCategory, Resource, Booking, BookingOccurrence, OccurrenceResourceCount, Recurrence

log = logging.getLogger(__name__)


class ResourceCategoryDayView(ListView):
    template_name = 'bookings/resource_category_day.html'
    context_object_name = 'resource_list'
    category = None
    decorators = []

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(ResourceCategory, pk=kwargs['id'])

        if not self.category.public and len(self.decorators) == 0:
            self.decorators.append(login_required)
        elif len(self.decorators) > 0:
            self.decorators.pop()

        return super(ResourceCategoryDayView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        resources = Resource.objects.filter(category=self.category, available=True)
        if not self.request.user.is_authenticated():
            resources = resources.filter(public=True)
        return resources

    @method_decorator(decorators)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ResourceCategoryDayView, self).get_context_data(**kwargs)

        # Category
        context['category'] = self.category
        context['paragraphs'] = self.category.paragraphs.filter(order_public__gt=0).order_by('order_public')

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
        locks = {}
        resources = self.get_queryset()
        for resource in resources:
            occurrences[resource.id] = []
            locks[resource.id] = []
            for occurrence in resource.get_occurrences(year=year, month=month, day=day):
                occurrences[resource.id].append(occurrence)

            for lock in resource.get_locks(year, month, day):
                locks[resource.id].append(lock)

        lines = []
        already_seen = defaultdict(list)
        for slot in self.category.get_slots(date):
            line = {
                'slot': slot
            }
            cells = []
            for resource in resources:
                if not resource.is_countable():
                    occurrence = slot.get_period(occurrences[resource.id])
                else:
                    occurrence = slot.get_periods(occurrences[resource.id])
                lock = slot.get_period(locks[resource.id])

                if occurrence is not None:  # We found an occurrence to display
                    if isinstance(occurrence, list):  # It's a countable resource
                        all_continuous = {slot}
                        found_occurrences = set()
                        continuous_slots(occurrence, all_continuous, occurrences[resource.id], found_occurrences)

                        # Remove the slots after day end and before the current slot since we want to display
                        # a cell from the current slot to some rows after.
                        continuous = set()
                        for s in all_continuous:
                            end = dt.datetime.combine(date, resource.category.day_end)
                            if resource.category.day_end == dt.time(0, 0):
                                # Since 13/03/2017 00:00 is considered in the beginning of the day
                                # and we allowed 00:00 for end of day, if we look at an end of day
                                # at 00:00, we should consider 00:00 the next day.
                                end += dt.timedelta(days=1)
                            if s.start >= slot.start and s.end <= end:
                                continuous.add(s)

                        if found_occurrences not in already_seen[resource.id]:
                            already_seen[resource.id].append(found_occurrences)

                            cells.append({
                                'type': 'start',
                                'rowspan': len(continuous),
                                'occurrences': map(lambda x: x.pk, found_occurrences),
                                'colspan': 1
                            })
                            cells.append({
                                'type': 'free',
                                'resource': resource,
                                'count': resource.count_available(slot.start, slot.end),
                                'colspan': 1
                            })
                        else:
                            cells.append({
                                'type': 'continue'
                            })
                            cells.append({
                                'type': 'free',
                                'resource': resource,
                                'count': resource.count_available(slot.start, slot.end),
                                'colspan': 1
                            })

                    else:  # It's a normal resource
                        if occurrence not in already_seen[resource.id]:
                            already_seen[resource.id].append(occurrence)

                            cell = {
                                'type': 'start',
                                'rowspan': self.get_number_of_slots_for_period(occurrence, date),
                                'occurrence': occurrence,
                                'colspan': 1
                            }

                            cells.append(cell)
                        else:
                            cells.append({
                                'type': 'continue'
                            })

                elif lock is not None:  # No occurrence, maybe a lock ?
                    if lock not in already_seen[resource.id]:
                        already_seen[resource.id].append(lock)

                        cells.append({
                            'type': 'start',
                            'rowspan': self.get_number_of_slots_for_period(lock, date),
                            'lock': lock,
                            'colspan': 2 if resource.is_countable() else 1
                        })

                    else:
                        cells.append({
                            'type': 'continue',
                            'colspan': 2 if resource.is_countable() else 1
                        })
                else:  # There is nothing to display
                    cell = {
                        'type': 'free',
                        'resource': resource,
                        'colspan': 2 if resource.is_countable() else 1
                    }
                    if resource.is_countable():
                        cell['count'] = resource.count_available(slot.start, slot.end)

                    cells.append(cell)

            line['cells'] = cells
            lines.append(line)

        context['lines'] = lines

        return context

    def get_number_of_slots_for_period(self, period, date):
        count = 0
        for slot in self.category.get_slots(date):
            if period.contains_slot(slot):
                count += 1

        return count


class BaseBookingView(ContextMixin):
    booking = None

    def get_context_data(self, **kwargs):
        context = super(BaseBookingView, self).get_context_data(**kwargs)
        page = self.request.GET.get('occ_page', 1)

        occurrences = self.booking.get_occurrences().order_by('start')
        paginator = Paginator(occurrences, 10)

        try:
            occurrences = paginator.page(page)
        except EmptyPage:
            occurrences = paginator.page(paginator.num_pages)

        context['occurrences'] = occurrences
        return context


class BookingCreateView(CreateView):
    model = Booking
    fields = ['contact_first_name', 'contact_last_name', 'contact_email', 'contact_phone', 'contact_asso',
              'reason', 'details']
    template_name = 'bookings/booking_new.html'
    decorators = [login_required, permission_required('bookings.add_booking')]
    start = None
    end = None
    booking = None
    object = None
    resource = None

    def get_form(self, form_class=None):
        form = super(BookingCreateView, self).get_form(form_class=form_class)
        type = self.resource.category.type
        if type == ResourceCategory.ASSO:
            form.fields['contact_asso'].required = True
        elif type == ResourceCategory.STUDENT:
            del form.fields['contact_asso']
        return form

    def get_success_url(self):
        return reverse('bookings:occurrence-new', kwargs={'booking_pk': self.booking.pk}) \
               + '?start=' + str(self.start.isoformat()) \
               + '&end=' + str(self.end.isoformat()) \
               + '&resource=' + str(self.resource.id)

    def dispatch(self, request, *args, **kwargs):
        self.resource = get_object_or_404(Resource, pk=self.request.GET.get('resource'))

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
        context['resource_id'] = self.resource.id

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


class BookingDetailView(DetailView, BaseBookingView):
    model = Booking
    template_name = 'bookings/booking_detail.html'
    booking = None

    def dispatch(self, request, *args, **kwargs):
        self.booking = get_object_or_404(Booking, pk=self.kwargs['pk'])
        return super(BookingDetailView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BookingDetailView, self).get_context_data(**kwargs)
        resource_requires_form = Resource.objects.filter(category__booking_form=True)

        form_needed = BookingOccurrence \
            .objects \
            .filter(booking=self.booking) \
            .filter(resources__in=resource_requires_form) \
            .distinct() \
            .exists()

        if form_needed:
            context['booking_form'] = BookingFormForm(booking=self.booking)

        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return super(BookingDetailView, self).get(request, *args, **kwargs)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        return redirect(to='bookings:booking-form', pk=request.POST.get('occurrence'))


class BookingUpdateView(UpdateView, BaseBookingView):
    model = Booking
    template_name = 'bookings/booking_edit.html'
    fields = ['contact_first_name', 'contact_last_name', 'contact_email', 'contact_phone', 'contact_asso',
              'reason', 'details']
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
        context['initial_resource'] = self.initial_resource

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
            return self.form_valid(form)

        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        occurrence = form.save(commit=False)

        recurrence_type = form.cleaned_data.get('recurrence_type')

        delta = None
        if recurrence_type == BookingOccurrenceForm.DAILY:
            delta = relativedelta(days=1)
        elif recurrence_type == BookingOccurrenceForm.WEEKLY:
            delta = relativedelta(weeks=1)
        elif recurrence_type == BookingOccurrenceForm.BI_WEEKLY:
            delta = relativedelta(weeks=2)
        elif recurrence_type == BookingOccurrenceForm.TRI_WEEKLY:
            delta = relativedelta(weeks=3)
        elif recurrence_type == BookingOccurrenceForm.QUAD_WEEKLY:
            delta = relativedelta(weeks=4)
        elif recurrence_type == BookingOccurrenceForm.MONTHLY:
            delta = relativedelta(months=1)
        elif recurrence_type == BookingOccurrenceForm.YEARLY:
            delta = relativedelta(years=1)

        if not delta:  # If it's not a recurrence
            for resource, count in form.cleaned_data.get('resources').items():
                occurrence.save()
                OccurrenceResourceCount.objects.create(occurrence=occurrence, resource=resource, count=count)
        else:
            recurrence = Recurrence.objects.create()
            occurrence.recurrence = recurrence
            start_time = occurrence.start
            end_time = occurrence.end

            for resource, count in form.cleaned_data.get('resources').items():
                if resource.count_available(start_time, end_time) >= count:
                    if not occurrence.pk:
                        occurrence.save()
                    OccurrenceResourceCount.objects.create(occurrence=occurrence, resource=resource, count=count)

            booking = occurrence.booking
            start_time += delta
            end_time += delta
            recurr_end = form.cleaned_data.get('recurrence_end')

            while start_time.date() <= end_time.date() <= recurr_end:
                occurrence = BookingOccurrence(
                    start=start_time, end=end_time,
                    booking=booking,
                    recurrence=recurrence
                )

                for resource, count in form.cleaned_data.get('resources').items():
                    if resource.count_available(start_time, end_time) >= count:
                        if not occurrence.pk:
                            occurrence.save()
                        OccurrenceResourceCount.objects.create(occurrence=occurrence, resource=resource, count=count)
                        messages.success(
                            self.request,
                            mark_safe(
                                _('Occurrence créée : <a href="{link}" class="alert-link">{occurrence}</a>'.format(
                                    occurrence=escape(str(occurrence)),
                                    link=occurrence.get_absolute_url()
                                ))
                            )
                        )
                    else:
                        occurrences = []
                        locks = []
                        for occurrence in resource.get_occurrences_period(start_time, end_time):
                            if occurrence not in occurrences:
                                occurrences.append(occurrence)

                        for lock in resource.get_locks_period(start_time, end_time):
                            if lock not in locks:
                                locks.append(lock)

                        occurrences.sort()
                        locks.sort()

                        for occurrence in occurrences:
                            if self.request.user.has_perm('bookings.change_bookingoccurrence'):
                                link = occurrence.get_absolute_url()
                            else:
                                link = occurrence.booking.get_absolute_url()

                            messages.warning(
                                self.request,
                                mark_safe(_('Conflit : <a href="{link}" class="alert-link">{conflict}</a>'.format(
                                    conflict=escape(str(occurrence)),
                                    link=link
                                )))
                            )

                        for lock in locks:
                            if self.request.user.has_perm('bookings.change_resourcelock'):
                                messages.warning(
                                    self.request,
                                    mark_safe(_('Conflit : <a href="{link}" class="alert-link">{conflict}</a>'.format(
                                        conflict=escape(str(lock)),
                                        link=lock.get_absolute_url()
                                    )))
                                )
                            else:
                                messages.warning(self.request,_('Conflit : {conflict}'.format(conflict=str(lock))))

                start_time += delta
                end_time += delta

        return HttpResponseRedirect(self.get_success_url())

    @method_decorator(decorators)
    def get(self, request, *args, **kwargs):
        return super(BookingOccurrenceCreateView, self).get(request, *args, **kwargs)


class BookingOccurrenceUpdateView(UpdateView, BaseBookingView):
    model = BookingOccurrence
    form_class = BookingOccurrenceUpdateForm
    template_name = 'bookings/occurrence_edit.html'
    decorators = [login_required, permission_required('bookings.change_bookingoccurrence')]
    booking = None

    def dispatch(self, request, *args, **kwargs):
        self.booking = get_object_or_404(Booking, pk=self.kwargs['booking_pk'])
        return super(BookingOccurrenceUpdateView, self).dispatch(request, *args, **kwargs)

    def get_form(self, *args, form_class=BookingOccurrenceUpdateForm):
        form = form_class(*args, booking_pk=self.booking.id, instance=self.get_object(), initial={
            'recurrence_end': None,
            'recurrence_type': BookingOccurrenceUpdateForm.NONE
        })

        return form

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
        form = self.get_form(request.POST)

        if form.is_valid():
            messages.success(request, _('Occurrence modifiée avec succès'))
            return self.form_valid(form)

        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = occurrence = form.save(commit=False)
        occurrence.save()
        OccurrenceResourceCount.objects.filter(occurrence=occurrence).delete()

        for resource, count in form.cleaned_data.get('resources').items():
            OccurrenceResourceCount.objects.create(occurrence=occurrence, resource=resource, count=count)

        return HttpResponseRedirect(self.get_success_url())


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

    @method_decorator(decorators)
    def post(self, request, *args, **kwargs):
        return super(BookingOccurrenceDeleteView, self).post(request, *args, **kwargs)


class SearchResultsListView(ListView):
    template_name = 'bookings/search.html'
    model = Booking
    query = None
    decorators = [login_required]

    def normalize_query(self, query_string,
                        findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                        normspace=re.compile(r'\s{2,}').sub):
        """ Splits the query string in invidual keywords, getting rid of unecessary spaces
            and grouping quoted words together.
            Example:

            >>> normalize_query('  some random  words "with   quotes  " and   spaces')
            ['some', 'random', 'words', 'with quotes', 'and', 'spaces']

        """
        return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]

    def get_query(self, query_string, search_fields):
        """Returns a query, that is a combination of Q objects. That combination
            aims to search keywords within a model by testing the given search fields.
        """
        query = None  # Query to search for every search term
        terms = self.normalize_query(query_string)
        for term in terms:
            or_query = None  # Query to search for a given term in each field
            for field_name in search_fields:
                q = Q(**{"%s__unaccent__icontains" % field_name: term})
                if or_query is None:
                    or_query = q
                else:
                    or_query |= q
            if query is None:
                query = or_query
            else:
                query &= or_query
        return query

    def dispatch(self, request, *args, **kwargs):
        self.query = self.request.GET.get('query')
        return super(SearchResultsListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.query:
            return Booking.objects \
                .filter(self.get_query(self.request.GET['query'], ['contact_first_name', 'contact_last_name',
                                                                   'contact_email', 'contact_phone', 'contact_asso',
                                                                   'reason', 'details']))
        else:
            return Booking.objects.all()

    def get_context_data(self, **kwargs):
        context = super(SearchResultsListView, self).get_context_data(**kwargs)
        context['query'] = self.query

        return context

    @method_decorator(decorators)
    def get(self, request, *args, **kwargs):
        return super(SearchResultsListView, self).get(request, *args, **kwargs)


class CountableOccurrencesList(ListView):
    template_name = 'bookings/occurrences_filter_list.html'
    model = BookingOccurrence
    filter = None
    context_object_name = 'occurrences_list'

    def dispatch(self, request, *args, **kwargs):
        self.filter = map(int, self.request.GET.get('filter').split(','))
        return super(CountableOccurrencesList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.filter:
            return BookingOccurrence.objects.filter(pk__in=self.filter)
        else:
            return BookingOccurrence.objects.all()


class BookingFormView(DetailView):
    model = BookingOccurrence
    template_name = 'bookings/booking_form.html'
    occurrence = None

    def dispatch(self, request, *args, **kwargs):
        self.occurrence = get_object_or_404(BookingOccurrence, pk=self.kwargs['pk'])
        return super(BookingFormView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BookingFormView, self).get_context_data(**kwargs)

        context['occurrence'] = self.occurrence
        context['booking'] = self.occurrence.booking

        category = self.occurrence.resources.first().category
        context['category'] = category
        context['paragraphs'] = category.paragraphs.filter(order_form__gt=0).order_by('order_form')

        context['total'] = {
            'fee': sum(map(lambda x: x.fee, self.occurrence.bookings.all())),
            'guarantee': sum(map(lambda x: x.guarantee, self.occurrence.bookings.all()))
        }

        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return super(BookingFormView, self).get(request, *args, **kwargs)


def continuous_slots(occurrences, slots, resource_occurrences, found_occurrences):
    found = set()
    for occ in occurrences:
        found_occurrences.add(occ)
        for s in occ.get_slots():
            found.add(s)

    if len(found) > 0 and not found <= slots:
        diff = found - slots
        occs = []
        for s in diff:
            occs += s.get_periods(resource_occurrences)
            slots.add(s)
            slots.update(continuous_slots(occs, slots, resource_occurrences, found_occurrences))

    return slots
