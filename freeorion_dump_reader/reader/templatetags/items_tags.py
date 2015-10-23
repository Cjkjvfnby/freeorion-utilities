from django import template
from reader.tools import date_from_id

register = template.Library()


@register.simple_tag()
def game_label(empire):
    return '<span>%s %s<small> [%s] </small><sup>%s</sup></span>' % (empire.name, empire.empire_id, empire.game_id, empire.creation_date.strftime('%d %b, %H:%M'))


@register.simple_tag()
def turn_label(turn):
    return '<span>Turn %s<small> [%s] </small><sup>%s</sup></span>' % (turn['turn'],
                                                                       turn['turn_id'],
                                                                       date_from_id(turn['turn_id']).strftime('%d %b, %H:%M'))
