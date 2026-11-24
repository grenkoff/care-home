"""Tests of the page that says which data the site keeps."""

import pytest
from django.test import Client


@pytest.mark.parametrize(
    ('language', 'phrase'),
    [
        ('en', 'Video from the cameras is never stored'),
        ('en', 'the name and phone number from an enquiry'),
        ('ru', 'никогда не сохраняется'),
    ],
)
def test_privacy_page_says_what_is_kept(
    client: Client,
    language: str,
    phrase: str,
) -> None:
    page = client.get(f'/{language}/privacy/').content.decode()

    assert phrase in page
