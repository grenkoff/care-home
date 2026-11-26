"""Errors of cameras."""

from typing import final


@final
class NotAdmittedError(PermissionError):
    """Raised for a viewer who has no working link to a resident in the home."""

    __slots__ = ()


@final
class UnknownCameraError(LookupError):
    """Raised for a camera that does not exist or is not active."""

    __slots__ = ()
