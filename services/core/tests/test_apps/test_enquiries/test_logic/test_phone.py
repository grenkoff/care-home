"""Tests of the phone numbers that visitors leave to be called back."""

import pytest

from server.apps.enquiries.logic.phone import InvalidPhoneError, Phone


@pytest.mark.parametrize(
    ('typed', 'number'),
    [
        ('+7 (495) 123-45-67', '+7 (495) 123-45-67'),
        ('  8 800 555 35 35 ', '8 800 555 35 35'),
        ('1234567', '1234567'),
        ('123456789012345', '123456789012345'),
    ],
)
def test_phone_keeps_a_number(typed: str, number: str) -> None:
    assert Phone(typed).checked() == number


@pytest.mark.parametrize(
    'typed',
    [
        'call me',
        '12',
        '123456',
        '1234567890123456',
        '+7 495 abc 45 67',
        '7+4951234567',
        '++74951234567',
        '+7\t495\t1234567',
        '',
    ],
)
def test_phone_refuses_what_is_not_a_number(typed: str) -> None:
    with pytest.raises(InvalidPhoneError):
        Phone(typed).checked()
