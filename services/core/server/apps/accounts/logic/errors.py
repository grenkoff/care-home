"""Errors of the invitations of relatives."""

from typing import final


@final
class UnknownInvitationError(LookupError):
    """Raised for a link that is unknown, already used or expired."""

    __slots__ = ()


@final
class TakenEmailError(ValueError):
    """Raised for an invitation to an e-mail that already has an account."""

    __slots__ = ()
