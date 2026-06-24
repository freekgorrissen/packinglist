"""Access control for application views."""

from django.contrib.auth.mixins import LoginRequiredMixin


class AppAccessMixin(LoginRequiredMixin):
    """Require a logged-in user for all application views."""

    login_url = 'login'
