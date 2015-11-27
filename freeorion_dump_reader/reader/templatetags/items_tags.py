from django import template

from reader.models import Turn
from reader.tools import date_from_id
from django.core.exceptions import ObjectDoesNotExist

register = template.Library()


@register.simple_tag()
def game_label(game):
    return ('<span>'
            '<strong style="color: {game.empire.rgb};">{game.empire.name} {game.empire.empire_id}</strong>'
            '<small> [{game.game_id}] </small>'
            '<sup>{time}</sup>'
            '</span>').format(game=game, time=game.creation_date.strftime('%d %b, %H:%M'))



@register.simple_tag()
def turn_label(turn):
    return '<span>Turn %s<small> [%s] </small><sup>%s</sup></span>' % (turn.turn,
                                                                       turn.turn_id,
                                                                       date_from_id(turn.turn_id).strftime('%d %b, %H:%M'))


@register.simple_tag()
def turn_links(turn):
    return '<a href="/{turn.game.game_id}/{turn.turn_id}/research/progress">research_progress</a>'.format(turn=turn)


@register.simple_tag()
def turn_info_link(turn):
    try:
        previous_turn_id = Turn.objects.get(turn_id=turn.parent_id).turn_id
    except ObjectDoesNotExist:
        previous_turn_id = 0

    return (
        '<a '
        'href="/{turn.game.game_id}/{turn.turn_id}/{turn.game.game_id}/{previous_turn_id}"'
        '>'
        'Turn info'
        '</a>'
    ).format(turn=turn, previous_turn_id=previous_turn_id)
