import os
from django.conf import settings
from django.http import Http404, HttpResponse
from django.views.generic import TemplateView

import reader.models
from reader.models import BaseModel, Game

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
        kwargs['games'] = [Game(path) for path in os.listdir(settings.DUMP_FOLDER)]
        kwargs['sections'] = SECTIONS
        return super(GamesList, self).get_context_data(**kwargs)


class ModelTemplateView(TemplateView):
    def get_context_data(self, **kwargs):
        kwargs = super(ModelTemplateView, self).get_context_data(**kwargs)
        self.model = get_model_class(kwargs['section'])
        self.game = kwargs['game']
        kwargs['empire_id'] = Game(kwargs['game']).empire_id
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
        kwargs['start'] = self.request.GET.get('start')
        kwargs['end'] = self.request.GET.get('end')
        return kwargs


def plot(request, game, section, turn, start, end):
    model = get_model_class(section)
    plotter = model.get_plotter(game)
    response = HttpResponse(content_type='image/png')
    plotter.plot(response, get_model_class(section).get_branch(game, turn,
                                                    start, end))
    return response
