"""Tests of the relatives found through the accounts module."""

import uuid
from typing import Final, final

import attrs
import pytest

from server.apps.accounts.public.accounts import UnknownAccountError
from server.apps.residents.infra.relatives import AccountRelatives
from server.apps.residents.logic.errors import UnknownRelativeError

_ANNA: Final = uuid.UUID('01900000-0000-7000-8000-000000000001')


@final
@attrs.define(slots=True, frozen=True)
class _Accounts:
    """Accounts among which only Anna has one."""

    def identified(self, email: str) -> uuid.UUID:
        """Returns the id of Anna or refuses any other e-mail."""
        if email != 'anna@example.test':
            raise UnknownAccountError
        return _ANNA


def test_finds_the_relative_through_accounts() -> None:
    assert AccountRelatives(_Accounts()).identified('anna@example.test') == _ANNA


def test_translates_an_unknown_account() -> None:
    with pytest.raises(UnknownRelativeError):
        AccountRelatives(_Accounts()).identified('boris@example.test')
