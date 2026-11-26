"""Admin panel of residents and their relatives."""

from typing import final

from django.contrib import admin

from server.apps.residents.models import Kinship, Resident


@final
class ResidentAdmin(admin.ModelAdmin[Resident]):
    """Residents of the home, by name."""

    list_display = ('full_name', 'moved_in_on', 'moved_out_on')


@final
class KinshipAdmin(admin.ModelAdmin[Kinship]):
    """Links of residents to the accounts of their relatives."""

    list_display = ('resident', 'kind', 'granted_at', 'revoked_at')


admin.site.register(Resident, ResidentAdmin)
admin.site.register(Kinship, KinshipAdmin)
