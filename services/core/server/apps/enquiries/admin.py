"""Admin panel of enquiries."""

from typing import final

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from server.apps.enquiries.models import Enquiry


@final
class EnquiryAdmin(admin.ModelAdmin[Enquiry]):
    """Enquiries of visitors that staff call back, the newest first."""

    list_display = ('sent_at', 'name', 'phone', 'handled')
    actions = ('mark_handled',)

    @admin.action(description=_('Mark as handled'))
    def mark_handled(self, request: HttpRequest, chosen: QuerySet[Enquiry]) -> None:
        """Marks the chosen enquiries as handled."""
        chosen.update(handled=True)


admin.site.register(Enquiry, EnquiryAdmin)
