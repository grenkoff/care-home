"""Views open only between the password and the second factor."""

from typing import Any, override

from django.http import HttpRequest, HttpResponseBase
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters

from server.apps.accounts.views.pending import Pending


class PendingOnly(View):
    """View open only to a user who gave the password and not yet the code."""

    @override
    @method_decorator(never_cache)
    @method_decorator(sensitive_post_parameters('code'))
    def dispatch(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponseBase:
        """Leads a visitor who has not given the password to sign in."""
        if not Pending(request).started():
            return redirect('accounts:sign_in')
        return super().dispatch(request, *args, **kwargs)
