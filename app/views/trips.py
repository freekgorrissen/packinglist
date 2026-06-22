from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from app.forms import TripForm
from app.mixins import AppAccessMixin
from app.models import Trip
from app.services.packing_list import generate_packing_list, group_for_display


class TripListView(AppAccessMixin, ListView):
    model = Trip
    template_name = 'trips/list.html'
    context_object_name = 'trips'


class TripCreateView(AppAccessMixin, CreateView):
    model = Trip
    form_class = TripForm
    template_name = 'trips/form.html'
    success_url = reverse_lazy('trip_list')


class TripUpdateView(AppAccessMixin, UpdateView):
    model = Trip
    form_class = TripForm
    template_name = 'trips/form.html'
    success_url = reverse_lazy('trip_list')


class TripDeleteView(AppAccessMixin, DeleteView):
    model = Trip
    template_name = 'crud/confirm_delete.html'
    success_url = reverse_lazy('trip_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'singular': 'Trip',
                'plural': 'Trips',
                'list_url_name': 'trip_list',
            }
        )
        return context


class TripPackingListView(AppAccessMixin, DetailView):
    model = Trip
    template_name = 'trips/packing_list.html'
    context_object_name = 'trip'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entries = generate_packing_list(self.object)
        context['display_sections'] = group_for_display(entries)
        context['entry_count'] = len(entries)
        return context
