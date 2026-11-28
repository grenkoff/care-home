"""Accounts that sign in: relatives by an e-mail, staff by a name or an e-mail."""

from typing import Final, final, override

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest

from server.apps.accounts.models import User

_EMAIL_SIGN: Final = '@'


@final
class SignInAccounts(ModelBackend):
    """Accounts found by name or staff e-mail; others need an e-mail name."""

    @override
    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: object,
    ) -> User | None:
        """Returns the account whose name or staff e-mail took the password."""
        return super().authenticate(
            request,
            self._name(username),
            password,
            **kwargs,
        )

    @override
    def user_can_authenticate(self, user: User | AnonymousUser | None) -> bool:
        """Lets in active staff and active accounts named by an e-mail."""
        return super().user_can_authenticate(user) and bool(
            user and (user.is_staff or _EMAIL_SIGN in user.get_username()),
        )

    def _name(self, typed: str | None) -> str | None:
        """Returns the user name of the one staff with the e-mail, or the name."""
        if not typed or _EMAIL_SIGN not in typed:
            return typed
        staff = User.objects.filter(is_staff=True, email__iexact=typed)
        match list(staff.values_list('username')):
            case [(name,)]:
                return name
            case _:
                return typed
