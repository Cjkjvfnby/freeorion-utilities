from django.views.generic import TemplateView
from reader.models import get_turns, BaseModel



class SummaryView(TemplateView):
    template_name = "summary.html"

    def get_context_data(self, **kwargs):
        section = kwargs['section']
        if section == 'research':
            summary_function = research_summary
            self.template_name = 'research_summary.html'
        else:
            summary_function = base_summary
        turns = summary_function(**kwargs)
        kwargs['empire_id'] = kwargs['game'].split('_', 1)[0]
        return super(SummaryView, self).get_context_data(data=turns, **kwargs)


def base_summary(**kwargs):
    turns = get_turns(kwargs['game'], kwargs['turn'], kwargs['section'])
    return turns


def research_summary(**kwargs):
    turns = get_turns(kwargs['game'], kwargs['turn'], kwargs['section'])
    result = []
    research_in_progress = set()
    for turn in turns:
        assert isinstance(turn, BaseModel)
        in_progress = set(x[0][1] for x in turn.columns)
        finished_this_turn = research_in_progress - in_progress
        added_this_turn = in_progress - research_in_progress
        result.append((turn.turn, finished_this_turn, added_this_turn))
        research_in_progress = in_progress
    return [x for x in result if any(x[1:])]
