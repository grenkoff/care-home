"""Errors of the residents and their relatives."""

from typing import final


@final
class UnknownRelativeError(LookupError):
    """Raised for an e-mail of a relative that has no account."""

    __slots__ = ()
