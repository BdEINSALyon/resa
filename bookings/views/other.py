import calendar
import datetime as dt
import logging
import re
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView

from bookings.models import ResourceCategory, Resource, Booking, BookingOccurrence

log = logging.getLogger(__name__)


class ResourceCategoryDayView(ListView):
    template_name = 'bookings/resource/resource_category_day.html'
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
        day, month, year = self._extract_date()
        date = dt.date(day=day, month=month, year=year)
        context['date'] = date

        context['today'] = dt.date.today()

        # Month calendar
        weeks = self._construct_month_calendar(month, year)
        context['weeks'] = weeks

        # Booking occurrences
        resources = self.get_queryset()
        locks, occurrences = self._find_matching_occurrences_and_locks(day, month, resources, year)

        lines = self._construct_day_view(date, locks, occurrences, resources)

        context['lines'] = lines

        return context

    def _construct_day_view(self, date, locks, occurrences, resources):
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

                            cells.append({
                                'type': 'start',
                                'rowspan': self.get_number_of_slots_for_period(occurrence, date),
                                'occurrence': occurrence,
                                'colspan': 1
                            })

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
        return lines

    @staticmethod
    def _find_matching_occurrences_and_locks(day, month, resources, year):
        occurrences = {}
        locks = {}
        for resource in resources:
            occurrences[resource.id] = []
            locks[resource.id] = []
            for occurrence in resource.get_occurrences(year=year, month=month, day=day):
                occurrences[resource.id].append(occurrence)

            for lock in resource.get_locks(year, month, day):
                locks[resource.id].append(lock)
        return locks, occurrences

    @staticmethod
    def _construct_month_calendar(month, year):
        cal = calendar.Calendar()
        days_in_month = cal.itermonthdates(year, month)
        weeks = []
        week_index = 0
        for month_day in days_in_month:
            weeks.append([])
            weeks[week_index].append(month_day)
            if month_day.weekday() == 6:
                week_index += 1
        return weeks

    def _extract_date(self):
        day = int(self.request.GET.get('day', dt.date.today().day))
        month = int(self.request.GET.get('month', dt.date.today().month))
        year = int(self.request.GET.get('year', dt.date.today().year))
        while month > 12:
            year += 1
            month -= 12
        return day, month, year

    def get_number_of_slots_for_period(self, period, date):
        count = 0
        for slot in self.category.get_slots(date):
            if period.contains_slot(slot):
                count += 1

        return count


class SearchResultsListView(ListView):
    template_name = 'bookings/search.html'
    model = Booking
    query = None
    decorators = [login_required]

    @staticmethod
    def normalize_query(query_string,
                        findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                        normspace=re.compile(r'\s{2,}').sub):
        """ Splits the query string in invidual keywords, getting rid of unecessary spaces
            and grouping quoted words together.
            Example:

            >>> SearchResultsListView.normalize_query('  some random  words "with   quotes  " and   spaces')
            ['some', 'random', 'words', 'with quotes', 'and', 'spaces']

        """
        return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]

    @staticmethod
    def get_query(query_string, search_fields):
        """Returns a query, that is a combination of Q objects. That combination
            aims to search keywords within a model by testing the given search fields.
        """
        query = None  # Query to search for every search term
        terms = SearchResultsListView.normalize_query(query_string)
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
    template_name = 'bookings/occurrence/occurrences_filter_list.html'
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
    template_name = 'bookings/booking/booking_form.html'
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
