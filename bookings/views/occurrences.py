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
from bookings.views.bookings import BaseBookingView

log = logging.getLogger(__name__)


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
    object = None

    def dispatch(self, request, *args, **kwargs):
        self.booking = get_object_or_404(Booking, pk=self.kwargs['booking_pk'])
        self.object = get_object_or_404(BookingOccurrence, pk=self.kwargs['pk'])
        return super(BookingOccurrenceUpdateView, self).dispatch(request, *args, **kwargs)

    def get_form(self, *args, form_class=BookingOccurrenceUpdateForm):
        form = form_class(*args, booking_pk=self.booking.id, instance=self.get_object())

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
        context['current_occurrence'] = self.get_object()

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
