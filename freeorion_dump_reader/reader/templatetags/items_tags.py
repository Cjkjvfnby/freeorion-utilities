from django import template
from reader.tools import date_from_id

register = template.Library()


@register.simple_tag()
def game_label(game):
    return '<span>%s %s<small> [%s] </small><sup>%s</sup></span>' % (game.empire_name, game.empire_id, game.game_id,
                                                                     game.creation_date.strftime('%d %b, %H:%M'))


@register.simple_tag()
def turn_label(turn):
    return '<span>Turn %s<small> [%s] </small><sup>%s</sup></span>' % (turn.turn,
                                                                       turn.turn_id,
                                                                       date_from_id(turn.turn_id).strftime('%d %b, %H:%M'))


@register.simple_tag()
def turn_links(turn):
    return '<a href="/{turn.game.game_id}/{turn.turn_id}/research/progress">research_progress</a>'.format(turn=turn)
