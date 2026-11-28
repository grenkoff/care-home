"""Accounts that sign in with a user name or, for staff, with an e-mail."""

from typing import final, override

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest

from server.apps.accounts.models import User


@final
class SignInAccounts(ModelBackend):
    """Accounts found by the user name, and staff found by their e-mail too."""

    @override
    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: object,
    ) -> AbstractBaseUser | None:
        """Returns the account whose name or staff e-mail took the password."""
        return super().authenticate(
            request,
            self._name(username),
            password,
            **kwargs,
        )

    def _name(self, typed: str | None) -> str | None:
        """Returns the user name of staff with the e-mail, or the name typed."""
        return (
            User.objects
            .filter(is_staff=True, email__iexact=typed)
            .values_list('username', flat=True)
            .first()
        ) or typed
