from itertools import count


class Field(object):
    # count instances to order them in proper way
    COUNTER = count()

    def __init__(self, db_name=None, preprocess=None):
        self._id = next(self.COUNTER)
        self.db_name = db_name
        self.preprocess = preprocess

    def set_name(self, name):
        self.name = name
        if self.db_name is None:
            self.db_name = name

    def get_value(self, data_dict):
        value = data_dict.get(self.db_name, None)
        if self.preprocess:
            return self.preprocess(value)
        else:
            return value

    def get_html(self, value):
        return value

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.name == other.name

    def __ne__(self, other):
        return not self == other.name


class StringField(Field):
    pass


class NumberField(Field):
    pass


class TargetField(Field):
    def get_html(self, value):
        if not value:
            return 'no mission'
        mission_type, target_id, target_type, target_name = value
        if mission_type == 'None':
            return "mission with out targets"
        return "%s: %s %s(%s)" % (mission_type, target_type, target_name, target_id)


class BooleanField(Field):
    def get_html(self, value):
        if value:
            return 'Yes'
        else:
            return 'No'


class TurnField(NumberField):
    def get_html(self, value):
        return "Never" if value == -65535 else value


class ListField(Field):
    def get_html(self, value):
        return ', '.join(map(str, value))


class MapField(Field):
    def get_html(self, value):
        return ', '.join(('<small><i>%s=</i></small>"%s"' % (k, v) for k, v in value.items()))


class CoordinatesField(Field):
    def get_html(self, value):
        x, y = value
        return '<small>x</small>:%.2f, <small>y</small>:%.2f' % (x, y)


class OwnerField(Field):
    def get_html(self, value):
        if value == -1:
            return 'monster'
        # elif int(self.turn.empire_id) == value:
        #     return 'me'
        else:
            return value
