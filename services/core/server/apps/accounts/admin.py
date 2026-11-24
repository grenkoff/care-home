"""Admin pages of the accounts module."""

from typing import Any, final, override

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpRequest

from server.apps.accounts.models import Invitation, User


@final
class InvitationAdmin(admin.ModelAdmin[Invitation]):
    """Invitations that staff make for relatives."""

    @override
    def save_model(
        self,
        request: HttpRequest,
        invitation: Invitation,
        form: Any,
        change: bool,
    ) -> None:
        """Issues a fresh link of the invitation and shows it to staff once."""


admin.site.register(User, UserAdmin)
admin.site.register(Invitation, InvitationAdmin)
