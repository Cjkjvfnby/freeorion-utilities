from reader.fields import (NumberField, StringField, TurnField, ListField, CoordinatesField,
                           BooleanField, TargetField, MapField, OwnerField)
from reader.base_models import Model


class PlanetModel(Model):
    SECTION = 'planets'
    pid = NumberField()
    name = StringField()
    size = NumberField()
    focus = StringField(preprocess=lambda x: x[6:].lower().capitalize())
    sid = NumberField()
    owned = BooleanField()
    visisbility = StringField()
    species = StringField(preprocess=lambda x: x[3:].lower().capitalize())

    def get_key(self):
        return self.pid


class SystemModel(Model):
    SECTION = 'systems'
    sid = NumberField()
    name = StringField()
    star = StringField()
    planets = ListField()
    visibility = StringField()
    neighbors = ListField()
    tags = ListField()
    coords = CoordinatesField()
    last_battle = TurnField()
    owner_tags = ListField()

    def get_key(self):
        return self.sid


class FleetModel(Model):
    SECTION = 'fleets'
    fid = NumberField()
    name = StringField()
    sid = NumberField()
    owner = OwnerField()
    visibility = StringField()
    ships = ListField()
    target = TargetField()

    def get_key(self):
        return self.fid


class OrderModel(Model):
    SECTION = 'orders'
    name = StringField()
    args = MapField()

    def get_key(self):
        return '%s: %s' % (self.name, ', '.join('%s:%s' % x for x in sorted(self. args.items())))


class ResearchModel(Model):
    SECTION = 'research'
    name = StringField()
    category = StringField()
    allocation = StringField()
    cost = NumberField()
    turn_left = NumberField()
    type = StringField()

    def get_key(self):
        return self.name
