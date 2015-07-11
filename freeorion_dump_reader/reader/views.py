
from django.http import Http404, HttpResponse
from django.views.generic import TemplateView
from reader.plotters import get_plotter

import reader.models
from reader.models import get_games, get_game, BaseModel

SECTIONS = ['planets', 'fleets', 'orders', 'research']


def get_model_class(name):
    for attr_name in dir(reader.models):
        attr = getattr(reader.models, attr_name)
        if isinstance(attr, type) and issubclass(attr, BaseModel) and attr.section == name:
            return attr
    raise Exception('Model %s not found' % name)


class GamesList(TemplateView):
    template_name = "games.html"

    def get_context_data(self, **kwargs):
        kwargs['games'] = get_games()
        kwargs['sections'] = SECTIONS
        return super(GamesList, self).get_context_data(**kwargs)


class ModelTemplateView(TemplateView):
    def get_context_data(self, **kwargs):
        kwargs = super(ModelTemplateView, self).get_context_data(**kwargs)
        self.model = get_model_class(kwargs['section'])
        self.turn = kwargs['turn']
        self.game = kwargs['game']
        kwargs['empire_id'] = kwargs['game'].split('_', 1)[0]
        return self.get_data(**kwargs)


class SectionView(ModelTemplateView):
    template_name = "section.html"

    def get_data(self, **kwargs):
        kwargs['data'] = self.model.get_branch(self.game, self.turn,
                                                 start=self.request.GET.get('start'),
                                                 end=self.request.GET.get('end'))
        return kwargs

class GameView(TemplateView):
    template_name = "game.html"

    def get_context_data(self, **kwargs):
        empire_name, creation_date, path, branches = get_game(kwargs['game'])
        return super(GameView, self).get_context_data(sections=SECTIONS, empire_name=empire_name,
                                                      creation_date=creation_date, branches=branches, **kwargs)


class DiffView(TemplateView):
    template_name = "diff.html"

    def get_context_data(self, **kwargs):
        turn_infos = get_model_class(kwargs['section']).load_game_section(kwargs['game'])
        turn1 = turn_infos.get(kwargs['turn1'])
        turn2 = turn_infos.get(kwargs['turn2'])
        if not turn1 or not turn2:
            raise Http404('Cant find turns in %s' % ', '.join(turn_infos))
        diff = turn1.compare(turn2)
        return super(DiffView, self).get_context_data(diff=diff, **kwargs)


def plot(request, game=None, turn=None, section=None):
    plotter = get_plotter(game, turn, section)
    response = HttpResponse(content_type='image/png')

    plotter.plot(response, get_model_class(section).get_turns(game, turn))
    return response
