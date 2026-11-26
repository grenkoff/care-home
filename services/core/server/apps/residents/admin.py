"""Admin panel of residents and their relatives."""

from typing import Any, final, override

from django import forms
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db.models import Field, QuerySet
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from server.apps.residents.logic.usecases import find_relative
from server.apps.residents.models import Kinship, Relative, Resident
from server.apps.residents.views.forms import KinshipForm, RelativeField
from server.common.di import HasContainer


@final
class ResidentAdmin(admin.ModelAdmin[Resident]):
    """Residents of the home, by name."""

    list_display = ('full_name', 'moved_in_on', 'moved_out_on')


@final
class KinshipAdmin(HasContainer, admin.ModelAdmin[Kinship]):
    """Links of residents to relatives, revoked but never changed or deleted."""

    form = KinshipForm
    list_display = ('resident', 'kind', 'granted_at', 'revoked_at')

    @admin.action(description=_('Revoke'), permissions=('change',))
    def revoke(self, request: HttpRequest, chosen: QuerySet[Kinship]) -> None:
        """Revokes the chosen links that still work and keeps them."""
        chosen.filter(revoked_at__isnull=True).update(revoked_at=timezone.now())

    actions = (revoke,)

    @override
    def formfield_for_dbfield(
        self,
        db_field: Field[Any, Any],
        request: HttpRequest,
        **kwargs: Any,
    ) -> forms.Field | None:
        """Asks for the e-mail of the relative instead of the id of the account."""
        if db_field.name == 'relative':
            return RelativeField(
                self.resolve(find_relative.FindRelative),
                label=_('e-mail of the relative'),
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    @override
    def has_change_permission(
        self,
        request: HttpRequest,
        kinship: Kinship | None = None,
    ) -> bool:
        """Lets staff revoke chosen links but never change one."""
        return kinship is None and super().has_change_permission(request)

    @override
    def has_delete_permission(
        self,
        request: HttpRequest,
        kinship: Kinship | None = None,
    ) -> bool:
        """Forbids deleting, so a revoked link stays in the history."""
        return False

    @override
    def save_model(
        self,
        request: HttpRequest,
        kinship: Kinship,
        form: Any,
        change: bool,
    ) -> None:
        """Records who of the staff granted the link."""
        granted_by = request.user.pk
        if granted_by is None:
            raise PermissionDenied
        kinship.granted_by = granted_by
        super().save_model(request, kinship, form, change)


@final
class RelativeAdmin(admin.ModelAdmin[Relative]):
    """Accounts copied from accounts, which staff read but never rewrite."""

    list_display = ('email',)

    @override
    def has_add_permission(self, request: HttpRequest) -> bool:
        """Forbids adding, since only the facts of accounts fill the copy."""
        return False

    @override
    def has_change_permission(
        self,
        request: HttpRequest,
        _relative: Relative | None = None,
    ) -> bool:
        """Forbids changes, so the copy stays as accounts reported it."""
        return False

    @override
    def has_delete_permission(
        self,
        request: HttpRequest,
        _relative: Relative | None = None,
    ) -> bool:
        """Forbids deleting, so a copied account stays linkable."""
        return False


admin.site.register(Resident, ResidentAdmin)
admin.site.register(Kinship, KinshipAdmin)
admin.site.register(Relative, RelativeAdmin)
