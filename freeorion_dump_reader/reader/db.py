import json
import os
from dump_reader import settings
import reader
from reader.tools import date_from_id

SECTIONS = ['systems', 'planets', 'fleets', 'orders', 'research']


def get_model_class(name):
    for attr_name in dir(reader.models):
        attr = getattr(reader.models, attr_name)
        if isinstance(attr, type) and getattr(attr, 'section') == name:
            return attr
    raise Exception('Model %s not found' % name)


class Game(object):
    def __init__(self, game_id):
        self.game_id = game_id
        self.empire_id, creation_date, self.name = game_id.split('_', 2)
        self.creation_date = date_from_id(creation_date)

    def branches(self):
        return db.get_branch_end(self.game_id)


class Database(dict):
    def __init__(self):
        self.__turn_cache = {}
        self.__branches_ends = {}
        self.__branch_lines = {}
        self.__games = tuple(
            sorted([Game(game_id) for game_id in os.listdir(settings.DUMP_FOLDER)],
                   key=lambda x: x.creation_date, reverse=True)
        )

        for game in self.__games:
            for section in SECTIONS:
                file_path = os.path.join(settings.DUMP_FOLDER, game.game_id, section)
                if not os.path.exists(file_path):
                    raise Exception("Path is missed %s" % file_path)
                with open(file_path) as f:
                    all_turns = []
                    for line in f:
                        line = line.strip('\n\r')
                        header, items = json.loads(line)
                        key = (game.game_id, section, header['turn_id'])
                        self.__turn_cache[key] = header, items
                        all_turns.append(header)
                # add only once on last section
                linked = set(x['parent_id'] for x in all_turns)
                self.__branches_ends[game.game_id] = tuple(x for x in all_turns if x['turn_id'] not in linked)

                for game_id, branches in self.__branches_ends.items():
                    for branch_end in branches:
                        branch_line = [branch_end]
                        while True:
                            key = game_id, SECTIONS[0], branch_line[-1]['parent_id']
                            # Stop if first turn or there is not data for previous turns
                            if key not in self.__turn_cache:
                                break
                            branch_line.append(self.__turn_cache[key][0])
                        branch_line.reverse()
                        self.__branch_lines.setdefault((game_id, section), {})['turn_id'] = tuple(branch_line)


    @staticmethod
    def get_line(lines, turn_id):
        for line in lines:
            line_iterator = reversed(line)
            for item in line_iterator:
                if item['turn_id'] == turn_id:
                    res = list(line_iterator)[::-1]
                    res.append(item)
                    return res
        raise Exception('Turn not found')

    def get_branch(self, game_id, section, branch_end, start, end):
        branch_lines = self.__branch_lines[game_id, section]
        if branch_end in branch_lines:
            branch_line = branch_lines[branch_end]
        else:
            branch_line = self.get_line(branch_lines.itervalues(), branch_end)

        if start is None:
            start = 1
        else:
            start = max(start and int(start) or 1, 1)
        if end is None:
            end = len(branch_line)
        else:
            end = min(end and int(end) or len(branch_line), len(branch_line))
        return branch_line[start-1:end]

    def get_games(self):
        return self.__games

    def get_branch_end(self, game_id):
        return self.__branches_ends[game_id]

    def get_turn(self, game_id, section, turn_id):
        return self.__turn_cache[(game_id, section, turn_id)]


db = Database()

