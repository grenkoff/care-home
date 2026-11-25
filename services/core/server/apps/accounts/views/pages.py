"""Pages of accounts rendered on the server."""

from http import HTTPStatus
from typing import final

from django.contrib.auth.forms import SetPasswordForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from server.apps.accounts.logic.errors import UnknownInvitationError
from server.apps.accounts.logic.usecases import accept_invitation
from server.apps.accounts.models import User
from server.apps.accounts.views.forms import RulesForm
from server.common.di import HasContainer


@final
class Accept(HasContainer, View):
    """Page where a relative accepts an invitation."""

    def get(self, request: HttpRequest, code: str) -> HttpResponse:
        """Asks for a password and the rules, or says the link is gone."""
        try:
            email = self.resolve(accept_invitation.OpenInvitation)(code)
        except UnknownInvitationError:
            return self._gone(request)
        return self._page(
            request,
            email,
            SetPasswordForm(User(username=email)),
            RulesForm(),
            HTTPStatus.OK,
        )

    def post(self, request: HttpRequest, code: str) -> HttpResponse:
        """Makes the account and leads to sign in, or shows what is wrong."""
        try:
            return self._accepted(request, code)
        except UnknownInvitationError:
            return self._gone(request)

    def _accepted(self, request: HttpRequest, code: str) -> HttpResponse:
        """Makes the account of valid forms or shows them again with errors."""
        email = self.resolve(accept_invitation.OpenInvitation)(code)
        password = SetPasswordForm(User(username=email), request.POST)
        rules = RulesForm(request.POST)
        if not all([password.is_valid(), rules.is_valid()]):
            return self._page(
                request,
                email,
                password,
                rules,
                HTTPStatus.BAD_REQUEST,
            )
        self.resolve(accept_invitation.AcceptInvitation)(
            code,
            password.cleaned_data['new_password1'],
        )
        return redirect('accounts:sign_in')

    def _page(
        self,
        request: HttpRequest,
        email: str,
        password: SetPasswordForm[User],
        rules: RulesForm,
        status: HTTPStatus,
    ) -> HttpResponse:
        """Renders the invitation with its forms."""
        return render(
            request,
            'accounts/invitation.html',
            {'email': email, 'password': password, 'rules': rules},
            status=status,
        )

    def _gone(self, request: HttpRequest) -> HttpResponse:
        """Renders the page of a link that no longer works."""
        return render(
            request,
            'accounts/invitation_gone.html',
            status=HTTPStatus.NOT_FOUND,
        )
