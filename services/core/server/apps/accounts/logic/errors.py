"""Errors of the accounts of relatives."""

from typing import final


@final
class UnknownInvitationError(LookupError):
    """Raised for a link that is unknown, already used or expired."""

    __slots__ = ()


@final
class TakenEmailError(ValueError):
    """Raised for an invitation to an e-mail that already has an account."""

    __slots__ = ()


@final
class WrongCodeError(ValueError):
    """Raised for a code of an authenticator that is wrong, stale or used."""

    __slots__ = ()
