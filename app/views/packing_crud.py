from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.forms import CATEGORY_HELPER_TEXT, PackingItemForm, PackingSectionForm
from app.mixins import AppAccessMixin
from app.models import PackingItem, PackingSection
from app.views.crud_factory import CrudConfig, make_create_view, make_delete_view, make_list_view, make_update_view

SECTION_CONFIG = CrudConfig(
    model=PackingSection,
    form_class=PackingSectionForm,
    list_url_name='section_list',
    create_url_name='section_create',
    update_url_name='section_update',
    delete_url_name='section_delete',
    singular='Packing Section',
    plural='Packing Sections',
)

SectionListView = make_list_view(SECTION_CONFIG)
SectionCreateView = make_create_view(SECTION_CONFIG)
SectionUpdateView = make_update_view(SECTION_CONFIG)
SectionDeleteView = make_delete_view(SECTION_CONFIG)


class PackingItemListView(AppAccessMixin, ListView):
    model = PackingItem
    template_name = 'packing/item_list.html'
    context_object_name = 'items'

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related('section')
            .prefetch_related(
                'destinations',
                'activities',
                'accommodations',
                'family_members',
            )
        )


class PackingItemFormMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_helper_text'] = CATEGORY_HELPER_TEXT
        return context


class PackingItemCreateView(AppAccessMixin, PackingItemFormMixin, CreateView):
    model = PackingItem
    form_class = PackingItemForm
    template_name = 'packing/item_form.html'
    success_url = reverse_lazy('item_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        if 'save_and_add' in self.request.POST:
            return redirect('item_create')
        return response


class PackingItemUpdateView(AppAccessMixin, PackingItemFormMixin, UpdateView):
    model = PackingItem
    form_class = PackingItemForm
    template_name = 'packing/item_form.html'
    success_url = reverse_lazy('item_list')


class PackingItemDeleteView(AppAccessMixin, DeleteView):
    model = PackingItem
    template_name = 'crud/confirm_delete.html'
    success_url = reverse_lazy('item_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'singular': 'Packing Item',
                'plural': 'Packing Items',
                'list_url_name': 'item_list',
            }
        )
        return context
