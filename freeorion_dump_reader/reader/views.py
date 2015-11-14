import json
import os
from django.db import transaction
from django.http import HttpResponseRedirect
from reader.models import Turn, Planet, Game, System, ResearchInfo, Research

from django.views.generic import TemplateView, ListView, View
from django.conf import settings
from reader.tools import date_from_id


class GameListView(ListView):
    model = Game


class ImportListView(TemplateView):
    template_name = "reader/import.html"

    def get_context_data(self, **kwargs):
        context = super(ImportListView, self).get_context_data(**kwargs)
        def is_dump(path):
            # TODO add check for name style
            return os.path.isdir(os.path.join(settings.DUMP_FOLDER, path))

        games = sorted([os.path.join(settings.DUMP_FOLDER, path) for path in os.listdir(settings.DUMP_FOLDER) if is_dump(path)],
                       key=os.path.getctime, reverse=True)

        ids = [os.path.basename(path) for path in games]
        present = Game.objects.all().in_bulk(ids)
        context['games'] = [(game_id, game_id in present, path) for game_id, path in zip(ids, games)]
        return context


def process_file(processor, game, name):
    with open(name) as f:
        for line in f:
            data, items = json.loads(line)
            turn, _ = Turn.objects.get_or_create(turn=data['turn'],
                                                 turn_id=data['turn_id'],
                                                 parent_id=data['parent_id'],
                                                 game=game)

            processor(game, turn, items)


def process_research_info(game, turn, items):
    item = items[0]
    ResearchInfo.objects.get_or_create(game=game,
                                       type=item['type'],
                                       category=item['category'],
                                       name=item['name'],
                                       cost=item['cost'])


def process_research(game, turn, items):
    for item in items:
        name = item.pop('name')
        ri = ResearchInfo.objects.get(name=name, game=game)
        Research.objects.get_or_create(turn=turn, research_info=ri, **item)


def process_systems(game, turn, items):
    neighbors_dict = {}
    systems = {}
    for item in items:
        neighbors_dict[item['sid']] = item.pop('neighbors')
        system, _ = System.objects.get_or_create(turn=turn, **item)
        systems[item['sid']] = system
    for sid, neighbors in neighbors_dict.items():
        for neighbor in neighbors:
            systems[sid].neighbors.add(systems[neighbor])


def process_planets(game, turn, items):
    for item in items:
        item['sid'] = System.objects.get(turn=turn, sid=item['sid'])
        Planet.objects.get_or_create(turn=turn, **item)


class ImportView(View):
    @transaction.atomic
    def post(self, request):
        folder = request.POST['path']
        game_id = os.path.basename(folder)
        empire_id, creation_date, name = game_id.split('_', 2)

        game, _ = Game.objects.get_or_create(
            game_id=game_id,
            empire_name=name,
            empire_id=empire_id,
            creation_date=date_from_id(creation_date))

        process_file(process_research_info, game, os.path.join(folder, 'research_info'))
        process_file(process_research, game, os.path.join(folder, 'research'))
        process_file(process_systems, game, os.path.join(folder, 'system'))
        process_file(process_planets, game, os.path.join(folder, 'planet'))

        return HttpResponseRedirect('/')
