"""Session of a user between the password and the second factor."""

import uuid
from collections.abc import Callable
from typing import Final, final

import attrs
from django.contrib.auth import login, logout
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from server.apps.accounts.logic.constants import CODE_ATTEMPTS
from server.apps.accounts.models import User

_USER: Final = 'accounts.pending.user'
_BACKEND: Final = 'accounts.pending.backend'
_NEXT: Final = 'accounts.pending.next'
_KEY: Final = 'accounts.pending.key'
_FAILURES: Final = 'accounts.pending.failures'
_NAMES: Final = (_USER, _BACKEND, _NEXT, _KEY, _FAILURES)
_LIFETIME: Final = 10 * 60


@final
@attrs.define(slots=True, frozen=True)
class Pending:
    """User who gave the password and has yet to give the second factor."""

    _request: HttpRequest

    def start(self, user: AbstractBaseUser, after: str) -> None:
        """Remembers in a fresh short session who gave the password and what next."""
        session = self._request.session
        session.cycle_key()
        for name in _NAMES:
            session.pop(name, None)
        session.set_expiry(_LIFETIME)
        session[_USER] = str(user.pk)
        session[_BACKEND] = user.backend
        session[_NEXT] = after

    def started(self) -> bool:
        """Tells whether somebody gave the password in this session."""
        return _USER in self._request.session

    def identifier(self) -> uuid.UUID:
        """Returns the id of the user who gave the password."""
        return uuid.UUID(self._request.session[_USER])

    def user(self) -> User:
        """Returns the user who gave the password."""
        return User.objects.get(pk=self.identifier())

    def offered(self, fresh: Callable[[], str]) -> str:
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
        for name in _NAMES:
            session.pop(name, None)
        session.set_expiry(None)
        return redirect(after)

    def failed(self, page: HttpResponse) -> HttpResponse:
        """Counts a wrong code and signs out after too many of them in a row."""
        session = self._request.session
        session[_FAILURES] = session.get(_FAILURES, 0) + 1
        if session[_FAILURES] < CODE_ATTEMPTS:
            return page
        logout(self._request)
        return redirect('accounts:sign_in')
