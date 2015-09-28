from itertools import count


class Field(object):
    # coubt instances to order them in proper way
    COUNTER = count()

    def __init__(self, db_name=None):
        self._id = next(self.COUNTER)
        self.db_name = db_name

    def set_name(self, name):
        self.name = name
        if self.db_name is None:
            self.db_name = name

    def get_value(self, data_dict):
        return data_dict[self.db_name]


class StringField(Field):
    pass


class NumberField(Field):
    pass
