from _diff import DictDiff


__all__ = []


class TraceableMeta(type):
    """
    Meta class for tracable dict, using the DictDiff service class.
    """

    EXCLUDE_CLASS_ATTR = [
        '__class__',
        '__new__',
        '__init__',
        '__dict__',
        '__metaclass__',
        '__getattribute__',
        '__setattr__'
    ]

    INCLUDE_CHILD_ATTR = [
        '_update'
    ]

    def wrapper(self, func):
        def wrapped(self, *args, **kwargs):
            before = self.as_dict()
            res = func(self, *args, **kwargs)
            after = self.as_dict()
            
            trace = DictDiff.find_diff(before, after)
            if len(trace) > 0:
                self.update_trace(trace)
            return res
        return wrapped

    def __init__(cls, classname, bases, class_dict):
        for attr_name in dir(cls):

            if attr_name in TraceableMeta.EXCLUDE_CLASS_ATTR:
                continue

            is_base_attr = any([hasattr(base, attr_name) for base in bases])
            if is_base_attr or attr_name in TraceableMeta.INCLUDE_CHILD_ATTR:

                attr = getattr(cls, attr_name)

                if hasattr(attr, '__call__'):
                    attr = cls.wrapper(attr)
                    setattr(cls, attr_name, attr)

        super(TraceableMeta, cls).__init__(classname, bases, class_dict)


__all__ += ['TraceableMeta']
