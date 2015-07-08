from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='cell', is_safe=True, takes_context=True)
def cell(value, key):
    if key == 'args':
        if not value:
            return ''
        return mark_safe(', '.join(('<small><i>%s=</i></small>%s' % (k, v) for k, v in value.items())))
    elif key == 'ships':
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
