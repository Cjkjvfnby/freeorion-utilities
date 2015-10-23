from db import db
from reader.fields import Field


class ModelMeta(type):
    """
    Metaclass for all models.
    """
    def __new__(cls, name, bases, attrs):
        super_new = super(ModelMeta, cls).__new__
        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})
        fields = []
        for attr_name, attr_value in attrs.items():
            if isinstance(attr_value, Field):
                attr_value.set_name(attr_name)
                fields.append(attr_value)
            else:
                setattr(new_class, attr_name, attr_value)
        new_class._fields = tuple(sorted(fields, key=lambda x: x._id))

        return new_class


class DataField(object):
    def __init__(self, field, value):
        self.value = value
        self.field = field

    def get_html(self):
        return self.field.get_html(self.value)

    def __eq__(self, other):
        return self.value == other.value and self.field == other.field

    def __ne__(self, other):
        return not self == other


class Turn(list):
    def __init__(self, header, data):
        self.turn_id = header['turn_id']
        self.parent_id = header['parent_id']
        self.turn = header['turn']
        super(Turn, self).__init__(data)


class Model(object):
    __metaclass__ = ModelMeta

    def __init__(self, data_dict):
        self.fields = []
        for field in self._fields:
            setattr(self, field.name, field.get_value(data_dict))
            self.fields.append(DataField(field, field.get_value(data_dict)))

    @classmethod
    def get_branch(cls, game_id, branch_end, start, end):
        turns = [db.get_turn(game_id, cls.SECTION, x['turn_id']) for x in db.get_branch(game_id, cls.SECTION, branch_end, start, end)]
        return [Turn(header, (cls(data) for data in info)) for header, info in turns]

    @classmethod
    def get_turn(cls, game_id, turn_id):
        header, info = db.get_turn(game_id, cls.SECTION, turn_id)
        return Turn(header, (cls(data) for data in info))

    def get_diff(self, other):
        res = []

        for first, second in zip(self.fields, other.fields):
            if first != second:
                res.append([first.field.name, first.get_html(), second.get_html()])
        if res:
            return [(self.SECTION, self.get_key(), None)] + res
        else:
            return []
