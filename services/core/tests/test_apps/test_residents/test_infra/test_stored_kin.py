"""Tests of the facade that tells relatives of residents in the home."""

import datetime as dt
from typing import Final

import pytest
from django.utils import timezone

from server.apps.accounts.models import User
from server.apps.residents.infra.kin import StoredKin
from server.apps.residents.models import Kinship, Resident

_MOVED_OUT: Final = dt.date(2026, 3, 1)


@pytest.mark.django_db
def test_a_working_link_relates_the_account(kinship: Kinship, relative: User) -> None:
    assert StoredKin().related(relative.pk)


@pytest.mark.django_db
def test_an_account_without_links_is_not_related(kinship: Kinship) -> None:
    stranger = User.objects.create_user(username='boris@example.test')

    assert not StoredKin().related(stranger.pk)


@pytest.mark.django_db
def test_a_revoked_link_does_not_relate(kinship: Kinship, relative: User) -> None:
    Kinship.objects.filter(pk=kinship.pk).update(revoked_at=timezone.now())

    assert not StoredKin().related(relative.pk)


@pytest.mark.django_db
def test_a_resident_who_moved_out_does_not_relate(
    kinship: Kinship,
    resident: Resident,
    relative: User,
) -> None:
    Resident.objects.filter(pk=resident.pk).update(moved_out_on=_MOVED_OUT)

    assert not StoredKin().related(relative.pk)
