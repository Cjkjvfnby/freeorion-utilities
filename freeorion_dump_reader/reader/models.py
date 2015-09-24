import json
import os
from django.conf import settings
from django.http import Http404
from reader.plotters import BasePlotter, PlanetsPlotter, FleetsPlotter, OrdersPlotter, ResearchPlotter, SystemPlotter
from reader.tools import date_from_id


_CACHE = {}


class LineEntry(object):
    """
    Generate html entry for single line
    """

    def process_args(self, value):
        return ', '.join(('<small><i>%s=</i></small>%s' % (k, v) for k, v in value.items()))

    def process_list(self, value):
        return ', '.join(str(x) for x in value)

    def process_target(self, value):
        if not value:
            return 'no mission'
        mission_type, target_id, target_type, target_name = value
        if mission_type == 'None':
            return "mission with out targets"
        return "%s: %s %s(%s)" % (mission_type, target_type, target_name, target_id)

    def process_focus(self, value):
        return value[6:].lower().capitalize()

    def process_species(self, value):
        return value[3:].lower().capitalize()

    def process_owned(self, value):
        return value and 'Yes' or 'No'

    def process_coords(self, value):
        return ', '.join('%.0f' % x for x in value)

    def process_last_battle(self, value):
        return value if value != -65535 else ''

    def process_owner(self, value):
        if value == -1:
            return 'monster'
        elif int(self.turn.empire_id) == value:
            return 'me'
        else:
            return value

    def __init__(self, name, item, turn):
        self.turn = turn
        self.VALUE_METHOD_MAP = {}
        self.VALUE_PROCESS_MAP = {'args': self.process_args,
                                  'ships': self.process_list,
                                  'neighbors': self.process_list,
                                  'tags': self.process_list,
                                  'owner_tags': self.process_list,
                                  'planets': self.process_list,
                                  'target': self.process_target,
                                  'focus': self.process_focus ,
                                  'species': self.process_species,
                                  'owned': self.process_owned,
                                  'coords': self.process_coords,
                                  'last_battle': self.process_last_battle,
                                  'owner': self.process_owner,
                                  }


        self.header = name
        self.classes = self.get_classes(item)
        self.html = self.get_html(item)

    def get_classes(self, item):
        return self.header

    def get_html(self, item):
        template = u'''<td class="{}">{}</td>'''

        value = item.get(self.header)
        if value is None:
            return template.format(self.header, '')

        if self.header in self.VALUE_METHOD_MAP:
            return template.format(self.header, self.VALUE_METHOD_MAP[self.header](item))
        else:
            if self.header in self.VALUE_PROCESS_MAP:
                return template.format(self.header, self.VALUE_PROCESS_MAP[self.header](value))
        return template.format(self.header, value)


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


class TurnSectionCollection(object):
    section = None
    headers = None
    entry_class = None
    plotter_class = BasePlotter
    summary_template_name = 'summary.html'

    @classmethod
    def get_plotter(cls, game):
        return cls.plotter_class(game, cls.section)

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
        if start is None:
            start = 1
        else:
            start = max(start and int(start) or 1, 1)
        if end is None:
            end = len(result)
        else:
            end = min(end and int(end) or len(result), len(result))
        return result[::-1][start-1:end]

    @classmethod
    def get_summary(cls, game, turn, start, end):
        cls.get_branch(game, turn, start, end)

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
                self.columns[-1].append(LineEntry(key, item, self))

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


class Planet(TurnSectionCollection):
    headers = ['pid', 'name', 'size', 'focus', 'sid', 'owned', 'owner', 'visibility', 'species']
    section = 'planets'
    entry_class = PlanetEntry
    plotter_class = PlanetsPlotter


class SystemEntry(TurnEntry):
        def get_id(self):
            return self.get('sid')


class System(TurnSectionCollection):
    headers = ['sid', 'name', 'star', 'planets', 'visibility', 'neighbors', 'tags', 'coords', 'last_battle', 'owner_tags']
    section = 'systems'
    entry_class = SystemEntry
    plotter_class = SystemPlotter
    summary_template_name = 'systems_summary.html'

    @classmethod
    def get_summary(cls, game, turn, start, end):
        result = {'points': [], 'starlanes': set()}
        data = cls.get_branch(game, turn, start, end)[-1]  # last turn
        sid_map = {s['sid']: s for s in data.data}
        for info in data.data:
            for x in info['neighbors']:
                result['starlanes'].add(tuple(sorted((x, info['sid']))))
            result['points'].append(info)
        result['starlanes'] = [[sid_map[a]['coords'], sid_map[b]['coords']] for a, b in result['starlanes']]
        return result


class FleetEntry(TurnEntry):
    def get_id(self):
        return self.get('fid')


class Fleet(TurnSectionCollection):
    headers = ['fid', 'name', 'sid', 'owner', 'visibility', 'ships', 'target']
    section = 'fleets'
    entry_class = FleetEntry
    plotter_class = FleetsPlotter


class OrderEntry(TurnEntry):
    def get_id(self,):
        return self.get('id')


class Orders(TurnSectionCollection):
    headers = ['name', 'args']
    section = 'orders'
    entry_class = OrderEntry
    plotter_class = OrdersPlotter


class ResearchEntry(TurnEntry):
    def get_id(self):
        return self.get('name')


class Research(TurnSectionCollection):
    headers = ['name', 'category', 'allocation', 'cost', 'turn_left', 'type']
    section = 'research'
    entry_class = ResearchEntry
    summary_template_name = 'research_summary.html'
    plotter_class = ResearchPlotter

    @classmethod
    def get_summary(cls, game, turn, start, end):
        turns = cls.get_branch(game, turn, start, end)
        result = []
        research_in_progress = set()
        for turn in turns:
            in_progress = set(x[0][1] for x in turn.columns)
            finished_this_turn = research_in_progress - in_progress
            added_this_turn = in_progress - research_in_progress
            result.append((turn.turn, finished_this_turn, added_this_turn))
            research_in_progress = in_progress
        return [x for x in result if any(x[1:])]


class Game(object):
    def __init__(self, game_id):
        self.game_id = game_id
        self.empire_id, creation_date, self.name = game_id.split('_', 2)
        self.creation_date = date_from_id(creation_date)
        self.branches = Orders.find_branches(game_id)
