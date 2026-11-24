"""Use case that takes an enquiry of a visitor."""

from __future__ import annotations

from typing import TYPE_CHECKING, final

import attrs

from server.apps.enquiries.logic.enquiries import Enquiry
from server.apps.enquiries.logic.phone import Phone

if TYPE_CHECKING:
    from server.apps.enquiries.logic.enquiries import Enquiries


@final
@attrs.define(slots=True, frozen=True)
class SendEnquiry:
    """Keeps the enquiry of a visitor for staff to call back."""

    _enquiries: Enquiries

    def __call__(self, *, name: str, phone: str, message: str) -> None:
        """Keeps the enquiry or raises InvalidPhoneError for a wrong phone."""
        self._enquiries.add(
            Enquiry(name=name, phone=Phone(phone).checked(), message=message),
        )
