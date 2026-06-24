from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import redirect
from django.views.generic import TemplateView

from app.forms import StyledPasswordChangeForm
from app.mixins import AppAccessMixin


class ProfileView(AppAccessMixin, TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['password_form'] = StyledPasswordChangeForm(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        password_form = StyledPasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            password_form.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password updated.')
            return redirect('profile')
        return self.render_to_response({
            **self.get_context_data(),
            'password_form': password_form,
        })
