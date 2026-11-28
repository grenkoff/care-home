"""Pages of the second factor of signing in: the code of an authenticator app."""

from collections.abc import Callable
from http import HTTPStatus
from typing import final

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render

from server.apps.accounts.logic.errors import LockedCodesError, WrongCodeError
from server.apps.accounts.logic.usecases import check_code, connect_authenticator
from server.apps.accounts.views import enrolment, forms
from server.apps.accounts.views.pending import Pending
from server.apps.accounts.views.pending_only import PendingOnly
from server.common.di import HasContainer

type _Check = Callable[[Pending, str], None]
type _Page = Callable[[HttpRequest, forms.CodeForm, HTTPStatus], HttpResponse]


class _Factor(HasContainer, PendingOnly):
    """Page of the second factor that knows whether the user has an app."""

    def _has_app(self, request: HttpRequest) -> bool:
        """Tells whether the user who gave the password connected an app."""
        return self.resolve(connect_authenticator.HasAuthenticator)(
            Pending(request).identifier(),
        )

    def _answer(self, request: HttpRequest, check: _Check, page: _Page) -> HttpResponse:
        """Signs in with a valid code, or shows the page again with the error."""
        pending = Pending(request)
        form = forms.CodeForm(request.POST)
        if form.is_valid() and self._proved(pending, form, check):
            return pending.signed_in(pending.user())
        return pending.failed(page(request, form, HTTPStatus.BAD_REQUEST))

    def _proved(self, pending: Pending, form: forms.CodeForm, check: _Check) -> bool:
        """Checks the code of a valid form or marks the code as wrong."""
        try:
            check(pending, form.cleaned_data['code'])
        except WrongCodeError:
            form.refuse()
            return False
        except LockedCodesError:
            form.lock()
            return False
        return True


@final
class Code(_Factor):
    """Page where a user gives the code of the authenticator app."""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Asks for the code, or leads a user without an app to connect one."""
        if not self._has_app(request):
            return redirect('accounts:connect')
        return self._page(request, forms.CodeForm(), HTTPStatus.OK)

    def post(self, request: HttpRequest) -> HttpResponse:
        """Signs in with a valid code, or shows the error."""
        if not self._has_app(request):
            return redirect('accounts:connect')
        checked = self.resolve(check_code.CheckCode)
        return self._answer(
            request,
            lambda pending, code: checked(pending.identifier(), code),
            self._page,
        )

    def _page(
        self,
        request: HttpRequest,
        form: forms.CodeForm,
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
        return self._page(request, forms.CodeForm(), HTTPStatus.OK)

    def post(self, request: HttpRequest) -> HttpResponse:
        """Connects the app of a valid code and signs in, or shows the error."""
        if self._has_app(request):
            return redirect('accounts:code')
        connected = self.resolve(connect_authenticator.ConnectAuthenticator)
        offered = self.resolve(connect_authenticator.OfferKey)
        return self._answer(
            request,
            lambda pending, code: connected(
                pending.identifier(),
                pending.offered(offered),
                code,
            ),
            self._page,
        )

    def _page(
        self,
        request: HttpRequest,
        form: forms.CodeForm,
        status: HTTPStatus,
    ) -> HttpResponse:
        """Renders the key of the app with the form of the code."""
        pending = Pending(request)
        user = pending.user()
        key = pending.offered(self.resolve(connect_authenticator.OfferKey))
        offer = enrolment.Enrolment(key, user.get_username(), settings.SITE_NAME)
        return render(
            request,
            'accounts/connect.html',
            {
                'key': key,
                'link': offer.link(),
                'picture': offer.picture(),
                'form': form,
                'later': user.is_staff,
            },
            status=status,
        )


@final
class Later(_Factor):
    """Button that lets staff sign in now and connect the app another time."""

    def post(self, request: HttpRequest) -> HttpResponse:
        """Signs staff in with the password alone and refuses everybody else."""
        pending = Pending(request)
        user = pending.user()
        if not user.is_staff:
            return HttpResponseForbidden()
        return pending.signed_in(user)
