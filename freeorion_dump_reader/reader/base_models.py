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


class Model(object):
    __metaclass__ = ModelMeta

    def __init__(self, data_dict):
        for field in self._fields:
            setattr(self, field.name, field.get_value(data_dict))

    def get_branch(self, game, branch_end, start, end):
        return [self.__class__(x) for x in db.get_branch(game, self.SECTION, branch_end, start, end)]




