import json
import os
from datetime import datetime
from django.http import Http404

DUMP_FOLDER = 'F:/projects/freeorion/default/AI/freeorion_debug/dumps'
_CACHE = {}


def get_games():
    games = []
    for x in os.listdir(DUMP_FOLDER):
        empire_id, creation_date, empire_name = x.split('_', 2)
        creation_date = datetime.fromtimestamp((int(creation_date, 16) / 1000) + 1433809768)  # revert from aistate
        games.append((empire_name, creation_date, x))
    return games


class TurnInfo(object):
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

    def __repr__(self):
        return "Turn info %s" % self.uid

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


def get_turns(game, turn, section):
    section_info = load_game_section(game, section)
    if turn not in section_info:
        raise Http404('Cant find proper turn: %s' % turn)
    last = section_info[turn]
    turns = [last]
    while last.parent in section_info:
        last = section_info[last.parent]
        turns.append(last)
    return turns[::-1]



def load_game_section(game, section):
    key = (game, section)
    if not key in _CACHE:
        file_path = os.path.join(DUMP_FOLDER, game, section)
        if not os.path.exists(file_path):
            raise Http404()
        data = {}
        with open(file_path) as f:
            for line in f:
                line = line.strip('\n\r')
                turn_info = TurnInfo(game, json.loads(line))
                data[turn_info.uid] = turn_info
        _CACHE[key] = data
    return _CACHE[key]
