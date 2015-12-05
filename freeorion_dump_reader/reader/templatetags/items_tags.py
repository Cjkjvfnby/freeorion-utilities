from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from reader.models import Turn
from reader.tools import date_from_id
from django.core.exceptions import ObjectDoesNotExist

register = template.Library()


@register.simple_tag()
def game_label(game):
    return mark_safe(('<span>'
                      '<strong style="color: {game.empire.rgb};">{game.empire.name} {game.empire.empire_id}</strong>'
                      '<small> [{game.game_id}] </small>'
                      '<sup>{time}</sup>'
                      '</span>').format(game=game, time=game.creation_date.strftime('%d %b, %H:%M')))


@register.simple_tag()
def turn_label(turn):
    return format_html('<span>Turn {}<small> [{}] </small><sup>{}</sup></span>', turn.turn,
                                                                       turn.turn_id,
                                                                       date_from_id(turn.turn_id).strftime('%d %b, %H:%M'))


def make_link_template(text, href):
    href = map(str, href)
    return '<a class="btn btn-xs btn-info" href="/{href}">{text}</a>'.format(text=text, href='/'.join(href))


@register.simple_tag()
def turn_links(turn):

    res = [make_link_template('research progress', [turn.game.game_id,  turn.turn_id, 'research', 'progress'])]

    try:
        previous_turn_id = Turn.objects.get(turn_id=turn.parent_id).turn_id
    except ObjectDoesNotExist:
        previous_turn_id = 0

    res.append(
        make_link_template('turn info', [turn.game.game_id, turn.turn_id, turn.game.game_id, previous_turn_id])
    )
    return mark_safe(' '.join(res))
