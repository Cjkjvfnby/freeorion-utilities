from django.db import models


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
    sid = models.IntegerField()
    owned = models.BooleanField()
    visibility = models.CharField(max_length=256)
    species = models.CharField(max_length=256)
    owner = models.CharField(max_length=256, null=True, blank=True)
    turn = models.ForeignKey(Turn)

    class meta:
        unique_together = (('pid', 'turn'),)


#
#
# class SystemModel(Model):
#     SECTION = 'systems'
#     sid = NumberField()
#     name = StringField()
#     star = StringField()
#     planets = ListField()
#     visibility = StringField()
#     neighbors = ListField()
#     tags = ListField()
#     coords = CoordinatesField()
#     last_battle = TurnField()
#     owner_tags = ListField()
#
#     def get_key(self):
#         return self.sid
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
# class ResearchModel(Model):
#     SECTION = 'research'
#     name = StringField()
#     category = StringField()
#     allocation = StringField()
#     cost = NumberField()
#     turn_left = NumberField()
#     type = StringField()
#
#     def get_key(self):
#         return self.name
