"""Tests of the pages of the site in a real browser."""

import os
from collections.abc import Iterator
from typing import Final

import pytest
from playwright.sync_api import Browser, Page, Playwright, expect, sync_playwright

_CORE: Final = os.environ.get('CORE_URL', 'http://localhost:8000')


@pytest.fixture(scope='module')
def playwright() -> Iterator[Playwright]:
    """Starts Playwright for the tests of the module."""
    with sync_playwright() as started:
        yield started


@pytest.fixture(scope='module')
def browser(playwright: Playwright) -> Iterator[Browser]:
    """Launches Chromium without a window."""
    launched = playwright.chromium.launch()
    yield launched
    launched.close()


@pytest.fixture
def page(browser: Browser) -> Iterator[Page]:
    """Opens a page in a fresh context, with empty storage."""
    context = browser.new_context(base_url=_CORE)
    yield context.new_page()
    context.close()


def test_language_form_switches_the_page(page: Page) -> None:
    page.goto('/ru/contacts/')

    page.get_by_label('Язык').select_option('en')
    page.get_by_role('button', name='Сменить').click()

    expect(page).to_have_url(f'{_CORE}/en/contacts/')
    expect(page.locator('html')).to_have_attribute('lang', 'en')
