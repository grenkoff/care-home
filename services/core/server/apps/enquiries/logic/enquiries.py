"""Enquiries of visitors who want a place or a visit."""

from typing import Protocol, final

import attrs


@final
@attrs.define(slots=True, frozen=True, kw_only=True)
class Enquiry:
    """Request of a visitor to be called back."""

    name: str
    phone: str
    message: str


class Enquiries(Protocol):
    """Enquiries that staff read."""

    def add(self, enquiry: Enquiry) -> None:
        """Keeps the enquiry for staff."""
