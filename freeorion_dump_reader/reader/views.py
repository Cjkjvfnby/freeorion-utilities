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
        all_turns = Turn.objects.filter(turn__lte=self.turn.turn, game=self.game).order_by('-turn')
        print len(all_turns)

        branch = [self.turn]
        next_turn = self.turn.parent_id
        for item in all_turns:
            if item.turn_id == next_turn:
                branch.append(item)
                next_turn = item.parent_id
        kwargs['branch'] = reversed(branch)
        return kwargs
