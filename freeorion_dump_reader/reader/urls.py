from django.conf.urls import url

from . import views
from . import importing

SECTION = '(?P<section>\w+)'
GAME = '(?P<game_id>\d+_[0-9a-f]+_\w+)'
GAME1 = '(?P<game_id1>\d+_[0-9a-f]+_\w+)'
GAME2 = '(?P<game_id2>\d+_[0-9a-f]+_\w+)'
TURN = '(?P<turn_id>[0-9a-f]+)-?(?P<decrement>\d+)?'
TURN1 = '(?P<turn_id1>[0-9a-f]+)-?(?P<decrement1>\d+)?'
TURN2 = '(?P<turn_id2>[0-9a-f]+)-?(?P<decrement2>\d+)?'


def get_url(*items):
    return r'^%s$' % '/'.join(items)


urlpatterns = [
    url(r'^$', views.GameListView.as_view(), name='games'),
    url(r'^import_list/$', importing.ImportListView.as_view(), name='import_list'),
    url(r'^import/$', importing.ImportView.as_view(), name='import'),
    url(get_url(GAME, TURN), views.BranchView.as_view(), name='branch'),
    url(get_url(GAME, TURN, 'research', 'progress'), views.BranchProgressView.as_view(), name='research_progress'),
    url(get_url('info', GAME, 'research', '(?P<research>[A-Z_]+)'), views.ResearchInfoModelView.as_view(), name='research_info'),
    url(get_url(GAME1, TURN1, GAME2, TURN2), views.TurnInfoView.as_view(), name='turn_info'),
    # url(r'^$', views.GamesList.as_view(), name='games'),
    # url(r'^research_compare$', views.ResearchCompare.as_view(), name='research_compare'),
    # # url(get_url(GAME, SECTION, TURN, '(?P<start>\d+)', '(?P<end>\d+)', 'plot.png'), views.plot, name='plot'),
    # url(get_url(GAME, SECTION, TURN), views.SectionView.as_view(), name='section'),
    # url(get_url(GAME, SECTION, TURN, 'summary'), views.SummaryView.as_view(), name='summary'),
    # url(get_url(GAME, SECTION, TURN_1, TURN_2), views.DiffView.as_view(), name='diff'),
]

