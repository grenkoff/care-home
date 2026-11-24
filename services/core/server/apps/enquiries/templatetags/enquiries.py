"""Template tags that put the enquiry form on pages of other modules."""

from django import template

from server.apps.enquiries.views.forms import EnquiryForm

register = template.Library()


@register.inclusion_tag('enquiries/form.html', takes_context=True)
def enquiry_form(context: template.Context) -> dict[str, object]:
    """Renders a blank enquiry form with the token of the page."""
    return {'form': EnquiryForm(), 'csrf_token': context.get('csrf_token')}
