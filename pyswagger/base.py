from __future__ import absolute_import
import six


class Context(list):
    """ Base of all Contexts

    __swagger_required__: required fields
    __swagger_child__: list of tuples about nested context
    __swagger_ref_obj__: class of reference object, would be used when
    performing request.
    """

    __swagger_required__ = []
    __swagger_child__ = []

    def __init__(self, parent_obj, backref):
        self._parent_obj = parent_obj
        self._backref = backref
        self.__reset_obj()

    def __enter__(self):
        return self

    def __reset_obj(self):
        """
        """
        self._obj = {}

    def back2parent(self, parent_obj, backref):
        """ update what we get as a reference object,
        and put it back to parent context.
        """
        if not self._obj:
            # TODO: a warning for empty object?
            return

        obj = self.__class__.__swagger_ref_object__(self)
        if isinstance(parent_obj[backref], list):
            parent_obj[backref].append(obj)
            # TODO: check for uniqueness
        else:
            parent_obj[backref] = obj

        self.__reset_obj()

    def __exit__(self, exc_type, exc_value, traceback):
        return self.back2parent(self._parent_obj, self._backref)

    def parse(self, obj=None):
        """ go deeper into objects
        """
        if not obj:
            return

        if not isinstance(obj, dict):
            raise ValueError('invalid obj passed: ' + str(type(obj)))

        if hasattr(self, '__swagger_required__'):
            # check required field
            missing = set(self.__class__.__swagger_required__) - set(obj.keys())
            if len(missing):
                raise ValueError('Required: ' + str(missing))

        if hasattr(self, '__swagger_child__'):
            # to nested objects
            for key, ctx_kls in self.__swagger_child__:
                items = obj.get(key, None)
                if isinstance(items, list):
                    # for objects grouped in list
                    self._obj[key] = []
                    for item in items:
                        with ctx_kls(self._obj, key) as ctx:
                            ctx.parse(obj=item)
                else:
                    self._obj[key] = {}
                    nested_obj = obj.get(key, None)
                    with ctx_kls(self._obj, key) as ctx:
                        ctx.parse(obj=nested_obj)

        # update _obj with obj
        if self._obj != None:
            for key in (set(obj.keys()) - set(self._obj.keys())):
                self._obj[key] = obj[key]
        else:
            self._obj = obj


class NamedContext(Context):
    """ for named object
    """
    def parse(self, obj=None):
        if not isinstance(obj, dict):
            raise ValueError('invalid obj passed: ' + str(type(obj)))

        for k, v in obj.iteritems():
            if isinstance(v, list):
                self._parent_obj[self._backref][k] = []
                for item in v:
                    super(NamedContext, self).parse(item)
                    self.back2parent(self._parent_obj[self._backref], k)
            elif isinstance(v, dict):
                super(NamedContext, self).parse(v)
                self._parent_obj[self._backref][k] = None
                self.back2parent(self._parent_obj[self._backref], k)
            else:
                raise ValueError('Unknown item type: ' + str(type(v)))


class BaseObj(object):
    """ Base implementation of all referencial objects,
    make all properties readonly.

    __swagger_fields__: list of names of fields, we will skip fields not
    in this list.
    __swagger_rename__: fields that need re-named.
    """

    __swagger_rename__ = {}
    __swagger_fields__ = []

    def __init__(self, ctx):
        super(BaseObj, self).__init__()

        if not issubclass(type(ctx), Context):
            raise TypeError('should provide args[0] as Context, not: ' + ctx.__class__.__name__)

        # handle required fields
        for field in set(ctx.__swagger_required__) & set(self.__swagger_fields__):
            self.update_field(field, ctx._obj[field])

        # handle not-required fields
        for field in set(self.__swagger_fields__) - set(ctx.__swagger_required__):
            self.update_field(field, ctx._obj.get(field, None))

    def get_private_name(self, f):
        f = self.__swagger_rename__[f] if f in self.__swagger_rename__.keys() else f
        return '_' + self.__class__.__name__ + '__' + f
 
    def update_field(self, f, obj):
        """ update a field
        """
        setattr(self, self.get_private_name(f), obj)


def _method_(name):
    """ getter factory """
    def _getter_(self):
        return getattr(self, self.get_private_name(name))
    return _getter_


class Field(type):
    """ metaclass to init fields
    """
    def __new__(metacls, name, bases, spc):
        def init_fields(fields, rename):
            for f in fields:
                f = rename[f] if f in rename.keys() else f
                spc[f] = property(_method_(f))

        rename = spc['__swagger_rename__'] if '__swagger_rename__' in spc.keys() else {}
        if '__swagger_fields__' in spc.keys():
            init_fields(spc['__swagger_fields__'], rename)

        for b in bases:
            fields = b.__swagger_fields__ if hasattr(b, '__swagger_fields__') else {}
            rename = b.__swagger_rename__ if hasattr(b, '__swagger_rename__') else {}
            init_fields(fields, rename)

        return type.__new__(metacls, name, bases, spc)


class Items(six.with_metaclass(Field, BaseObj)):
    """ Items Object
    """
    __swagger_fields__ = ['type', '$ref']
    __swagger_rename__ = {'$ref': 'ref'}


class ItemsContext(Context):
    """ Context of Items Object
    """
    __swagger_ref_object__ = Items
    __swagger_required__ = []


class DataTypeObj(BaseObj):
    """ Data Type Fields
    """
    __swagger_fields__ = [
        'type',
        '$ref',
        'format',
        'defaultValue',
        'enum',
        'items',
        'minimum',
        'maximum',
        'uniqueItems'
    ]
    __swagger_rename__ = {'$ref': 'ref'}

    def __init__(self, ctx):
        super(DataTypeObj, self).__init__(ctx)

        # Items Object, too lazy to create a Context for DataTypeObj
        # to wrap this child.
        with ItemsContext(ctx._obj, 'items') as items_ctx:
            items_ctx.parse(ctx._obj.get('items', None))

        type_fields = set(DataTypeObj.__swagger_fields__) - set(ctx.__swagger_required__)
        for field in type_fields:
            # almost every data field is not required.
            # TODO: need to make sure either 'type' or '$ref' is shown.
            local_obj = ctx._obj.get(field, None)
            self.update_field(field, local_obj)
