import os
import sys
import json
from EnumsAI import AIFleetMissionType
sys.path.append('c:/Python27/Lib/site-packages/')

import freeOrionAIInterface as fo
import FreeOrionAI as foAI

'''
===================
Hack to dump orders
===================
'''

# dump for issue orders
turn_dumps = {}

params = {
  'issueScrapOrder': ['object id'],
  'issueAggressionOrder': ['fid', 'aggressive'],
  'issueBombardOrder': ['?', '?'],
  'issueChangeFocusOrder': ['pid', 'focus'],
  'issueChangeProductionQuantityOrder': ['queue index', 'new quantity', 'new blocksize'],
  'issueColonizeOrder': ['sid', 'pid'],
  'issueCreateShipDesignOrder': ['name', 'description', 'hull', 'partlist', 'icon', 'model', 'has translation'],
  'issueDequeueProductionOrder': ['queue index'],
  'issueDequeueTechOrder': ['tech'],
  'issueEnqueueBuildingProductionOrder': ['building', 'pid'],
  'issueEnqueueShipProductionOrder': ['ship', 'location'],
  'issueEnqueueTechOrder': ['tech', 'queue index'],
  'issueFleetMoveOrder': ['fid', 'sid'],
  'issueFleetTransferOrder': ['sid', 'fid'],
  'issueGiveObjectToEmpireOrder': ['?', '?'],
  'issueInvadeOrder': ['sid', 'pid'],
  'issueNewFleetOrder': ['name', 'sid'],
  'issueRenameOrder': ['object id', 'name'],
  'issueRequeueProductionOrder': ['old position', 'new position'],
}


def dump_order(function):
    def wrapper(*args):
        turn_dumps.setdefault(fo.currentTurn(), []).append((function.__name__[5:-5], dict(zip(params[function.__name__], args))))
        return function(*args)
    return wrapper

for name in dir(fo):
    if name.startswith('issue') and name.endswith('Order'):
        setattr(fo, name, dump_order(getattr(fo, name)))


uid_time_format = '%y-%m-%d_%H-%M-%S%f'


class Dumper(object):
    NAME = None

    def __init__(self, uid):
        current_folder = os.path.dirname(__file__)
        dums_path = os.path.join(current_folder, 'dumps')
        if not os.path.exists(dums_path):
            os.mkdir(dums_path)
        game_folder = os.path.join(dums_path, str(uid))
        if not os.path.exists(game_folder):
            os.mkdir(game_folder)
        self.game_folder = game_folder

    def get_items(self):
        raise NotImplementedError()

    def construct_item(self, item):
        raise NotImplementedError()

    def sort(self, collection):
        raise NotImplementedError('Implement in children.')

    def _dump(self, section, common_info, item_list):
        """
        Add serialized values to file.
        """
        file_path = os.path.join(self.game_folder, section)
        with open(file_path, 'a') as f:
            f.write(json.dumps([common_info, item_list]))
            f.write('\n')

    def dump(self, **kwargs):
        self.turn = kwargs['turn']
        result = []
        for item in self.get_items():
            data = self.construct_item(item)
            result.append(data)
        self.sort(result)
        self._dump(self.NAME, kwargs, result)


class DumpSystems(Dumper):
    NAME = 'systems'

    def get_items(self):
        return fo.getUniverse().systemIDs

    def sort(self, collection):
        collection.sort(key=lambda x: x['sid'])

    def construct_item(self, sid):
        universe = fo.getUniverse()

        system = universe.getSystem(sid)

        owners = set()
        for pid in system.planetIDs:
            planet = universe.getPlanet(pid)
            owners.add(planet.owner)

        owner_tags = set()
        for owner in owners:
            if owner == fo.getEmpire().empireID:
                owner_tags.add('owned')
            elif owner == -1:
                continue
            else:
                owner_tags.add('enemies')
        if system in foAI.foAIstate.unexploredSystemIDs:
            owner_tags.add('unexplored')

        data = {
            'sid': sid,
            'name': system.name,
            'star': system.starType.name,
            'planets': list(system.planetIDs),
            'visibility': str(universe.getVisibility(sid, fo.empireID())),
            'neighbors': list(universe.getImmediateNeighbors(sid, fo.empireID())),
            'tags': list(system.tags),
            'coords': (system.x, system.y),
            'last_battle': system.lastTurnBattleHere,
            'owner_tags': list(owner_tags)
        }
        return data

class DumpPlanets(Dumper):
    NAME = 'planets'

    def sort(self, collection):
        collection.sort(key=lambda x: x['pid'])
        collection.sort(key=lambda x: x['sid'])

    def get_items(self):
        return fo.getUniverse().planetIDs

    def construct_item(self, pid):
        universe = fo.getUniverse()
        planet = universe.getPlanet(pid)
        data = {
            'pid': pid,
            'name': planet.name,
            'size': planet.size.name,
            'focus': planet.focus,
            'sid': planet.systemID,
            'owned': not planet.unowned,
            'owner': planet.owner if planet.owner != -1 else None,
            'species': planet.speciesName,
            'visibility': str(universe.getVisibility(pid, fo.empireID())),
        }
        return data


class DumpFleet(Dumper):
    NAME = 'fleets'

    def sort(self, collection):
        collection.sort(key=lambda x: x['fid'])

    def get_items(self):
        universe = fo.getUniverse()
        return set(universe.fleetIDs) - set(universe.destroyedObjectIDs(fo.getEmpire().empireID))

    def construct_item(self, fid):
        universe = fo.getUniverse()
        fleet = universe.getFleet(fid)
        mission = foAI.foAIstate.get_fleet_mission(fid)
        data = {
            'fid': fid,
            'name': fleet.name,
            'sid': fleet.systemID,
            'owner': fleet.owner,
            'visibility': str(universe.getVisibility(fid, fo.getEmpire().empireID)),
            'ships': list(fleet.shipIDs),
        }
        if mission and mission.target:

            obj = mission.target.get_object()
            name = obj and obj.name or 'unknown'
            data['target'] = [AIFleetMissionType.name(mission.type), mission.target.id,
                              mission.target.object_name, name]
        return data


class DumpOrders(Dumper):
    NAME = 'orders'

    def sort(self, collection):
        collection.sort(key=lambda x: x['id'])

    def get_items(self):
        turn = fo.currentTurn()
        turn_orders = turn_dumps.get(turn, [])
        return enumerate(turn_orders)

    def construct_item(self, order_pairs):
        i, (name, args) = order_pairs
        return {
            'id': '%s-%s' % (self.turn, i),
            'name': name,
            'args': args
        }

class DumpResearch(Dumper):
    NAME = 'research'

    def sort(self, collection):
        collection.sort(key=lambda x: x['name'])

    def get_items(self):
        return [element for element in fo.getEmpire().researchQueue]

    def construct_item(self, element):
        tech = fo.getTech(element.tech)
        return {
            'category': tech.category,
            'type': tech.type.name,
            'name': tech.name,
            'allocation': element.allocation,
            'cost': tech.researchCost(fo.empireID()),
            'turn_left': element.turnsLeft
        }

class DumpInfo(Dumper):
    """
    Dump various information once per game.
    """
    NAME = 'info'

    def sort(self, collection):
        pass

    def construct_item(self, item):
        return item

    def get_items(self):
        return [list(fo.techs())]

    def _dump(self, section, common_info, item_list):
        file_path = os.path.join(self.game_folder, section)
        if not os.path.exists(file_path):
            with open(file_path, 'a') as f:
                f.write(json.dumps([common_info, item_list]))
                f.write('\n')

def dump_data(result):
    empire = fo.getEmpire()
    uniq_key = '%s_%s_%s' % (empire.empireID, foAI.foAIstate.uid, empire.name.replace(' ', '_'))
    data = {
        'turn_id': foAI.foAIstate.get_current_turn_uid(),
        'parent_id': foAI.foAIstate.get_prev_turn_uid(),
        'turn': fo.currentTurn(),
    }
    for cls in (DumpPlanets, DumpFleet, DumpOrders, DumpResearch, DumpSystems, DumpInfo):
        cls(uniq_key).dump(**data)


from freeorion_debug.listeners import register_post_handler
register_post_handler('generateOrders', dump_data)
