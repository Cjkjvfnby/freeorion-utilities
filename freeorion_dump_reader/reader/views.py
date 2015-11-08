import json
import os
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import ContextMixin

from reader.models import Turn, Planet, Game

from django.views.generic import TemplateView, FormView, ListView, View
from django.conf import settings

from django import forms
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

        context['games'] = [(os.path.basename(x), x) for x in games]
        return context


class ImportView(View):
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        folder = request.POST['path']
        game_id = os.path.basename(folder)

        empire_id, creation_date, name = game_id.split('_', 2)

        game, _ = Game.objects.get_or_create(
            game_id=game_id,
            empire_name=name,
            empire_id=empire_id,
            creation_date=date_from_id(creation_date))

        with open(os.path.join(folder, 'planets')) as f:
            for line in f:
                data, items = json.loads(line)
                turn, _ = Turn.objects.get_or_create(turn=data['turn'],
                                                     parent_id=data['parent_id'],
                                                     turn_id=data['turn_id'],
                                                     game=game)
                for item in items:
                    Planet.objects.get_or_create(turn=turn, **item)
        return HttpResponseRedirect('/')








#
#


