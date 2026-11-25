"""Admin pages of the accounts module."""

from typing import Any, final, override

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext

from server.apps.accounts.logic.usecases import invite_relative
from server.apps.accounts.models import Invitation, User
from server.common.di import HasContainer


@final
class InvitationAdmin(HasContainer, admin.ModelAdmin[Invitation]):
    """Invitations that staff make for relatives and never change once sent."""

    list_display = ('email', 'expires_at', 'accepted_at')

    @override
    def has_change_permission(
        self,
        request: HttpRequest,
        _invitation: Invitation | None = None,
    ) -> bool:
        """Forbids changes, so a link already sent keeps working."""
        return False

    @override
    def save_model(
        self,
        request: HttpRequest,
        invitation: Invitation,
        form: Any,
        change: bool,
    ) -> None:
        """Issues a fresh link of the invitation and shows it to staff once."""
        issued = self.resolve(invite_relative.InviteRelative)()
        invitation.email = invitation.email.lower()
        invitation.digest = issued.digest
        invitation.expires_at = issued.expires_at
        super().save_model(request, invitation, form, change)
        link = request.build_absolute_uri(
            reverse('accounts:accept', args=(issued.code,)),
        )
        self.message_user(
            request,
            gettext('Send this link to the relative, it is shown only once: %(link)s')
            % {'link': link},
            messages.SUCCESS,
        )


admin.site.register(User, UserAdmin)
admin.site.register(Invitation, InvitationAdmin)
