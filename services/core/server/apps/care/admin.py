"""Admin panel of care."""

from typing import final

from django.contrib import admin

from server.apps.care.models import Service


@final
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin[Service]):
    """Care services that staff write in both languages and put in order."""

    list_display = ('name_ru', 'name_en', 'price_cents', 'position')
