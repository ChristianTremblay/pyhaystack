# -*- coding: utf-8 -*-
"""
Filter abstract syntax tree builder.  These classes and functions attempt to
build a filter string for use with 'read' operations by combining Python's
operators to trick it into producing the desired values.

Yes, we're hijacking operators to do what they weren't expected to do.

Typical usage::

        from pyhaystack.util import filterbuilder as fb

        # Get all historical points:
        session.find_points(fb.Field('his'))

        # All historical points in Brisbane timezone.
        session.find_points(fb.Field('his') & \
                ( fb.Field('tz') == fb.Scalar('Brisbane') ))
"""

import hszinc


class Base(object):
    def __and__(self, other):
        return And(self, other)

    def __or__(self, other):
        return Or(self, other)

    def __not__(self):
        return Not(self)


class Field(Base):
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, Scalar):
            raise TypeError("not a scalar: %r" % other)
        return Equal(self, other)

    def __ne__(self, other):
        if not isinstance(other, Scalar):
            raise TypeError("not a scalar: %r" % other)
        return NotEqual(self, other)

    def __lt__(self, other):
        if not isinstance(other, Scalar):
            raise TypeError("not a scalar: %r" % other)
        return LessThan(self, other)

    def __le__(self, other):
        if not isinstance(other, Scalar):
            raise TypeError("not a scalar: %r" % other)
        return LessThanOrEqual(self, other)

    def __gt__(self, other):
        if not isinstance(other, Scalar):
            raise TypeError("not a scalar: %r" % other)
        return GreaterThan(self, other)

    def __ge__(self, other):
        if not isinstance(other, Scalar):
            raise TypeError("not a scalar: %r" % other)
        return GreaterThanOrEqual(self, other)

    def __str__(self):
        return str(self.value)


class Scalar(Base):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return hszinc.dump_scalar(self.value, mode=hszinc.MODE_ZINC)


class Binary(Base):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        if isinstance(self.x, Binary):
            x = "( %s )" % self.x
        else:
            x = str(self.x)

        if isinstance(self.y, Binary):
            y = "( %s )" % self.y
        else:
            y = str(self.y)

        return "%s %s %s" % (x, self.OP, y)


class Unary(Base):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        if isinstance(self.value, Binary):
            return "%s ( %s )" % (self.OP, self.value)
        else:
            return "%s %s" % (self.OP, self.value)


class Equal(Binary):
    OP = "=="


class NotEqual(Binary):
    OP = "!="


class LessThan(Binary):
    OP = "<"


class LessThanOrEqual(Binary):
    OP = "<="


class GreaterThan(Binary):
    OP = ">"


class GreaterThanOrEqual(Binary):
    OP = ">="


class And(Binary):
    OP = "and"


class Or(Binary):
    OP = "or"


class Not(Unary):
    OP = "not"
