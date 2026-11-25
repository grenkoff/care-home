"""Pages of the second factor of signing in: the code of an authenticator app."""

from http import HTTPStatus
from typing import final

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from server.apps.accounts.logic.errors import WrongCodeError
from server.apps.accounts.logic.usecases import check_code, connect_authenticator
from server.apps.accounts.views.enrolment import Enrolment
from server.apps.accounts.views.forms import CodeForm
from server.apps.accounts.views.pending import Pending, PendingOnly
from server.common.di import HasContainer


class _Factor(HasContainer, PendingOnly):
    """Page of the second factor that knows whether the user has an app."""

    def _has_app(self, request: HttpRequest) -> bool:
        """Tells whether the user who gave the password connected an app."""
        return self.resolve(connect_authenticator.HasAuthenticator)(
            Pending(request).identifier(),
        )


@final
class Code(_Factor):
    """Page where a user gives the code of the authenticator app."""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Asks for the code, or leads a user without an app to connect one."""
        if not self._has_app(request):
            return redirect('accounts:connect')
        return self._page(request, CodeForm(), HTTPStatus.OK)

    def post(self, request: HttpRequest) -> HttpResponse:
        """Signs in with a valid code, or shows the error."""
        if not self._has_app(request):
            return redirect('accounts:connect')
        pending = Pending(request)
        form = CodeForm(request.POST)
        if form.is_valid() and self._checked(pending, form):
            return pending.signed_in(pending.user())
        return pending.failed(self._page(request, form, HTTPStatus.BAD_REQUEST))

    def _checked(self, pending: Pending, form: CodeForm) -> bool:
        """Checks a code or marks it as wrong."""
        try:
            self.resolve(check_code.CheckCode)(
                pending.identifier(),
                form.cleaned_data['code'],
            )
        except WrongCodeError:
            form.refuse()
            return False
        return True

    def _page(
        self,
        request: HttpRequest,
        form: CodeForm,
        status: HTTPStatus,
    ) -> HttpResponse:
        """Renders the form of the code."""
        return render(request, 'accounts/code.html', {'form': form}, status=status)


@final
class Connect(_Factor):
    """Page where a user connects an authenticator app after the password."""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Shows the key of a new authenticator app."""
        if self._has_app(request):
            return redirect('accounts:code')
        return self._page(request, CodeForm(), HTTPStatus.OK)

    def post(self, request: HttpRequest) -> HttpResponse:
        """Connects the app of a valid code and signs in, or shows the error."""
        if self._has_app(request):
            return redirect('accounts:code')
        pending = Pending(request)
        form = CodeForm(request.POST)
        if form.is_valid() and self._connected(pending, form):
            return pending.signed_in(pending.user())
        return pending.failed(self._page(request, form, HTTPStatus.BAD_REQUEST))

    def _connected(self, pending: Pending, form: CodeForm) -> bool:
        """Connects the app of a valid code or marks the code as wrong."""
        try:
            self.resolve(connect_authenticator.ConnectAuthenticator)(
                pending.identifier(),
                pending.key(self.resolve(connect_authenticator.OfferKey)),
                form.cleaned_data['code'],
            )
        except WrongCodeError:
            form.refuse()
            return False
        return True

    def _page(
        self,
        request: HttpRequest,
        form: CodeForm,
        status: HTTPStatus,
    ) -> HttpResponse:
        """Renders the key of the app with the form of the code."""
        pending = Pending(request)
        key = pending.key(self.resolve(connect_authenticator.OfferKey))
        return render(
            request,
            'accounts/connect.html',
            {
                'key': key,
                'enrolment': Enrolment(key, pending.user().email, settings.SITE_NAME),
                'form': form,
            },
            status=status,
        )
