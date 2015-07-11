import json
import os
from django.conf import settings
from django.http import Http404
from reader.tools import date_from_id


_CACHE = {}


class TurnEntry(dict):
    def __init__(self, turn_model, data):
        super(TurnEntry, self).__init__(data)
        self.model = turn_model

    def get_diff(self, other):
        keys = set(self.keys() + other.keys())
        this_id, other_id = self.get_id(), other.get_id()
        diff = [('id', this_id, other_id)]
        for key in keys:
            this_value = self.get(key)
            other_value = other.get(key)
            if this_value != other_value:
                diff.append((key, this_value, other_value))
        if len(diff) == 1:  # only header
            return None
        return diff

    def get_id(self):
        raise NotImplementedError('Override in children.')


class BaseModel(object):
    section = None
    entry_class = TurnEntry

    @classmethod
    def get_turns(cls, game, turn):
        section_info = cls.load_game_section(game)
        if turn not in section_info:
            raise Http404('Cant find proper turn: %s' % turn)
        last = section_info[turn]
        turns = [last]
        while last.parent_id in section_info:
            last = section_info[last.parent_id]
            turns.append(last)
        return turns[::-1]

    @classmethod
    def find_branches(cls, game):
        turn_infos = cls.load_game_section(game).values()
        linked = set(x.parent_id for x in turn_infos)
        return [x for x in turn_infos if x.turn_id not in linked]

    @classmethod
    def load_game_section(cls, game):
        key = (game, cls.section)
        if key not in _CACHE:
            file_path = os.path.join(settings.DUMP_FOLDER, game, cls.section)
            if not os.path.exists(file_path):
                raise Http404("Path is missed %s" % file_path)
            data = {}
            with open(file_path) as f:
                for line in f:
                    line = line.strip('\n\r')
                    turn_info = cls(game, json.loads(line))
                    data[turn_info.turn_id] = turn_info
            _CACHE[key] = data
        return _CACHE[key]

    @classmethod
    def get_branch(cls, game, turn, start, end):
        turns = cls.load_game_section(game)
        result = [turns[turn]]
        while result[-1].parent_id in turns:
            result.append(turns[result[-1].parent_id])
        start = start and int(start) or 1
        end = end and int(end) or len(result)
        return result[::-1][start-1:end]

    def __init__(self, game, input_data):
        """
        Convention first name in header is all ways unique key for item!!!
        """
        self.turn_info, data = input_data
        self.data = [self.entry_class(self, x) for x in data]

        self.turn = self.turn_info['turn']
        self.turn_id = self.turn_info['turn_id']
        self.parent_id = self.turn_info['parent_id']
        empire_id, _, empire_name = game.split('_', 2)
        self.empire_id = empire_id
        self.empire_name = empire_name
        self.columns = []
        for item in self.data:
            self.columns.append([])
            for key in self.headers:
                self.columns[-1].append((key, item.get(key)))

    def get_date(self):
        return date_from_id(self.turn_id)

    def __repr__(self):
        return "%s %s" % (self.section, self.turn_id)

    def compare(self, other):
        """
        Make diff with other turn.
        Only fields from this turn_info are counted.
        Only difference are shown.
        Structure:
         - list of diffs of each items.
           - diff is list of 3 item tuple (key, first_value, second_value)
             if key missed in one of items its value will be None

        """
        data1 = {x.get_id(): x for x in self.data}
        data2 = {x.get_id(): x for x in other.data}
        keys = set(data1.keys() + data2.keys())
        difference = []
        for key in sorted(keys):
            diff = self._compare_entries(data1.get(key), data2.get(key))
            if diff:
                difference.append(diff)
        return difference

    def _compare_entries(self, this, other):
        """
        Return list of 3 item tuples if have any differences
        In that case first tuple is unique key
        if not differences None returned.
        """
        if this is None:
            return [('id', None, other.get_id())]
        if other is None:
            return [('id', this.get_id(), None)]
        return this.get_diff(other)


class PlanetEntry(TurnEntry):
        def get_id(self):
            return self.get('pid')


class Planet(BaseModel):
    headers = ['pid', 'name', 'size', 'focus', 'sid', 'owned', 'owner', 'visibility', 'species']
    section = 'planets'
    entry_class = PlanetEntry


class FleetEntry(TurnEntry):
    def get_id(self):
        return self.get('fid')


class Fleet(BaseModel):
    headers = ['fid', 'name', 'sid', 'owner', 'visibility', 'ships', 'target']
    section = 'fleets'
    entry_class = FleetEntry


class OrderEntry(TurnEntry):
    def get_id(self,):
        return self.get('id')

class Orders(BaseModel):
    headers = ['name', 'args']
    section = 'orders'
    entry_class = OrderEntry


class ResearchEntry(TurnEntry):
    def get_id(self):
        return self.get('name')

class Research(BaseModel):
    headers = ['name', 'category', 'allocation', 'cost', 'turn_left', 'type']
    section = 'research'
    entry_class = ResearchEntry


class Game(object):
    def __init__(self, game_id):
        self.game_id = game_id
        self.empire_id, creation_date, self.name = game_id.split('_', 2)
        self.creation_date = date_from_id(creation_date)
        self.branches = Orders.find_branches(game_id)
