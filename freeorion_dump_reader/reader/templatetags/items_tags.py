from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag()
def game_label(empire):
    return '<span>%s %s<small> [%s] </small><sup>%s</sup></span>' % (empire.name, empire.empire_id, empire.game_id, empire.creation_date.strftime('%d %b, %H:%M'))


@register.simple_tag()
def turn_label(turn):
    return '<span>Turn %s<small> [%s] </small><sup>%s</sup></span>' % (turn.turn, turn.turn_id, turn.get_date().strftime('%d %b, %H:%M'))
