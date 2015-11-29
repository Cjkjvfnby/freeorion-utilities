from reader.models import VISIBILITY_PARTIAL, Planet


def formatter_species(name):
    return name[3:]


class Diff(object):
    def __init__(self, name, this, that, added, removed, info=''):
        self.name = name
        self.this = this
        self.that = that
        self.added = added
        self.removed = removed
        self.info = info

    def __unicode__(self):
        return "Diff for %s" % self.name

    def same(self):
        return self.this == self.that


def get_diff(this, that):
    """
    :type this: reader.models.Turn
    :type that: reader.models.Turn

    """
    def number_diff(name, first, second, info=''):
        added, removed = '', ''
        diff = first - second
        if diff > 0:
            added = '%+d' % diff
        elif diff < 0:
            removed = '%d' % diff
        return Diff(name, first, second, added, removed, info=info)

    def list_diff(name, first, second, info='', formatter=lambda x: x):
        first = set(formatter(x) for x in first)
        second = set(formatter(x) for x in second)

        def _to_str(collection):
            return ', '.join(sorted(str(x) for x in collection))

        added, removed = first - second, second - first
        return Diff(name, _to_str(first), _to_str(second), _to_str(added), _to_str(removed), info=info)

    return [
        number_diff('turn', this.turn, that.turn),
        number_diff('population', this.population, that.population),
        number_diff('production', this.production, that.production),
        number_diff('fleet count', this.fleets.count(), that.fleets.count()),
        number_diff('order issued', this.orders.count(), that.orders.count()),
        number_diff('systems known', this.systems.count(), that.systems.count()),
        number_diff('systems supplied', this.systems.filter(supplied=True).count(),
                    that.systems.filter(supplied=True).count()),
        number_diff('systems explored', this.systems.filter(explored=True).count(),
                    that.systems.filter(explored=True).count()),
        number_diff('systems with partial visibility', this.systems.filter(visibility=VISIBILITY_PARTIAL).count(),
                    that.systems.filter(visibility=VISIBILITY_PARTIAL).count()),
        number_diff('known planets',
                    Planet.objects.filter(turn=this).count(),
                    Planet.objects.filter(turn=that).count()
                    ),
        number_diff('owned planets',
                    Planet.objects.filter(turn=this, owned=True).count(),
                    Planet.objects.filter(turn=that, owned=True).count()
                    ),
        list_diff('species',
                  Planet.objects.filter(turn=this, owned=True).values_list('species', flat=True),
                  Planet.objects.filter(turn=that, owned=True).values_list('species', flat=True),
                  formatter=formatter_species
                  ),
    ]
