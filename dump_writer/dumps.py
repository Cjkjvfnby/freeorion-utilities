import os
from subprocess import PIPE, Popen
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
        turn_dumps.setdefault(fo.currentTurn(), []).append(
            (function.__name__[5:-5], dict(zip(params[function.__name__], args))))
        return function(*args)

    return wrapper


for name in dir(fo):
    if name.startswith('issue') and name.endswith('Order'):
        setattr(fo, name, dump_order(getattr(fo, name)))

uid_time_format = '%y-%m-%d_%H-%M-%S%f'


class Dumper(object):
    """
    Base dump class.
    You need to implement two methods:
     - `get_items` return list of any items
     - `construct_item` applied to each item in `get_items` list and convert it to dict.
    and set 'NAME'

    As result you will have folder named as game.
    File named as `NAME`
    Each line in file represent turn dump in json format: [{<turn indfo>}, [<item>, ...]]
    """
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
        self._dump(self.NAME, kwargs, result)


class DumpSystems(Dumper):
    NAME = 'system'

    def get_items(self):
        empire = fo.getEmpire()
        self.explored_systems = frozenset(empire.exploredSystemIDs)
        self.suppliable_systems = frozenset(empire.fleetSupplyableSystemIDs)
        self.capital = empire.capitalID
        return fo.getUniverse().systemIDs

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
            'visibility': str(universe.getVisibility(sid, fo.empireID())),
            'neighbors': list(universe.getImmediateNeighbors(sid, fo.empireID())),
            'tags': list(system.tags),
            'coords': (system.x, system.y),
            'last_battle': system.lastTurnBattleHere,
            'owner_tags': list(owner_tags),
            'supplied': sid in self.suppliable_systems,
            'explored': sid in self.explored_systems,
            'is_capital': sid == self.capital,
        }
        return data


class DumpPlanets(Dumper):
    NAME = 'planet'

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


class DumpShips(Dumper):
    NAME = 'ship'

    def get_items(self):
        universe = fo.getUniverse()
        self.destroyed = set(universe.destroyedObjectIDs(fo.getEmpire().empireID))
        return universe.shipIDs

    def construct_item(self, shid):
        universe = fo.getUniverse()
        ship = universe.getShip(shid)

        data = {
            'shid': shid,
            'fleet_id': ship.fleetID,
            'name': ship.name,
            'species': ship.speciesName,
            'speed': ship.speed,
            'age_in_turns': ship.ageInTurns,
            'is_monster': ship.isMonster,
            'is_armed': ship.isArmed,
            'can_colonize': ship.canColonize,
            'can_invade': ship.canInvade,
            'can_bombard': ship.canBombard,
            'design_id': ship.designID,
            'colonizing_planet': ship.orderedColonizePlanet,
            'invading_planet': ship.orderedInvadePlanet,
            'is_scrapping': ship.orderedScrapped,
            'is_destroyed': shid in self.destroyed
        }
        return data


class DumpShipDesignInfo(Dumper):
    """
    Dumps static information about design. This does not changed during turn.
    """

    NAME = 'design_info'

    def get_items(self):
        empire = fo.getEmpire()
        # TODO add monster designs too
        designs = [fo.getShipDesign(did) for did in empire.availableShipDesigns]
        return [design for design in designs if self.turn == design.designedOnTurn or self.turn == 1]

    def construct_item(self, design):
        data = {
            'did': design.id,
            'name': design.name(False),
            'parts': list(design.parts),
            'description_key': design.description(False),
            'designed_on_turn': design.designedOnTurn,
            'structure': design.structure,
            'shields': design.shields,
            'speed': design.speed,
            'hull': design.hull,
            'defense': design.defense,
        }
        return data


class DumpShipDesign(Dumper):
    """
    Dumps information about design that can be changed during turns.
    """

    NAME = 'design'

    def get_items(self):
        empire = fo.getEmpire()
        # TODO add monster designs too
        return empire.availableShipDesigns

    def construct_item(self, did):
        design = fo.getShipDesign(did)
        data = {
            'did': did,
            'attack_stats': list(design.attackStats)
        }
        return data


class DumpFleet(Dumper):
    NAME = 'fleet'

    def get_items(self):
        universe = fo.getUniverse()
        self.destroyed = set(universe.destroyedObjectIDs(fo.getEmpire().empireID))
        return set(universe.fleetIDs)

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
            'is_destroyed': fid in self.destroyed
        }
        if mission and mission.target:
            obj = mission.target.get_object()
            name = obj and obj.name or 'unknown'
            data['target'] = [AIFleetMissionType.name(mission.type), mission.target.id,
                              mission.target.object_name, name]
        return data


class DumpTurn(Dumper):
    NAME = 'turn'

    def get_items(self):
        empire = fo.getEmpire()
        stats = {
            'buildings': list(empire.availableBuildingTypes),
            'hulls': list(empire.availableShipHulls),
            'parts': list(empire.availableShipParts),
            'population': empire.population(),
            'production': empire.productionPoints,
        }
        return [stats]

    def construct_item(self, item):
        return item


class DumpOrders(Dumper):
    NAME = 'order'

    def get_items(self):
        turn = fo.currentTurn()
        return turn_dumps.get(turn, [])

    def construct_item(self, order_pairs):
        name, args = order_pairs
        return {
            'name': name,
            'args': args
        }


class DumpResearch(Dumper):
    NAME = 'research'

    def get_items(self):
        return [element for element in fo.getEmpire().researchQueue]

    def construct_item(self, element):
        tech = fo.getTech(element.tech)
        return {
            'name': tech.name,
            'allocation': element.allocation,
            'turn_left': element.turnsLeft
        }


class DumpResearchInfo(Dumper):
    """
    Dump research tree information once per game.
    """
    NAME = 'research_info'

    def construct_item(self, item):
        tech = fo.getTech(item)
        return {
            'category': tech.category,
            'type': tech.type.name,
            'name': tech.name,
            'cost': tech.researchCost(fo.empireID()),
        }

    def get_items(self):
        return list(fo.techs())

    def _dump(self, section, common_info, item_list):
        file_path = os.path.join(self.game_folder, section)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write(json.dumps([common_info, item_list]))
                f.write('\n')


class DumpEmpireInfo(Dumper):
    """
    Dump empire information once per game.
    """
    NAME = 'empire_info'

    def construct_item(self, item):
        empire = fo.getEmpire(item)

        color = empire.colour
        return {
            'empire_id': empire.empireID,
            'name': empire.name,
            'rgba': (color.r, color.g, color.b, color.a),
            'current_empire': fo.getEmpire().empireID
        }

    def get_items(self):
        return list(fo.allEmpireIDs())

    def _dump(self, section, common_info, item_list):
        file_path = os.path.join(self.game_folder, section)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
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
    for cls in (DumpPlanets, DumpFleet, DumpOrders, DumpResearch,
                DumpSystems, DumpResearchInfo, DumpEmpireInfo, DumpShips,
                DumpShipDesign, DumpTurn, DumpShipDesignInfo):
        cls(uniq_key).dump(**data)


from freeorion_debug.listeners import register_post_handler

register_post_handler('generateOrders', dump_data)

print "You can find dumps in %s" % os.path.join(os.path.dirname(__file__), 'dumps')


# TODO list
# 'production_queue': empire.productionQueue,
# 'research_queue': empire.researchQueue,
# add supply ranges to system
