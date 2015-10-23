from inspect import isclass, getmembers
import os
from pprint import pprint
from django.conf import settings
import json
from django.http import Http404, HttpResponse
from django.views.generic import TemplateView
from reader.base_models import Model
from reader.models import ResearchModel

import reader.models
from reader.db import db, Game, SECTIONS


def get_model_class(name):
    for attr_name in dir(reader.models):
        attr = getattr(reader.models, attr_name)
        if isinstance(attr, type) and issubclass(attr, Model) and getattr(attr, 'SECTION', None) == name:
            return attr
    raise Exception('Model %s not found' % name)


class GamesList(TemplateView):
    template_name = "games.html"

    def get_context_data(self, **kwargs):
        if not os.path.exists(settings.DUMP_FOLDER):
            raise Http404('Dumps folder not found')
        kwargs['games'] = db.get_games()
        kwargs['sections'] = SECTIONS
        return super(GamesList, self).get_context_data(**kwargs)


class ResearchCompare(TemplateView):
    template_name = "research_compare.html"

    def get_context_data(self, **kwargs):
        if self.request.GET.get('md'):
            self.template_name = 'research_compare.md'

        games = [x.split('-') for x in self.request.GET.getlist('q[]')]

        branches = [ResearchModel.get_branch(game_id, research_group, None, None) for game_id, research_group in games]

        border = min(len(branch) for branch in branches)

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
            for research_group in turns[:border]:
                names = set(x.name for x in research_group)
                new = names - in_progress
                finished = in_progress - names
                in_progress.update(new)
                in_progress -= finished
                for tech in new:
                    tech_stats[tech].append({'started': research_group[0].turn_info['turn']})
                for tech in finished:
                    tech_stats[tech][-1]['finished'] = research_group[0].turn_info['turn']
        kwargs['stats'] = sorted(sorted(tech_stats.items()), key=lambda x: len(x[1]), reverse=True)
        return super(ResearchCompare, self).get_context_data(**kwargs)


class ModelTemplateView(TemplateView):
    def get_context_data(self, **kwargs):
        kwargs = super(ModelTemplateView, self).get_context_data(**kwargs)
        self.model = get_model_class(kwargs['section'])
        self.game = kwargs['game'] = Game(kwargs['game'])
        self.turn = kwargs['turn']
        self.empire_id = kwargs['empire_id'] = self.game.empire_id
        kwargs['sections'] = SECTIONS
        self.start = kwargs['start'] = self.request.GET.get('start')
        self.end = kwargs['end'] = self.request.GET.get('end')
        return self.get_data(**kwargs)


class SectionView(ModelTemplateView):
    template_name = "section.html"

    def get_data(self, **kwargs):
        data = self.model.get_branch(self.game.game_id, self.turn, self.start,
                                     self.end)
        kwargs['data'] = data
        if data:
            kwargs['headers'] = kwargs['data'][0][0]._fields
        return kwargs


class DiffView(ModelTemplateView):
    template_name = "diff.html"

    def get_data(self, **kwargs):
        turn1_items = self.model.get_turn(self.game.game_id, kwargs['turn1'])
        turn2_items = self.model.get_turn(self.game.game_id, kwargs['turn2'])
        if not turn1_items or not turn2_items:
            raise Http404('Cant find turns')
        kwargs['diff'] = self.compare(turn1_items, turn2_items)
        return kwargs

    def compare(self, first, second):
        data1 = {x.get_key(): x for x in first}
        data2 = {x.get_key(): x for x in second}
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
            return [('id', None, other.get_key())]
        if other is None:
            return [('id', this.get_key(), None)]
        return this.get_diff(other)


def research_summary_function(**kwargs):
    turns = kwargs['data']

    kwargs['data'] = []
    research_in_progress = set()
    for turn in turns:
        in_progress = set(x.name for x in turn)
        finished_this_turn = research_in_progress - in_progress
        added_this_turn = in_progress - research_in_progress
        if finished_this_turn or added_this_turn:
            kwargs['data'].append((turn.turn, finished_this_turn, added_this_turn))
        research_in_progress = in_progress
    return kwargs


INFO = {
    'default': {
        'summary_view': 'summary',
        'summary_function': lambda **kwargs: kwargs
    },
    ResearchModel: {
        'summary_view': 'research_summary',
        'summary_function': research_summary_function
    }
}


class SummaryView(ModelTemplateView):
    def get_template_names(self):
        name = INFO.get(self.model, {}).get('summary_view')
        if not name:
            name = INFO['default']['summary_view']
        return name + '.html'

    def get_data(self, **kwargs):
        summary_function = INFO.get(self.model, {}).get('summary_function')
        if not summary_function:
            summary_function = INFO['default']['summary_function']
        kwargs['data'] = self.model.get_branch(self.game.game_id, self.turn, self.start, self.end)
        return summary_function(**kwargs)


def plot(request, game, section, turn, start, end):
    model = get_model_class(section)
    plotter = model.get_plotter(game)
    response = HttpResponse(content_type='image/png')
    plotter.plot(response, get_model_class(section).get_branch(game, turn, start, end))
    return response



