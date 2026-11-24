"""Admin panel of care."""

from django.contrib import admin

from server.apps.care.models import Service

admin.site.register(Service)
