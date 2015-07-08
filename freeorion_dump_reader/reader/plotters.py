from collections import Counter

# http://stackoverflow.com/a/28538794/1310066
import colorsys
from itertools import cycle
import matplotlib
matplotlib.use('agg')

from matplotlib.pyplot import gca, FormatStrFormatter, xkcd, figure, close, xticks, grid, hist
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.font_manager import FontProperties

xkcd()


def get_plotter(game, turn, section):
    if section == 'orders':
        return OrdersPlotter(game, turn, section)
    elif section == 'planets':
        return PlanetsPlotter(game, turn, section)
    elif section == 'fleets':
        return FleetsPlotter(game, turn, section)
    elif section == 'research':
        return ResearchPlotter(game, turn, section)
    return BasePlotter(game, turn, section)



def color_iterator():
    while True:
        color = 20
        for hue in range(0, color*6, 6):
            hue = 1. * hue / color
            col = [int(x) for x in colorsys.hsv_to_rgb(hue, 1.0, 230)]
            yield "#{0:02x}{1:02x}{2:02x}".format(*col)


class BasePlotter(object):
    def __init__(self, game, turn, section):
        self.turn = turn
        self.game = game
        self.section = section
        self.figure = figure(figsize=(12, 6))
        self.axis = gca()
        self._color = color_iterator()
        self._line_style = cycle(['-', '--', '-.', ':'])
        self._style = self.style_iterator()

    def next_style(self):
        return next(self.style_iterator())

    def style_iterator(self):
        while True:
            yield dict(
                color=next(self._color),
                linestyle=next(self._line_style))

    def get_y_label(self):
        return self.section

    def add_graph(self, y_values, label=None):
        label = label or self.section
        self.axis.plot(self.x_values, y_values, label=label, **self.next_style())
        self.axis.yaxis.set_major_formatter(FormatStrFormatter('%d'))
        self.axis.yaxis.set_major_formatter(FormatStrFormatter('%d'))
        self.axis.set_xlim(1, self.x_values[-1])
        # dont show float numbers on small amount of turns
        if len(self.x_values) < 10:
            xticks(self.x_values)
        self.axis.set_ylabel(self.get_y_label(), size=16)
        self.axis.set_xlabel('turns', size=16)
    
    def add_graphs(self, turns):
        y_values = [len(x.data) for x in turns]
        self.add_graph(y_values)

    def plot(self, response, turns):
        self.x_values = [x.turn for x in turns]
        self.add_graphs(turns)
        canvas = FigureCanvasAgg(self.figure)
        # shrink axis to fit legend http://stackoverflow.com/a/4701285/1310066
        box = self.axis.get_position()
        self.axis.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        self.set_legend()
        canvas.print_png(response)
        close(self.figure)

    def set_legend(self):
        fontP = FontProperties()
        fontP.set_size('small')
        self.axis.legend(loc='upper left', bbox_to_anchor=(1, 1), prop=fontP)

ORDERS_NAMES = (
    'Scrap',
    'Aggression',
    'Bombard',
    'ChangeFocus',
    'ChangeProductionQuantity',
    'Colonize',
    'CreateShipDesign',
    'DequeueProduction',
    'DequeueTech',
    'EnqueueBuildingProduction',
    'EnqueueShipProduction',
    'EnqueueTech',
    'FleetMove',
    'FleetTransfer',
    'GiveObjectToEmpire',
    'Invade',
    'NewFleet',
    'Rename',
    'RequeueProduction'
)


class OrdersPlotter(BasePlotter):
    def plot(self, response, turns):
        """
        Ignore first turn.
        """
        return super(OrdersPlotter, self).plot(response, turns[1:])

    def add_graphs(self, turns):
        used_orders = set()
        turn_orders = {}
        for turn_info in turns:
            for info in turn_info.data:
                turn_orders.setdefault(turn_info.turn, Counter())[info['name']] += 1
                used_orders.add(info['name'])

        for order in ORDERS_NAMES:
            if order in used_orders:
                y_values = [turn_orders[x.turn][order] for x in turns]
                self.add_graph(y_values, label=order)


PLANETS_VISIBILITIES = ['none', 'basic', 'partial', 'full']


class PlanetsPlotter(BasePlotter):
    def add_graphs(self, turns):
        planets = []
        for turn_info in turns:
            planets.append([0, 0, 0, 0])
            for info in turn_info.data:
                planets[-1][PLANETS_VISIBILITIES.index(info['visibility'])] += 1

        for i in xrange(1, len(PLANETS_VISIBILITIES) + 1):
            y_values = [sum(planets[x.turn-1][:i]) for x in turns]
            self.add_graph(y_values, label=PLANETS_VISIBILITIES[i - 1])


class FleetsPlotter(BasePlotter):
    def add_graphs(self, turns):
        fleets = {}
        owners = set()
        for turn_info in turns:
            for info in turn_info.data:
                fleets.setdefault(turn_info.turn, Counter())[info['owner']] += len(info['ships'])
                owners.add(info['owner'])

        owners = sorted(owners)
        owner_names = []
        for x in owners:
            if x == -1:
                owner_names.append('Monsters')
            elif x == turns[0].empire_id:
                owner_names.append('Me')
            else:
                owner_names.append('Empire %s' % x)

        for owner, owner_name in zip(owners, owner_names):
            y_values = [fleets[x.turn][owner] for x in turns]
            self.add_graph(y_values, label=owner_name)

    def get_y_label(self):
        return "ships in fleets"

class ResearchPlotter(BasePlotter):
    def get_y_label(self):
        return "research in queue"
