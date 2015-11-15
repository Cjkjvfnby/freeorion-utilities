from reader.models import Game, Turn

from django.views.generic import TemplateView, ListView


class GameListView(ListView):
    model = Game


class ResearchInfo(TemplateView):
    template_name = 'reader/research.html'

    def get_context_data(self, **kwargs):
        pass


class GameMixin(TemplateView):
    def get_context_data(self, **kwargs):
        self.game = Game.objects.get(game_id=kwargs['game_id'])
        kwargs['game'] = self.game
        kwargs = self.prepare_context(**kwargs)
        return super(GameMixin, self).get_context_data(**kwargs)


class TurenMixin(GameMixin):
    def get_context_data(self, **kwargs):
        self.turn = Turn.objects.get(turn_id=kwargs['turn_id'])
        kwargs['turn'] = self.turn
        return super(TurenMixin, self).get_context_data(**kwargs)


class BranchView(TurenMixin):
    template_name = 'reader/branch.html'

    def prepare_context(self, **kwargs):
        kwargs['branch'] = self.game.get_branch(self.turn)
        return kwargs


class BranchProgressView(TurenMixin):
    template_name = 'reader/research_progress.html'

    def prepare_context(self, **kwargs):
        branch = self.game.get_branch(self.turn)
        return kwargs
