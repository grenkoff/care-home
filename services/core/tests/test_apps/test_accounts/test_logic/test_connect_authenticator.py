"""Tests of the use cases that connect an authenticator app."""

import uuid
from datetime import UTC, datetime
from typing import Final, final

import attrs
import pytest

from server.apps.accounts.logic.codes import Key
from server.apps.accounts.logic.errors import WrongCodeError
from server.apps.accounts.logic.usecases.connect_authenticator import (
    ConnectAuthenticator,
    HasAuthenticator,
    OfferKey,
)

_KEY: Final = 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'
_USER: Final = uuid.UUID(int=1)


@final
@attrs.define(slots=True, frozen=True)
class _Stopped:
    """Fake: a clock that always shows the same moment."""

    _seconds: int

    def now(self) -> datetime:
        """Returns the moment."""
        return datetime.fromtimestamp(self._seconds, tz=UTC)


@final
@attrs.define(slots=True, frozen=True)
class _Same:
    """Fake: keys that are always the same."""

    def fresh(self) -> str:
        """Returns the key."""
        return _KEY


@final
@attrs.define(slots=True, frozen=True)
class _Kept:
    """Fake: authenticators kept in a list."""

    keys: list[tuple[uuid.UUID, str, int]] = attrs.field(factory=list)

    def connected(self, user: uuid.UUID) -> bool:
        """Tells whether the user has a key in the list."""
        return any(kept == user for kept, _, _ in self.keys)

    def connect(self, user: uuid.UUID, key: str, step: int) -> None:
        """Keeps the user, the key and the step."""
        self.keys.append((user, key, step))


def test_key_comes_from_its_source() -> None:
    assert OfferKey(_Same())() == _KEY


@pytest.mark.parametrize(('seconds', 'step'), [(0, 0), (59, 1)])
def test_valid_code_connects_with_its_step(seconds: int, step: int) -> None:
    kept = _Kept()
    code = Key(_KEY).code(step)

    ConnectAuthenticator(kept, _Stopped(seconds))(_USER, _KEY, code)

    assert kept.keys == [(_USER, _KEY, step)]


def test_wrong_code_connects_nothing() -> None:
    kept = _Kept()
    code = Key(_KEY).code(9)

    with pytest.raises(WrongCodeError):
        ConnectAuthenticator(kept, _Stopped(59))(_USER, _KEY, code)

    assert not kept.keys


def test_user_has_an_authenticator_once_connected() -> None:
    kept = _Kept()
    before = HasAuthenticator(kept)(_USER)

    kept.connect(_USER, _KEY, 1)

    assert (before, HasAuthenticator(kept)(_USER)) == (False, True)
