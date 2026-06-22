from django.views.generic import TemplateView

from app.mixins import AppAccessMixin


class HomeView(AppAccessMixin, TemplateView):
    template_name = 'home.html'
