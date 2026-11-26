"""Tests of the copy of accounts that residents keep from the facts of accounts."""

from typing import Final
from uuid import uuid7

import msgspec
import pytest

from server.apps.accounts.public.events import AccountOpened
from server.apps.residents.infra.accounts import CopiedAccounts
from server.apps.residents.models import Relative
from server.common.outbox.relay import Envelope

_OPENED: Final = AccountOpened(id=uuid7(), account=uuid7(), email='anna@example.test')
_ENVELOPE: Final = Envelope(_OPENED.id, msgspec.to_builtins(_OPENED))


@pytest.mark.django_db
def test_copies_the_opened_account() -> None:
    CopiedAccounts().receive(_ENVELOPE)

    assert list(Relative.objects.values_list('account', 'email')) == [
        (_OPENED.account, _OPENED.email),
    ]


@pytest.mark.django_db
def test_a_second_delivery_keeps_one_copy() -> None:
    CopiedAccounts().receive(_ENVELOPE)
    CopiedAccounts().receive(_ENVELOPE)

    assert Relative.objects.count() == 1


@pytest.mark.django_db
def test_another_fact_of_the_same_account_keeps_one_copy() -> None:
    again = AccountOpened(id=uuid7(), account=_OPENED.account, email=_OPENED.email)
    CopiedAccounts().receive(_ENVELOPE)

    CopiedAccounts().receive(Envelope(again.id, msgspec.to_builtins(again)))

    assert Relative.objects.count() == 1
