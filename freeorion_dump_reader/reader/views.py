from django.shortcuts import get_object_or_404
from reader.models import Game, Turn, ResearchInfo

from django.views.generic import TemplateView, ListView, DetailView


class GameListView(ListView):
    model = Game

class GameMixin(TemplateView):
    def get_template_names(self):
        templates = super(GameMixin, self).get_template_names()
        if 'md' in self.request.GET:
            templates.insert(0, templates[0].replace('.html', '.md'))
        return templates

    def get_context_data(self, **kwargs):
        self.game = Game.objects.get(game_id=kwargs['game_id'])
        kwargs['game'] = self.game
        kwargs = self.prepare_context(**kwargs)
        return super(GameMixin, self).get_context_data(**kwargs)


class TurnMixin(GameMixin):
    def get_context_data(self, **kwargs):
        self.turn = Turn.objects.get(turn_id=kwargs['turn_id'])
        kwargs['turn'] = self.turn
        return super(TurnMixin, self).get_context_data(**kwargs)


class BranchView(TurnMixin):
    template_name = 'reader/branch.html'

    def prepare_context(self, **kwargs):
        kwargs['branch'] = self.game.get_branch(self.turn)
        return kwargs


class BranchProgressView(TurnMixin):
    template_name = 'reader/research_progress.html'

    def prepare_context(self, **kwargs):

        turns = self.game.get_branch(self.turn)
        research_in_progress = set()
        kwargs['progress'] = []

        for turn in turns:
            researches = turn.research_set.all()
            in_progress = set(x.research_info for x in researches)
            finished_this_turn = research_in_progress - in_progress
            added_this_turn = in_progress - research_in_progress
            if finished_this_turn or added_this_turn:
                kwargs['progress'].append((turn.turn, finished_this_turn, added_this_turn))
            research_in_progress = in_progress
        return kwargs


class ResearchInfoModelView(DetailView):
    def get_object(self, queryset=None):
        game_id = self.kwargs['game_id']
        research = self.kwargs['research']
        return get_object_or_404(ResearchInfo, game_id=game_id, name=research)


