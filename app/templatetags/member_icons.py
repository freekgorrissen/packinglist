from django import template
from django.utils.safestring import mark_safe

from app.models import MemberIcon

register = template.Library()

MEMBER_ICON_HTML = {
    MemberIcon.MAN: '<i class="bi bi-person-standing member-icon" aria-hidden="true"></i>',
    MemberIcon.WOMAN: '<i class="bi bi-person-standing-dress member-icon" aria-hidden="true"></i>',
    MemberIcon.CHILD: '<i class="bi bi-person-arms-up member-icon" aria-hidden="true"></i>',
    MemberIcon.DOG: '<span class="member-icon member-icon-emoji" aria-hidden="true">🐕</span>',
}


@register.simple_tag
def member_icon(icon_key):
    return mark_safe(MEMBER_ICON_HTML.get(icon_key, MEMBER_ICON_HTML[MemberIcon.MAN]))
