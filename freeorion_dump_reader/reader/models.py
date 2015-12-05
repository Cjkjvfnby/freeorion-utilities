import os
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db import models
from django.conf import settings


class Game(models.Model):
    game_id = models.CharField(max_length=256, primary_key=True)
    creation_date = models.DateTimeField()

    class Meta:
        ordering = ['-creation_date', 'game_id']

    def __unicode__(self):
        return 'Game(%s) at %s' % (self.empire.name, self.creation_date)

    @property
    def empire(self):
        return self.empires.get(is_me=True)

    def get_ends(self):
        return Branch.objects.filter(turn__game=self)

    def get_branch(self, turn):
        return Branch.objects.get(turn=turn).turns.order_by('id').all()


class Part(models.Model):
    name = models.CharField(max_length=256, primary_key=True)


class Hull(models.Model):
    name = models.CharField(max_length=256, primary_key=True)


class Building(models.Model):
    name = models.CharField(max_length=256, primary_key=True)


class Turn(models.Model):
    turn = models.IntegerField()
    game = models.ForeignKey(Game, related_name='turns')
    turn_id = models.CharField(max_length=256)
    parent_id = models.CharField(max_length=256, blank=True, null=True)
    production = models.FloatField()
    population = models.FloatField()
    parts = models.ManyToManyField(Part)
    hulls = models.ManyToManyField(Hull)
    buildings = models.ManyToManyField(Building)

    class Meta:
        unique_together = (("game", "turn_id"),)

    @classmethod
    def find_turn(cls, game_id, turn_id, decrement):

        base_turn = cls.objects.get(game__game_id=game_id, turn_id=turn_id)
        if decrement is None:
            return base_turn
        else:
            decrement = int(decrement)
            assert decrement >= 0, 'Decrement should be positive'
            return base_turn.branches.first().turns.get(turn=base_turn.turn-decrement)

    def __unicode__(self):
        return 'Turn %s(%s)' % (self.turn, self.turn_id)

    def get_empire(self):
        return self.game.empires.filter(is_me=True).get()

    def get_monsters(self):
        return self.game.empires.filter(empire_id=-1).get()


class Planet(models.Model):
    pid = models.IntegerField()
    name = models.CharField(max_length=256)
    size = models.CharField(max_length=256)  # Change to choices
    focus = models.CharField(max_length=256)
    owned = models.BooleanField()
    visibility = models.CharField(max_length=256)
    species = models.CharField(max_length=256)
    empire = models.ForeignKey('Empire', related_name='planets', null=True)
    turn = models.ForeignKey(Turn, related_name='planets')
    sid = models.ForeignKey('System', related_name='planets')

    class Meta:
        unique_together = (('pid', 'turn'),)


VISIBILITY_PARTIAL = 'partial'
VISIBILITY_FULL = 'full'
VISIBILITY_NONE = 'none'

VISIBILITY = tuple((x, x) for x in (VISIBILITY_FULL, VISIBILITY_PARTIAL, VISIBILITY_NONE))


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
    turn = models.ForeignKey(Turn, related_name='systems')
    supplied = models.BooleanField()
    explored = models.BooleanField()
    is_capital = models.BooleanField()

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
    return '#%02X%02X%02X' % (red, green, blue)


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
        unique_together = (('game', 'name'),)

    def get_icon(self):
        info = get_research_information(self.name)
        icon_path = os.path.join('data', 'art', info['graphic'])
        st = static(icon_path.replace('\\', '/'))
        return '<img src="%s" width="16px" style="background-color: %s">' % (st, info['color'])


class Research(models.Model):
    allocation = models.CharField(max_length=256)
    turn_left = models.IntegerField()
    research_info = models.ForeignKey(ResearchInfo, related_name='researches')
    turn = models.ForeignKey(Turn, related_name='researches')

    class Meta:
        unique_together = (('turn', 'research_info'),)


class Fleet(models.Model):
    fid = models.IntegerField()
    name = models.CharField(max_length=256)
    system = models.ForeignKey(System, null=True)
    empire = models.ForeignKey('Empire', related_name='fleets')
    visibility = models.CharField(max_length=256, choices=VISIBILITY)
    turn = models.ForeignKey(Turn, related_name='fleets')
    is_destroyed = models.BooleanField()

    class Meta:
        unique_together = ('turn', 'fid')


class FleetTarget(models.Model):
    fleet = models.OneToOneField(Fleet, primary_key=True)
    mission_type = models.CharField(max_length=256)  # TODO use enum
    target_id = models.CharField(max_length=256)  # TODO make enum or ContentTypeKey
    target_type = models.CharField(max_length=256)  # TODO remove after all models will be in base
    target_name = models.CharField(max_length=256)


class Empire(models.Model):
    """
    Basic information about empire
    """
    empire_id = models.IntegerField()
    rgb = models.CharField(max_length=7)
    name = models.CharField(max_length=256)
    is_me = models.BooleanField()
    game = models.ForeignKey(Game, related_name='empires')

    class Meta:
        unique_together = (('game', 'empire_id'),)

    def __unicode__(self):
        return 'Empire %s(%s)' % (self.name, self.empire_id)


class DesignInfo(models.Model):
    did = models.IntegerField()
    name = models.CharField(max_length=256)
    parts = models.CharField(max_length=1024)
    description_key = models.CharField(max_length=256)
    designed_on_turn = models.IntegerField()
    structure = models.IntegerField()
    shields = models.IntegerField()
    speed = models.IntegerField()
    hull = models.CharField(max_length=256)
    defense = models.IntegerField()
    game = models.ForeignKey(Game)

    class Meta:
        unique_together = (('game', 'did'),)


class Design(models.Model):
    attack_stats = models.CharField(max_length=256)
    design_info = models.ForeignKey(DesignInfo, related_name='designs')
    turn = models.ForeignKey(Turn, related_name='designs')

    class Meta:
        unique_together = (('turn', 'design_info'),)

    def __repr__(self):
        return 'Design(turn="%s", design_info__name="%s")' % (self.turn, self.design_info.name)


class Ship(models.Model):
    shid = models.IntegerField()
    name = models.CharField(max_length=256)
    species = models.CharField(max_length=256)  # add new table
    speed = models.IntegerField()
    age_in_turns = models.IntegerField()

    is_monster = models.BooleanField()
    is_armed = models.BooleanField()
    can_colonize = models.BooleanField()
    can_invade = models.BooleanField()
    can_bombard = models.BooleanField()

    colonizing_planet = models.IntegerField(help_text='have colonize order for planet')
    invading_planet = models.IntegerField(help_text='have invide order for planet')
    is_scrapping = models.BooleanField()
    fleet = models.ForeignKey(Fleet, related_name='ships')
    design = models.ForeignKey(Design, null=True, related_name='ships')  # Design ID can be null because monster fleet
    is_destroyed = models.BooleanField()

    class Meta:
        unique_together = (('fleet', 'shid'),)


class Order(models.Model):
    name = models.CharField(max_length=256)
    args = models.CharField(max_length=4096)
    turn = models.ForeignKey(Turn, related_name='orders')


class Branch(models.Model):
    turns = models.ManyToManyField(Turn, related_name='branches')
    turn = models.ForeignKey(Turn, related_name='ends')

    def __repr__(self):
        return 'Branch(%s)' % self.turn
