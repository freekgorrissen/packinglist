from itertools import groupby

from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.forms import FAMILY_MEMBERS_REQUIRED_TEXT, PackingItemForm, PackingSectionForm
from app.mixins import AppAccessMixin
from app.models import FamilyMember, MemberType, PackingItem, PackingSection
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section_groups'] = [
            {'section': section, 'items': list(items)}
            for section, items in groupby(context['items'], key=lambda item: item.section)
        ]
        return context


class PackingItemFormMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['family_members_required_text'] = FAMILY_MEMBERS_REQUIRED_TEXT
        ids_by_type = {
            member_type.value: list(
                FamilyMember.objects.filter(member_type=member_type.value).values_list('pk', flat=True)
            )
            for member_type in MemberType
        }
        ids_by_type['humans'] = list(
            FamilyMember.objects.exclude(member_type=MemberType.PET).values_list('pk', flat=True)
        )
        context['family_member_ids_by_type'] = ids_by_type
        return context


class PackingItemCreateView(AppAccessMixin, PackingItemFormMixin, CreateView):
    model = PackingItem
    form_class = PackingItemForm
    template_name = 'packing/item_form.html'
    success_url = reverse_lazy('item_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['batch_add_checked'] = 'batch_add' in self.request.POST
            context['batch_names'] = self.request.POST.getlist('batch_names')
        else:
            context['batch_add_checked'] = False
            context['batch_names'] = []
        return context

    def form_valid(self, form):
        if form.batch_add:
            for name in form.batch_names:
                form.save_new_item(name)
            if 'save_and_add' in self.request.POST:
                return redirect('item_create')
            return redirect(self.success_url)

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
