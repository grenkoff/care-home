"""Database models of residents."""

import uuid
from typing import Final, final, override

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from server.apps.residents.logic.constants import (
    EMAIL_MAX_LENGTH,
    FULL_NAME_MAX_LENGTH,
    KIND_MAX_LENGTH,
)


@final
class Resident(models.Model):
    """Person who lives or lived in the home."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    full_name = models.CharField(_('full name'), max_length=FULL_NAME_MAX_LENGTH)
    moved_in_on = models.DateField(_('moved in'))
    moved_out_on = models.DateField(_('moved out'), null=True, blank=True)

    class Meta:
        """Order of residents for staff: by name."""

        ordering = ('full_name',)
        verbose_name = _('resident')
        verbose_name_plural = _('residents')
        constraints = (
            models.CheckConstraint(
                condition=models.Q(moved_out_on__isnull=True)
                | models.Q(moved_out_on__gte=models.F('moved_in_on')),
                name='%(app_label)s_%(class)s_moves_out_after_moving_in',
                violation_error_message=_(
                    'A resident cannot move out before moving in.',
                ),
            ),
        )

    @override
    def __str__(self) -> str:
        """Returns the full name of the resident."""
        return self.full_name


KINDS: Final = (
    ('spouse', _('spouse')),
    ('child', _('child')),
    ('grandchild', _('grandchild')),
    ('sibling', _('sibling')),
    ('other', _('other relative')),
)


@final
class KinshipQuerySet(models.QuerySet['Kinship']):
    """Links of residents to relatives, narrowed to those that work."""

    def working(self, relative: uuid.UUID) -> KinshipQuerySet:
        """Keeps the links of the relative that work to residents in the home."""
        return self.filter(
            relative=relative,
            revoked_at__isnull=True,
            resident__moved_out_on__isnull=True,
        )


@final
class Kinship(models.Model):
    """Link through which a relative may follow a resident."""

    objects = KinshipQuerySet.as_manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    resident = models.ForeignKey(
        Resident,
        on_delete=models.PROTECT,
        related_name='kinships',
        verbose_name=_('resident'),
        db_index=True,
    )
    kind = models.CharField(
        _('kinship'),
        max_length=KIND_MAX_LENGTH,
        choices=KINDS,
    )
    relative = models.UUIDField(_('relative'))
    granted_by = models.UUIDField(_('granted by'), editable=False)
    granted_at = models.DateTimeField(
        _('granted'),
        default=timezone.now,
        editable=False,
    )
    revoked_at = models.DateTimeField(
        _('revoked'),
        null=True,
        blank=True,
        editable=False,
    )

    class Meta:
        """Order of links for staff: the latest first."""

        ordering = ('-granted_at',)
        verbose_name = _('kinship')
        verbose_name_plural = _('kinships')
        constraints = (
            models.CheckConstraint(
                condition=models.Q(kind__in=[code for code, _label in KINDS]),
                name='%(app_label)s_%(class)s_kind_valid',
            ),
            models.UniqueConstraint(
                fields=('relative', 'resident'),
                condition=models.Q(revoked_at__isnull=True),
                name='%(app_label)s_%(class)s_one_working_link',
                violation_error_message=_(
                    'This relative is already linked to this resident.',
                ),
            ),
        )

    @override
    def __str__(self) -> str:
        """Returns the resident and the kinship."""
        return f'{self.resident}: {self.get_kind_display()}'


@final
class Relative(models.Model):
    """Account that staff may link to residents, copied from accounts by its fact."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    account = models.UUIDField(_('account'), unique=True)
    email = models.EmailField(_('e-mail'), max_length=EMAIL_MAX_LENGTH, unique=True)

    class Meta:
        """Order of copied accounts: by e-mail."""

        ordering = ('email',)
        verbose_name = _('relative')
        verbose_name_plural = _('relatives')

    @override
    def __str__(self) -> str:
        """Returns the e-mail of the account."""
        return self.email
