from django import template
from django.utils.translation import gettext as _
from django.utils.translation import pgettext

register = template.Library()


@register.filter
def translate_category(category_name):
    """
    Translate category names. This filter handles the translation of
    service category names that come from the database.
    """
    translations = {
        "Arts and Crafts": _("Arts and Crafts"),
        "Beauty": _("Beauty"),
        "Caregiving": _("Caregiving"),
        "Conversation and Counseling": _("Conversation and Counseling"),
        "Education": _("Education"),
        "Entertainment": _("Entertainment"),
        "Financial": _("Financial"),
        "Fitness": _("Fitness"),
        "Food": _("Food"),
        "General Labor": _("General Labor"),
        "Healthcare": _("Healthcare"),
        "Home": pgettext(
            "service_category", "Home"
        ),  # Use context for service category
        "Landscaping": _("Landscaping"),
        "Legal": _("Legal"),
        "Other": _("Other"),
        "Pet": _("Pet"),
        "Repair": _("Repair"),
        "Tech": _("Tech"),
        "Transportation": _("Transportation"),
        "Wellness": _("Wellness"),
    }
    return translations.get(category_name, category_name)
