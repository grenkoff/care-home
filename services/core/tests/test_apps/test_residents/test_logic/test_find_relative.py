"""Tests of finding the account of a relative by e-mail."""

import uuid
from typing import Final, final

import attrs
import pytest

from server.apps.residents.logic.errors import UnknownRelativeError
from server.apps.residents.logic.usecases.find_relative import FindRelative

_ANNA: Final = uuid.UUID('01900000-0000-7000-8000-000000000001')


@final
@attrs.define(slots=True, frozen=True)
class _Known:
    """Relatives among whom only Anna has an account."""

    def identified(self, email: str) -> uuid.UUID:
        """Returns the id of Anna or refuses any other e-mail."""
        if email != 'anna@example.test':
            raise UnknownRelativeError
        return _ANNA


def test_finds_the_account_of_a_relative() -> None:
    assert FindRelative(_Known())('anna@example.test') == _ANNA


def test_refuses_an_email_without_an_account() -> None:
    with pytest.raises(UnknownRelativeError):
        FindRelative(_Known())('boris@example.test')
