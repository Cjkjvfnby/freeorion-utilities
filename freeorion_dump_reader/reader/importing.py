import json
import os

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import HttpResponseRedirect
from reader.models import Turn, Planet, Game, System, ResearchInfo, Research, Fleet, FleetTarget, Empire, ShipDesign, \
    Ship, Order, Part, Hull, Building, Branch, ShipDesignInfo
from django.views.generic import TemplateView, View
from django.conf import settings
from reader.tools import date_from_id

dead_fleets = set()
dead_ships = set()


class ImportListView(TemplateView):
    template_name = "reader/import.html"

    def get_context_data(self, **kwargs):
        context = super(ImportListView, self).get_context_data(**kwargs)

        def is_dump(path):
            # TODO add check for name style
            return os.path.isdir(os.path.join(settings.DUMP_FOLDER, path))

        games = sorted(
            [os.path.join(settings.DUMP_FOLDER, path) for path in os.listdir(settings.DUMP_FOLDER) if is_dump(path)],
            key=os.path.getctime, reverse=True)

        ids = [os.path.basename(path) for path in games]
        present = Game.objects.all().in_bulk(ids)
        context['games'] = [(game_id, game_id in present, path) for game_id, path in zip(ids, games)]
        return context


def process_file(processor, game, folder, name=None):
    name = name or processor.__name__
    name = os.path.join(folder, name)
    with open(name) as f:
        for line in f:
            data, items = json.loads(line)
            turn, _ = Turn.objects.get_or_create(turn=data['turn'],
                                                 turn_id=data['turn_id'],
                                                 parent_id=data['parent_id'],
                                                 game=game)

            processor(game, turn, items)


def research_info(game, turn, items):
    for item in items:
        ResearchInfo.objects.get_or_create(game=game,
                                           type=item['type'],
                                           category=item['category'],
                                           name=item['name'],
                                           cost=item['cost'])


def empire_info(game, turn, items):
    for item in items:
        rgb = '#%02X%02X%02X' % tuple(item.pop('rgba'))[:-1]
        this_empire = item.pop('current_empire')
        Empire.objects.get_or_create(game=game,
                                     rgb=rgb,
                                     is_me=this_empire == item['empire_id'],
                                     **item)
    # Fake empire to hold monster and rebel fleets
    Empire(game=game,
           rgb='#FF0000',
           is_me=False,
           empire_id=-1,
           name='Monsters and rebels').save()


def research(game, turn, items):
    for item in items:
        name = item.pop('name')
        ri = ResearchInfo.objects.get(name=name, game=game)
        Research.objects.get_or_create(turn=turn, research_info=ri, **item)


def system(game, turn, items):
    neighbors_dict = {}
    systems = {}
    for item in items:
        neighbors_dict[item['sid']] = item.pop('neighbors')
        system, _ = System.objects.get_or_create(turn=turn, **item)
        systems[item['sid']] = system
    for sid, neighbors in neighbors_dict.items():
        for neighbor in neighbors:
            systems[sid].neighbors.add(systems[neighbor])


def planet(game, turn, items):
    for item in items:
        item['sid'] = System.objects.get(turn=turn, sid=item['sid'])
        owner = item.pop('owner', None)
        if owner:
            item['empire'] = Empire.objects.get(game=game, empire_id=owner)
        Planet.objects.get_or_create(turn=turn, **item)


def fleet(game, turn, items):
    dead_fleets = set()
    for item in items:
        target = item.pop('target', None)
        sid = item.pop('sid')
        owner = item.pop('owner', -1)
        # dont load destroyed fleet more then once
        fid = item['fid']
        if item['is_destroyed']:
            if fid in dead_fleets:
                continue
            else:
                dead_fleets.add(fid)
        item['empire'] = Empire.objects.get(game=game, empire_id=owner)
        if sid != -1:
            item['system'] = System.objects.get(turn=turn, sid=sid)

        fleet, _ = Fleet.objects.get_or_create(turn=turn, **item)
        if target:
            mission_type, target_id, target_type, target_name = target
            FleetTarget.objects.get_or_create(fleet=fleet, mission_type=mission_type,
                                              target_id=target_id, target_type=target_type, target_name=target_name
                                              )
def design_info(game, turn, items):
    for item in items:
        item['parts'] = ''.join(map(str, item['parts']))
        ShipDesignInfo.objects.get_or_create(game=game, **item)


def design(game, turn, items):
    for item in items:
        item['attack_stats'] = ''.join(map(str, item['attack_stats']))
        did = item.pop('did')
        info = ShipDesignInfo.objects.get(game=game, did=did)
        ShipDesign.objects.get_or_create(turn=turn, design_info=info, **item)


def ship(game, turn, items):
    for item in items:
        # dont load destroyed ships more then once
        shid = item['shid']
        if item['is_destroyed']:
            if shid in dead_ships:
                continue
            else:
                dead_ships.add(shid)
        fleet_id = item.pop('fleet_id')
        fleet = Fleet.objects.get(turn=turn, fid=fleet_id)
        try:
            item['design'] = ShipDesign.objects.get(turn=turn, design_info__did=item.pop('design_id'))

        except ObjectDoesNotExist:
            pass
        Ship.objects.get_or_create(fleet=fleet, **item)


def order(game, turn, items):
    for item in items:
        Order.objects.get_or_create(turn=turn, **item)


def process_turn(game, folder, name=None):
    name = 'turn'
    name = os.path.join(folder, name)
    with open(name) as f:
        for line in f:
            data, items = json.loads(line)
            item = items[0]
            parts = item.pop('parts')
            hulls = item.pop('hulls')
            buildings = item.pop('buildings')
            turn, created = Turn.objects.get_or_create(turn=data['turn'],
                                                       turn_id=data['turn_id'],
                                                       parent_id=data['parent_id'],
                                                       game=game,
                                                       **item
                                                       )
            # do it only once
            if created:
                for collection, model, field in (
                        (parts, Part, turn.parts),
                        (hulls, Hull, turn.hulls),
                        (buildings, Building, turn.buildings)
                ):
                    field.add(*[model.objects.get_or_create(name=name)[0] for name in collection])


def get_ends(game):
        turns = game.turns.all()
        linked = set(x.parent_id for x in turns)
        return (x for x in turns if x.turn_id not in linked)


def get_branch(game, turn):
    all_turns = Turn.objects.filter(turn__lte=turn.turn, game=game).order_by('-turn')
    branch = [turn]
    next_turn = turn.parent_id
    for item in all_turns:
        if item.turn_id == next_turn:
            branch.append(item)
            next_turn = item.parent_id
    return reversed(branch)


class ImportView(View):
    @transaction.atomic
    def post(self, request):
        folder = request.POST['path']
        game_id = os.path.basename(folder)
        empire_id, creation_date, name = game_id.split('_', 2)

        game, _ = Game.objects.get_or_create(
            game_id=game_id,
            creation_date=date_from_id(creation_date))
        process_turn(game, folder)

        Branch.objects.filter(turns__game=game).delete()

        for end in get_ends(game):
            branch = Branch(turn=end)
            branch.save()
            branch.turns.add(*get_branch(game, end))

        processors = (
            research_info,
            design_info,
            empire_info,
            research,
            system,
            planet,
            design,
            fleet,
            ship,
            order,
        )

        for processor in processors:
            process_file(processor, game, folder)

        return HttpResponseRedirect('/')
