"""Admin panel of enquiries."""

from django.contrib import admin

from server.apps.enquiries.models import Enquiry

admin.site.register(Enquiry)
