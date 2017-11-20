import datetime as dt
import logging

import dateutil.parser
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django.views.generic.base import ContextMixin

from bookings.adhesion import AdhesionAPI
from bookings.forms import BookingFormForm
from bookings.models import ResourceCategory, Resource, Booking, BookingOccurrence

log = logging.getLogger(__name__)


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
    template_name = 'bookings/booking/booking_new.html'
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
    template_name = 'bookings/booking/booking_detail.html'
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
    template_name = 'bookings/booking/booking_edit.html'
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
    template_name = 'bookings/booking/booking_delete.html'

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

