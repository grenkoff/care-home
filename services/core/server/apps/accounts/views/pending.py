"""Session of a user between the password and the second factor."""

from collections.abc import Callable
from typing import Any, Final, final, override

import attrs
from django.contrib.auth import login
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.shortcuts import redirect
from django.views import View

from server.apps.accounts.models import User

_USER: Final = 'accounts.pending.user'
_BACKEND: Final = 'accounts.pending.backend'
_NEXT: Final = 'accounts.pending.next'
_KEY: Final = 'accounts.pending.key'


@final
@attrs.define(slots=True, frozen=True)
class Pending:
    """User who gave the password and has yet to give the second factor."""

    _request: HttpRequest

    def start(self, user: AbstractBaseUser, after: str) -> None:
        """Remembers who gave the password and where to lead after the code."""
        session = self._request.session
        session[_USER] = str(user.pk)
        session[_BACKEND] = user.backend
        session[_NEXT] = after

    def started(self) -> bool:
        """Tells whether somebody gave the password in this session."""
        return _USER in self._request.session

    def user(self) -> User:
        """Returns the user who gave the password."""
        return User.objects.get(pk=self._request.session[_USER])

    def key(self, fresh: Callable[[], str]) -> str:
        """Returns the key of the app being connected, made once per session."""
        session = self._request.session
        if _KEY not in session:
            session[_KEY] = fresh()
        return str(session[_KEY])

    def signed_in(self, user: User) -> HttpResponse:
        """Signs the user in and leads where the password page was asked to."""
        session = self._request.session
        after = session[_NEXT]
        login(self._request, user, session[_BACKEND])
        for name in (_USER, _BACKEND, _NEXT, _KEY):
            session.pop(name, None)
        return redirect(after)


class PendingOnly(View):
    """View open only to a user who gave the password and not yet the code."""

    @override
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
