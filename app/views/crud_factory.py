from dataclasses import dataclass

from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.mixins import AppAccessMixin


@dataclass(frozen=True)
class CrudConfig:
    model: type
    form_class: type
    list_url_name: str
    create_url_name: str
    update_url_name: str
    delete_url_name: str
    singular: str
    plural: str


def make_list_view(config: CrudConfig):
    class View(AppAccessMixin, ListView):
        model = config.model
        template_name = 'crud/list.html'
        context_object_name = 'objects'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context.update(
                {
                    'singular': config.singular,
                    'plural': config.plural,
                    'create_url_name': config.create_url_name,
                    'update_url_name': config.update_url_name,
                    'delete_url_name': config.delete_url_name,
                }
            )
            return context

    return View


def make_create_view(config: CrudConfig):
    class View(AppAccessMixin, CreateView):
        model = config.model
        form_class = config.form_class
        template_name = 'crud/form.html'
        success_url = reverse_lazy(config.list_url_name)

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context.update(
                {
                    'singular': config.singular,
                    'plural': config.plural,
                    'list_url_name': config.list_url_name,
                }
            )
            return context

    return View


def make_update_view(config: CrudConfig):
    class View(AppAccessMixin, UpdateView):
        model = config.model
        form_class = config.form_class
        template_name = 'crud/form.html'
        success_url = reverse_lazy(config.list_url_name)

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context.update(
                {
                    'singular': config.singular,
                    'plural': config.plural,
                    'list_url_name': config.list_url_name,
                }
            )
            return context

    return View


def make_delete_view(config: CrudConfig):
    class View(AppAccessMixin, DeleteView):
        model = config.model
        template_name = 'crud/confirm_delete.html'
        success_url = reverse_lazy(config.list_url_name)

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context.update(
                {
                    'singular': config.singular,
                    'plural': config.plural,
                    'list_url_name': config.list_url_name,
                }
            )
            return context

    return View
