from django import template
from django.utils.safestring import mark_safe

register = template.Library()



@register.simple_tag()
def game_label(empire):
    return '<span>%s %s<small> [%s] </small><sup>%s</sup></span>' % (empire.name, empire.empire_id, empire.game_id, empire.creation_date.strftime('%d %b, %H:%M'))


@register.simple_tag()
def turn_label(turn):
    return '<span>Turn %s<small> [%s] </small><sup>%s</sup></span>' % (turn.turn, turn.turn_id, turn.get_date().strftime('%d %b, %H:%M'))


@register.filter(name='cell', is_safe=True, takes_context=True)
def cell(value, key):
    if key == 'args':
        if not value:
            return ''
        return mark_safe(', '.join(('<small><i>%s=</i></small>%s' % (k, v) for k, v in value.items())))
    elif key in ('ships', 'neighbors', 'tags', 'owner_tags', 'planets'):
        return ', '.join(str(x) for x in value)
    elif key == 'target':
        if not value:
            return "no mission"
        mission_type, target_id, target_type, target_name = value
        print value
        if mission_type == 'None':
            return "mission with out targets"
        return "%s: %s %s(%s)" % (mission_type, target_type, target_name, target_id)
    elif key == 'focus':
        return value[6:].lower().capitalize()
    elif key == 'species':
        return value[3:].lower().capitalize()
    elif key == 'owned':
        return value and 'Yes' or 'No'
    elif key == 'coords':
        return ', '.join('%.0f' % x for x in value)
    elif key == 'last_battle':
        return value if value != -65535 else ''
    return value


@register.filter(name='empire_cell', is_safe=True, takes_context=True)
def empire_cell(empire_id, my_empire_id):
    empire_id = str(empire_id)
    if empire_id == '-1':
        return 'monster'
    elif empire_id == my_empire_id:
        return 'me'
    else:
        return str(empire_id)
