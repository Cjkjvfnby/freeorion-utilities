from django.shortcuts import get_object_or_404

from reader.diff_tools import get_diff
from reader.models import Game, Turn, ResearchInfo

from django.views.generic import TemplateView, ListView, DetailView


class GameListView(ListView):
    model = Game


class MdMixin(TemplateView):
    def get_template_names(self):
        templates = super(MdMixin, self).get_template_names()
        if 'md' in self.request.GET:
            templates.insert(0, templates[0].replace('.html', '.md'))
        return templates


class GameMixin(MdMixin):
    def get_context_data(self, **kwargs):
        self.game = Game.objects.get(game_id=kwargs['game_id'])
        kwargs['game'] = self.game
        kwargs = self.prepare_context(**kwargs)
        return super(GameMixin, self).get_context_data(**kwargs)


class TurnMixin(GameMixin):
    def get_context_data(self, **kwargs):
        self.turn = Turn.find_turn(kwargs['game_id'], kwargs['turn_id'], kwargs['decrement'])
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
            researches = turn.researches.all()
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


class TurnInfoView(MdMixin):
    template_name = 'reader/turn_info.html'

    def get_turn(self, game, turn_id, decrement):
        if turn_id == '0':
            return Turn(
                game=game,
                turn_id='0',
                parent_id='0',
                turn=0,
                production=0,
                population=0
            )
        else:
            return Turn.find_turn(game.game_id, turn_id, decrement)

    def get_context_data(self, **kwargs):
        game_1 = Game.objects.get(game_id=kwargs['game_id1'])
        game_2 = Game.objects.get(game_id=kwargs['game_id2'])
        kwargs['game1'] = game_1
        kwargs['game2'] = game_2
        this = self.get_turn(game_1, kwargs['turn_id1'], kwargs['decrement1'])
        that = self.get_turn(game_2, kwargs['turn_id2'], kwargs['decrement2'])
        kwargs['this'] = this
        kwargs['that'] = that

        kwargs['compare'] = get_diff(this, that)
        return super(TurnInfoView, self).get_context_data(**kwargs)
