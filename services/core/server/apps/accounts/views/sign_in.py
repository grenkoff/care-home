"""Page of the password, the first of the two factors of signing in."""

from typing import final, override

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.shortcuts import redirect

from server.apps.accounts.views.pending import Pending


@final
class SignIn(LoginView):
    """Page of the password, the first of the two factors."""

    @override
    def form_valid(self, form: AuthenticationForm) -> HttpResponse:
        """Remembers who gave the password and asks for the second factor."""
        Pending(self.request).start(form.get_user(), self.get_success_url())
        return redirect('accounts:code')
