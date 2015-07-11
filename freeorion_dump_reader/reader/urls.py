from django.conf.urls import url

from . import views
from . import summaries

SECTION = '(?P<section>\w+)'
GAME = '(?P<game>\d+_[0-9a-f]+_\w+)'
TURN = '(?P<turn>[0-9a-f]+)'
TURN_1 = '(?P<turn1>[0-9a-f]+)'
TURN_2 = '(?P<turn2>[0-9a-f]+)'


def get_url(*items):
    return r'^%s$' % '/'.join(items)


urlpatterns = [
    url(r'^$', views.GamesList.as_view(), name='games'),
    url(get_url(GAME, TURN, SECTION, 'plot.png'), views.plot, name='plot'),
    url(get_url(GAME, SECTION, TURN), views.SectionView.as_view(), name='section'),
    url(get_url(GAME, SECTION, TURN, 'summary'), summaries.SummaryView.as_view(), name='summary'),
    url(get_url(GAME, SECTION, TURN_1, TURN_2), views.DiffView.as_view(), name='diff'),
]

