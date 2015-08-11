import os
from django.conf import settings
import json
from django.http import Http404, HttpResponse
from django.views.generic import TemplateView

import reader.models
from reader.models import BaseModel, Game, Research

SECTIONS = ['systems', 'planets', 'fleets', 'orders', 'research']


def get_model_class(name):
    for attr_name in dir(reader.models):
        attr = getattr(reader.models, attr_name)
        if isinstance(attr, type) and issubclass(attr, BaseModel) and attr.section == name:
            return attr
    raise Exception('Model %s not found' % name)


class GamesList(TemplateView):
    template_name = "games.html"

    def get_context_data(self, **kwargs):
        kwargs['games'] = sorted(
            [Game(path) for path in os.listdir(settings.DUMP_FOLDER)],
            key=lambda x: x.creation_date,
            reverse=True)
        kwargs['sections'] = SECTIONS
        return super(GamesList, self).get_context_data(**kwargs)


class ResearchCompare(TemplateView):
    template_name = "research_compare.html"

    def get_context_data(self, **kwargs):
        games = [x.split('-') for x in self.request.GET.getlist('q[]')]
        branches = [Research.get_branch(game, turn, None, None) for game, turn in games]
        border = min(len(branch) for branch in branches)

        if self.request.GET.get('md'):
            self.template_name = 'research_compare.md'

        kwargs['game_count'] = len(branches)
        kwargs['border'] = border

        file_path = os.path.join(settings.DUMP_FOLDER, games[0][0], 'info')
        if not os.path.exists(file_path):
            raise Http404("Path is missed %s" % file_path)
        with open(file_path) as f:
            line = next(f).strip('\n\r')
            turn_info = json.loads(line)[1]
            all_techs = turn_info[0]
        tech_stats = {tech: [] for tech in all_techs}
        for turns in branches:
            in_progress = set()
            for turn in turns[:border]:
                names = set(x['name'] for x in turn.data)
                new = names - in_progress
                finished = in_progress - names
                in_progress.update(new)
                in_progress -= finished
                for tech in new:
                    tech_stats[tech].append({'started': turn.turn})
                for tech in finished:
                    tech_stats[tech][-1]['finished'] = turn.turn
        kwargs['stats'] = sorted(sorted(tech_stats.items()), key=lambda x: len(x[1]), reverse=True)
        return super(ResearchCompare, self).get_context_data(**kwargs)


class ModelTemplateView(TemplateView):
    def get_context_data(self, **kwargs):
        kwargs = super(ModelTemplateView, self).get_context_data(**kwargs)
        self.model = get_model_class(kwargs['section'])
        self.game = kwargs['game']
        kwargs['empire_id'] = Game(kwargs['game']).empire_id
        kwargs['sections'] = SECTIONS
        kwargs['start'] = self.request.GET.get('start')
        kwargs['end'] = self.request.GET.get('end')
        return self.get_data(**kwargs)


class SectionView(ModelTemplateView):
    template_name = "section.html"

    def get_data(self, **kwargs):
        kwargs['data'] = self.model.get_branch(self.game, kwargs['turn'],
                                               start=self.request.GET.get('start'),
                                               end=self.request.GET.get('end'))
        kwargs['branch'] = kwargs['data'][-1]
        return kwargs


class DiffView(ModelTemplateView):
    template_name = "diff.html"

    def get_data(self, **kwargs):
        turn_infos = self.model.load_game_section(self.game)
        turn1 = turn_infos.get(kwargs['turn1'])
        turn2 = turn_infos.get(kwargs['turn2'])
        if not turn1 or not turn2:
            raise Http404('Cant find turns in %s' % ', '.join(turn_infos))
        kwargs['diff'] = turn1.compare(turn2)
        return kwargs


class SummaryView(ModelTemplateView):
    template_name = "summary.html"

    def get_data(self, **kwargs):
        self.template_name = self.model.summary_template_name
        kwargs['data'] = self.model.get_summary(self.game, kwargs['turn'],
                                                start=self.request.GET.get('start'),
                                                end=self.request.GET.get('end'))
        kwargs['empire_id'] = Game(kwargs['game']).empire_id
        return kwargs


def plot(request, game, section, turn, start, end):
    model = get_model_class(section)
    plotter = model.get_plotter(game)
    response = HttpResponse(content_type='image/png')
    plotter.plot(response, get_model_class(section).get_branch(game, turn, start, end))
    return response



