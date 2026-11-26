"""Tests of the outbox that keeps facts in the transaction of their change."""

from typing import final
from uuid import UUID, uuid7

import msgspec
import pytest

from server.common.outbox.outbox import OutsideTransactionError, StoredOutbox


@final
class _Happened(msgspec.Struct, frozen=True):
    """Fact of the tests with nothing but its id."""

    id: UUID


@pytest.mark.django_db(transaction=True)
def test_refuses_a_fact_outside_a_transaction() -> None:
    with pytest.raises(OutsideTransactionError):
        StoredOutbox().add('tests.v1.happened', _Happened(id=uuid7()))
