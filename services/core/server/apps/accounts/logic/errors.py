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


@final
class LockedCodesError(PermissionError):
    """Raised for any code of an app while its codes are locked."""

    __slots__ = ()
