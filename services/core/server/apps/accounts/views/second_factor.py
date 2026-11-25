"""Pages of the second factor of signing in: the code of an authenticator app."""

from http import HTTPStatus
from typing import final

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from server.apps.accounts.logic.errors import WrongCodeError
from server.apps.accounts.logic.usecases import connect_authenticator
from server.apps.accounts.models import User
from server.apps.accounts.views.enrolment import Enrolment
from server.apps.accounts.views.forms import CodeForm
from server.apps.accounts.views.pending import Pending, PendingOnly
from server.common.di import HasContainer


@final
class Code(PendingOnly):
    """Page where a user gives the code of the authenticator app."""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Leads a user without an app to connect one."""
        return redirect('accounts:connect')


@final
class Connect(HasContainer, PendingOnly):
    """Page where a user connects an authenticator app after the password."""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Shows the key of a new authenticator app."""
        return self._page(request, Pending(request).user(), CodeForm(), HTTPStatus.OK)

    def post(self, request: HttpRequest) -> HttpResponse:
        """Connects the app of a valid code and signs in, or shows the error."""
        user = Pending(request).user()
        form = CodeForm(request.POST)
        if form.is_valid() and self._connected(request, user, form):
            return Pending(request).signed_in(user)
        return self._page(request, user, form, HTTPStatus.BAD_REQUEST)

    def _connected(self, request: HttpRequest, user: User, form: CodeForm) -> bool:
        """Connects the app of a valid code or marks the code as wrong."""
        try:
            self.resolve(connect_authenticator.ConnectAuthenticator)(
                user.pk,
                Pending(request).key(self.resolve(connect_authenticator.OfferKey)),
                form.cleaned_data['code'],
            )
        except WrongCodeError:
            form.refuse()
            return False
        return True

    def _page(
        self,
        request: HttpRequest,
        user: User,
        form: CodeForm,
        status: HTTPStatus,
    ) -> HttpResponse:
        """Renders the key of the app with the form of the code."""
        key = Pending(request).key(self.resolve(connect_authenticator.OfferKey))
        return render(
            request,
            'accounts/connect.html',
            {
                'key': key,
                'enrolment': Enrolment(key, user.email, settings.SITE_NAME),
                'form': form,
            },
            status=status,
        )
