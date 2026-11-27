"""Tests of the pages of the site in a real browser."""

import os
from collections.abc import Iterator
from typing import Final

import pytest
from playwright.sync_api import Browser, Page, Playwright, expect, sync_playwright

_CORE: Final = os.environ.get('CORE_URL', 'http://localhost:8000')
_STAFF_SESSION: Final = os.environ.get('STAFF_SESSION', '')
_HOME: Final = '/ru/'
_THEME: Final = 'Тема'


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


@pytest.fixture
def staff(browser: Browser) -> Iterator[Page]:
    """Opens a page for staff and puts back the theme of the site they found."""
    context = browser.new_context(base_url=_CORE)
    context.add_cookies([{'name': 'sessionid', 'value': _STAFF_SESSION, 'url': _CORE}])
    signed_in = context.new_page()
    signed_in.goto(_HOME)
    found = signed_in.locator('html').get_attribute('data-theme') or 'warm'
    yield signed_in
    signed_in.goto(_HOME)
    signed_in.get_by_label(_THEME).select_option(found)
    expect(signed_in.locator('html')).to_have_attribute('data-theme', found)
    context.close()


def test_language_switches_as_soon_as_it_is_chosen(page: Page) -> None:
    page.goto('/ru/contacts/')

    page.get_by_label('Язык').select_option('en')

    expect(page).to_have_url(f'{_CORE}/en/contacts/')
    expect(page.locator('html')).to_have_attribute('lang', 'en')


def test_staff_choice_restyles_the_site_at_once(staff: Page) -> None:
    staff.get_by_label(_THEME).select_option('bold')

    expect(staff.locator('html')).to_have_attribute('data-theme', 'bold')


def test_visitors_see_the_theme_staff_chose(staff: Page, page: Page) -> None:
    staff.get_by_label(_THEME).select_option('classic')
    expect(staff.locator('html')).to_have_attribute('data-theme', 'classic')

    page.goto(_HOME)

    expect(page.locator('html')).to_have_attribute('data-theme', 'classic')
