"""Admin panel of cameras and the journal of viewings."""

from typing import final, override

from django.contrib import admin
from django.http import HttpRequest

from server.apps.cameras.models import Camera, Viewing


@final
class CameraAdmin(admin.ModelAdmin[Camera]):
    """Cameras of the common areas that staff name and switch on or off."""

    list_display = ('name_ru', 'name_en', 'stream', 'active')


@final
class ViewingAdmin(admin.ModelAdmin[Viewing]):
    """Journal of viewings that staff read and never rewrite."""

    list_display = ('opened_at', 'camera', 'viewer')

    @override
    def has_add_permission(self, request: HttpRequest) -> bool:
        """Forbids adding, so the journal holds only real viewings."""
        return False

    @override
    def has_change_permission(
        self,
        request: HttpRequest,
        viewing: Viewing | None = None,
    ) -> bool:
        """Forbids changing, so the journal stays as it was written."""
        return False

    @override
    def has_delete_permission(
        self,
        request: HttpRequest,
        viewing: Viewing | None = None,
    ) -> bool:
        """Forbids deleting, so no viewing disappears from the journal."""
        return False


admin.site.register(Camera, CameraAdmin)
admin.site.register(Viewing, ViewingAdmin)
