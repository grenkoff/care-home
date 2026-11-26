"""Tests of the relatives found in the copy of accounts that residents keep."""

from uuid import uuid7

import pytest

from server.apps.residents.infra.relatives import CopiedRelatives
from server.apps.residents.logic.errors import UnknownRelativeError
from server.apps.residents.models import Relative


@pytest.mark.django_db
def test_finds_the_relative_regardless_of_case() -> None:
    copied = Relative.objects.create(account=uuid7(), email='anna@example.test')

    assert CopiedRelatives().identified('Anna@Example.test') == copied.account


@pytest.mark.django_db
def test_refuses_an_email_that_was_not_copied() -> None:
    with pytest.raises(UnknownRelativeError):
        CopiedRelatives().identified('boris@example.test')
