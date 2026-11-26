"""Admin panel of cameras."""

from typing import final

from django.contrib import admin

from server.apps.cameras.models import Camera


@final
class CameraAdmin(admin.ModelAdmin[Camera]):
    """Cameras of the common areas that staff name and switch on or off."""

    list_display = ('name_ru', 'name_en', 'stream', 'active')


admin.site.register(Camera, CameraAdmin)
