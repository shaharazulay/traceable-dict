from types import MethodType

from _diff import DictDiff


__all__ = []


class TraceableMeta(type):
    """
    Meta class for tracable dict, using the DictDiff service class.
    """

    CLASS_ATTR = [
        '__class__',
        '__new__',
        '__init__',
        '__dict__',
        '__metaclass__',
        '__getattribute__',
        '__setattr__'
    ]

    def wrapper(self, func):
        def wrapped(self, *args, **kwargs):
            print 'wrapper.__call__(): ', func.__name__
            before = self.freeze
            res = func(self, *args, **kwargs)
            after = self.freeze
            
            trace = DictDiff.find_diff(before, after)
            if len(trace) > 0:
                self.update_trace(trace)
            return res
        return wrapped
        
    def __init__(cls, classname, bases, class_dict):
        print 'meta.__init__()'
        for attr_name in dir(cls):

            if attr_name in TraceableMeta.CLASS_ATTR:
                continue

            attr = getattr(cls, attr_name)
            if isinstance(attr, MethodType) or isinstance(attr, property):
                continue

            if hasattr(attr, '__call__'):
                attr = cls.wrapper(attr)
                setattr(cls, attr_name, attr)

        super(TraceableMeta, cls).__init__(classname, bases, class_dict)


__all__ += ['TraceableMeta']
