import json
import os
from django.conf import settings
from django.http import Http404
from reader.tools import date_from_uid


_CACHE = {}


class BaseModel(object):
    section = None

    @classmethod
    def get_turns(cls, game, turn):
        section_info = cls.load_game_section(game)
        if turn not in section_info:
            raise Http404('Cant find proper turn: %s' % turn)
        last = section_info[turn]
        turns = [last]
        while last.parent in section_info:
            last = section_info[last.parent]
            turns.append(last)
        return turns[::-1]

    @classmethod
    def find_branches(cls, game):
        turn_infos = cls.load_game_section(game).values()
        linked = set(x.parent for x in turn_infos)
        return [x for x in turn_infos if x.uid not in linked]

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
                    data[turn_info.uid] = turn_info
            _CACHE[key] = data
        return _CACHE[key]

    @classmethod
    def get_branch(cls, game, turn, start, end):
        turns = cls.load_game_section(game)
        result = [turns[turn]]
        while result[-1].parent in turns:
            result.append(turns[result[-1].parent])
        start = start and int(start) or 1
        end = end and int(end) or len(result)
        return result[::-1][start-1:end]

    def __init__(self, game, input_data):
        """
        Convention first name in header is all ways unique key for item!!!
        """
        self.turn_info, self.data = input_data
        self.headers = self.turn_info.pop('headers')
        self.headers.remove('id')
        self.turn = self.turn_info['turn']
        self.uid = self.turn_info['turn_uid']
        self.parent = self.turn_info['parent_uid']
        empire_id, _, empire_name = game.split('_', 2)
        self.empire_id = empire_id
        self.empire_name = empire_name
        self.columns = []
        for item in self.data:
            self.columns.append([])
            for key in self.headers:
                self.columns[-1].append((key, item.get(key)))

    def get_date(self):
        return date_from_uid(self.uid)

    def __repr__(self):
        return "%s %s" % (self.section, self.uid)

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
        data1 = {x['id']: x for x in self.data}
        data2 = {x['id']: x for x in other.data}
        keys = set(data1.keys() + data2.keys())
        difference = []
        for key in sorted(keys):
            diff = self._compare_items(data1.get(key), data2.get(key))
            if diff:
                difference.append(diff)
        return difference

    @staticmethod
    def _compare_items(this, other):
        """
        Return list of 3 item tuples if have any differences
        In that case first tuple is unique key
        if not differences None returned.
        """
        if this is None:
            this = {}
        if other is None:
            other = {}
        keys = set(this.keys() + other.keys())

        this_id = this.get('id')
        other_id = other.get('id')
        if this_id and other_id:
            assert this_id == other_id, 'Cant make diff for different objects'
        diff = [('id', this_id, other_id)]
        for key in keys:
            this_value = this.get(key)
            other_value = other.get(key)
            if this_value != other_value:
                diff.append((key, this_value, other_value))
        if len(diff) == 1:  # only header
            return None
        return diff


class Planet(BaseModel):
    section = 'planets'


class Fleet(BaseModel):
    section = 'fleets'


class Orders(BaseModel):
    section = 'orders'


class Research(BaseModel):
    section = 'research'

def get_game(game):
    empire_id, creation_date, empire_name = game.split('_', 2)
    creation_date = date_from_uid(creation_date)
    return empire_name, creation_date, game, Orders.find_branches(game)

def get_games():
    games = []
    for path in os.listdir(settings.DUMP_FOLDER):
        games.append(get_game(path))
    return games


