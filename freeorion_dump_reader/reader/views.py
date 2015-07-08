
from operator import attrgetter
from django.http import Http404, HttpResponse
from django.views.generic import TemplateView
from reader.plotters import get_plotter
from reader.tools import get_turns, get_games, load_game_section

SECTIONS = ['planets', 'fleets', 'orders', 'research']


class GamesList(TemplateView):
    template_name = "games.html"

    def get_context_data(self, **kwargs):
        kwargs['games'] = get_games()
        kwargs['sections'] = SECTIONS
        return super(GamesList, self).get_context_data(**kwargs)


class GameView(TemplateView):
    template_name = "game.html"

    def get_context_data(self, **kwargs):
        return super(GameView, self).get_context_data(sections=SECTIONS, **kwargs)


class SectionView(TemplateView):
    template_name = "section.html"

    def get_context_data(self, **kwargs):
        values = sorted(load_game_section(kwargs['game'], kwargs['section']).values(), key=attrgetter('turn'))
        kwargs['empire_id'] = kwargs['game'].split('_', 1)[0]
        return super(SectionView, self).get_context_data(data=values, **kwargs)


class DiffView(TemplateView):
    template_name = "diff.html"

    def get_context_data(self, **kwargs):
        turn_infos = load_game_section(kwargs['game'], kwargs['section'])

        turn1 = turn_infos.get(kwargs['turn1'])
        turn2 = turn_infos.get(kwargs['turn2'])
        if not turn1 or not turn2:
            raise Http404('Cant find turns in %s' % ', '.join(turn_infos))
        diff = turn1.compare(turn2)
        return super(DiffView, self).get_context_data(diff=diff, **kwargs)


def plot(request, game=None, turn=None, section=None):
    plotter = get_plotter(game, turn, section)
    response = HttpResponse(content_type='image/png')
    plotter.plot(response, get_turns(game, turn, section))
    return response
