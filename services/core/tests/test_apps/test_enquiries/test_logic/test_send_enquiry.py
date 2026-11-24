"""Tests of the use case that takes an enquiry of a visitor."""

from typing import final

import attrs
import pytest

from server.apps.enquiries.logic.enquiries import Enquiry
from server.apps.enquiries.logic.phone import InvalidPhoneError
from server.apps.enquiries.logic.usecases.send_enquiry import SendEnquiry


@final
@attrs.define(slots=True, frozen=True)
class _Kept:
    """Fake: enquiries kept in a list."""

    sent: list[Enquiry] = attrs.field(factory=list)

    def add(self, enquiry: Enquiry) -> None:
        """Keeps the enquiry."""
        self.sent.append(enquiry)


def test_enquiry_keeps_the_checked_phone() -> None:
    kept = _Kept()

    SendEnquiry(kept)(name='Anna', phone=' +7 495 123-45-67 ', message='A visit')

    assert kept.sent == [
        Enquiry(name='Anna', phone='+7 495 123-45-67', message='A visit'),
    ]


def test_enquiry_with_a_wrong_phone_is_not_kept() -> None:
    kept = _Kept()

    with pytest.raises(InvalidPhoneError):
        SendEnquiry(kept)(name='Anna', phone='call me', message='')

    assert not kept.sent
