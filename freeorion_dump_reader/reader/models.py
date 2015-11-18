import os
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db import models
from django.conf import settings


class Game(models.Model):
    game_id = models.CharField(max_length=256, primary_key=True)
    empire_name = models.CharField(max_length=256)
    creation_date = models.DateTimeField()
    empire_id = models.IntegerField()

    class Meta:
        ordering = ['-creation_date', 'empire_name']

    def __unicode__(self):
        return 'Game(%s) at %s' % (self.empire_name, self.creation_date)

    def get_ends(self):
        turns = self.turn_set.all()
        linked = set(x.parent_id for x in turns)
        return (x for x in turns if x.turn_id not in linked)

    def get_branch(self, turn):
        all_turns = Turn.objects.filter(turn__lte=turn.turn, game=self).order_by('-turn')
        branch = [turn]
        next_turn = turn.parent_id
        for item in all_turns:
            if item.turn_id == next_turn:
                branch.append(item)
                next_turn = item.parent_id
        return reversed(branch)


class Turn(models.Model):
    turn = models.IntegerField()
    game = models.ForeignKey(Game)
    turn_id = models.CharField(max_length=256)
    parent_id = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        unique_together = (("game", "turn_id"),)

    def __unicode__(self):
        return 'Turn %s' % self.turn


class Planet(models.Model):
    pid = models.IntegerField()
    name = models.CharField(max_length=256)
    size = models.CharField(max_length=256)  # Change to choices
    focus = models.CharField(max_length=256)
    owned = models.BooleanField()
    visibility = models.CharField(max_length=256)
    species = models.CharField(max_length=256)
    owner = models.CharField(max_length=256, null=True, blank=True)
    turn = models.ForeignKey(Turn)
    sid = models.ForeignKey('System')

    class Meta:
        unique_together = (('pid', 'turn'),)


VISIBILITY = tuple((x, x) for x in ('partial', 'full', 'none'))


class System(models.Model):
    sid = models.IntegerField()
    name = models.CharField(max_length=256)
    star = models.CharField(max_length=256)
    visibility = models.CharField(max_length=256, choices=VISIBILITY)
    neighbors = models.ManyToManyField("self")
    tags = models.CharField(max_length=1024)
    coords = models.CharField(max_length=256)  # coords
    last_battle = models.IntegerField()
    owner_tags = models.CharField(max_length=1024)
    turn = models.ForeignKey(Turn)

    class Meta:
        unique_together = (('sid', 'turn'),)


RESEARCH_TYPES = tuple((x, x) for x in ('application', 'theory', 'refinement'))
RESEARCH_CATEGORIES = tuple(
    (x, x) for x in ('CONSTRUCTION_CATEGORY', 'SPY_CATEGORY', 'PRODUCTION_CATEGORY', 'SHIPS_CATEGORY',
                     'GROWTH_CATEGORY', 'DEFENSE_CATEGORY', 'LEARNING_CATEGORY'))


def read_techs(stream):
    res = []
    for line in stream:
        if line.startswith('Tech'):
            yield res
            res = []
        else:
            res.append(line.strip(' \t\n\r'))


_research_cache = {}


def rgb(red, green, blue, alpha=255):
    return '#%x%x%x' % (red, green, blue)


_categories = {
    'LEARNING_CATEGORY': ('learning.png', rgb(54, 202, 229)),
    'GROWTH_CATEGORY': ('growth.png', rgb(116, 225, 107)),
    'PRODUCTION_CATEGORY': ('production.png', rgb(240, 106, 106, 255)),
    'CONSTRUCTION_CATEGORY': ('construction.png', rgb(241, 233, 87, 255)),
    'DEFENSE_CATEGORY': ('defense.png', rgb(70, 80, 215, 255)),
    'SHIPS_CATEGORY': ('ships.png', rgb(255, 139, 85, 255)),
    'SPY_CATEGORY': ('spy.png', rgb(168, 0, 255, 255)),
}


def get_research_information(name):
    if not _research_cache:
        path = os.path.join(settings.PROJECT_FOLDER, 'techs.txt')
        with open(path) as f:
            iterator = read_techs(f)
            next(iterator)
            for tech_lines in iterator:
                info = {}
                for item in tech_lines:
                    if item.startswith('name = "'):
                        info['name'] = item.split(' = ')[1].strip('"')
                    elif item.startswith('description = "'):
                        info['short_description'] = item.split(' = ')[1].strip('"')
                    elif item.startswith('short_description = "'):
                        info['description'] = item.split(' = ')[1].strip('"')
                    elif item.startswith('graphic = "'):
                        info['graphic'] = item.split(' = ')[1].strip('"')
                    elif item.startswith('category = "'):
                        info['category'] = item.split(' = ')[1].strip('"')
                path, color = _categories[info['category']]
                if 'graphic' not in info:
                    info['icon'] = 'icons/tech/categories/' + path
                info['color'] = color
                _research_cache[info['name']] = info
    return _research_cache[name]


class ResearchInfo(models.Model):
    game = models.ForeignKey(Game)
    category = models.CharField(choices=RESEARCH_CATEGORIES, max_length=256)
    name = models.CharField(max_length=256)
    cost = models.FloatField()
    type = models.CharField(choices=RESEARCH_TYPES, max_length=256)

    class Meta:
        unique_together = ('game', 'name')

    def get_icon(self):
        info = get_research_information(self.name)
        icon_path = os.path.join('data', 'art', info['graphic'])
        st = static(icon_path.replace('\\', '/'))
        return '<img src="%s" width="16px" style="background-color: %s">' % (st, info['color'])


class Research(models.Model):
    allocation = models.CharField(max_length=256)
    turn_left = models.IntegerField()
    research_info = models.ForeignKey(ResearchInfo)

    turn = models.ForeignKey(Turn)

#
#
# class FleetModel(Model):
#     SECTION = 'fleets'
#     fid = NumberField()
#     name = StringField()
#     sid = NumberField()
#     owner = OwnerField()
#     visibility = StringField()
#     ships = ListField()
#     target = TargetField()
#
#     def get_key(self):
#         return self.fid
#
#
# class OrderModel(Model):
#     SECTION = 'orders'
#     name = StringField()
#     args = MapField()
#
#     def get_key(self):
#         return '%s: %s' % (self.name, ', '.join('%s:%s' % x for x in sorted(self. args.items())))
#
#
