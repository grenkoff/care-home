"""Use cases that connect an authenticator app as the second factor."""

import uuid
from typing import Final, final

import attrs

from server.apps.accounts.logic.authenticators import Authenticators, Keys
from server.apps.accounts.logic.codes import Authenticator, Key
from server.apps.accounts.logic.invitations import Clock

_NEVER: Final = -1


@final
@attrs.define(slots=True, frozen=True)
class OfferKey:
    """Offers the key of a new authenticator app."""

    _keys: Keys

    def __call__(self) -> str:
        """Returns a fresh key."""
        return self._keys.fresh()


@final
@attrs.define(slots=True, frozen=True)
class HasAuthenticator:
    """Tells whether a user connected an authenticator app."""

    _authenticators: Authenticators

    def __call__(self, user: uuid.UUID) -> bool:
        """Returns whether the app of the user is connected."""
        return self._authenticators.connected(user)


@final
@attrs.define(slots=True, frozen=True)
class ConnectAuthenticator:
    """Connects the authenticator app whose code proves that it has the key."""

    _authenticators: Authenticators
    _clock: Clock

    def __call__(self, user: uuid.UUID, key: str, code: str) -> None:
        """Keeps the key of a valid code or raises WrongCodeError."""
        moment = self._clock.now()
        step = Authenticator(Key(key), _NEVER).accepted(code, moment)
        self._authenticators.connect(user, key, step)
