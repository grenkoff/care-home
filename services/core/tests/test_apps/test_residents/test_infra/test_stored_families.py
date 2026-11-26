"""Tests of the families kept in the tables of residents."""

import datetime as dt

import pytest
from django.utils import timezone

from server.apps.accounts.models import User
from server.apps.residents.infra.families import StoredFamilies
from server.apps.residents.logic.family import Member
from server.apps.residents.models import Kinship, Resident


def _linked(resident: Resident, relative: User) -> Kinship:
    """Links the resident to the relative as a child."""
    return Kinship.objects.create(
        resident=resident,
        kind='child',
        relative=relative.pk,
        granted_by=relative.pk,
    )


@pytest.mark.django_db
def test_lists_the_linked_residents(resident: Resident, relative: User) -> None:
    _linked(resident, relative)

    assert StoredFamilies().members(relative.pk) == (
        Member(full_name='Maria Ivanova', kind='child'),
    )


@pytest.mark.django_db
def test_hides_residents_who_moved_out(resident: Resident, relative: User) -> None:
    _linked(resident, relative)
    resident.moved_out_on = dt.date(2026, 3, 1)
    resident.save()

    assert StoredFamilies().members(relative.pk) == ()


@pytest.mark.django_db
def test_hides_revoked_links(resident: Resident, relative: User) -> None:
    Kinship.objects.filter(pk=_linked(resident, relative).pk).update(
        revoked_at=timezone.now(),
    )

    assert StoredFamilies().members(relative.pk) == ()


@pytest.mark.django_db
def test_hides_residents_of_other_relatives(
    resident: Resident,
    relative: User,
) -> None:
    _linked(resident, User.objects.create_user(username='boris@example.test'))

    assert StoredFamilies().members(relative.pk) == ()
