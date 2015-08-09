from django.conf.urls import url

from . import views

SECTION = '(?P<section>\w+)'
GAME = '(?P<game>\d+_[0-9a-f]+_\w+)'
TURN = '(?P<turn>[0-9a-f]+)'
TURN_1 = '(?P<turn1>[0-9a-f]+)'
TURN_2 = '(?P<turn2>[0-9a-f]+)'


def get_url(*items):
    return r'^%s$' % '/'.join(items)


urlpatterns = [
    url(r'^$', views.GamesList.as_view(), name='games'),
    url(r'^research_compare$', views.ResearchCompare.as_view(), name='research_compare'),
    url(get_url(GAME, SECTION, TURN, '(?P<start>\d+)', '(?P<end>\d+)', 'plot.png'), views.plot, name='plot'),
    url(get_url(GAME, SECTION, TURN), views.SectionView.as_view(), name='section'),
    url(get_url(GAME, SECTION, TURN, 'summary'), views.SummaryView.as_view(), name='summary'),
    url(get_url(GAME, SECTION, TURN_1, TURN_2), views.DiffView.as_view(), name='diff'),
]

