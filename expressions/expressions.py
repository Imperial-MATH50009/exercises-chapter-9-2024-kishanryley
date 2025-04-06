from numbers import Number as Num
from functools import singledispatch


class Expression():
    def __init__(self, *operands):
        l = list()  # noqa E741
        for x in operands:
            if isinstance(x, Num):
                x = Number(x)
            l.append(x)
        self.operands = tuple(l)

    def __add__(self, other):
        return Add(self, other)

    def __sub__(self, other):
        return Sub(self, other)

    def __mul__(self, other):
        return Mul(self, other)

    def __truediv__(self, other):
        return Div(self, other)

    def __pow__(self, other):
        return Pow(self, other)

    def __radd__(self, other):
        return Add(other, self)

    def __rsub__(self, other):
        return Sub(other, self)

    def __rmul__(self, other):
        return Mul(other, self)

    def __rtruediv__(self, other):
        return Div(other, self)

    def __rpow__(self, other):
        return Pow(other, self)


class Terminal(Expression):
    prec = 3

    def __init__(self, value):
        self.value = value
        super().__init__()

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return repr(self.value)


class Number(Terminal):
    def __init__(self, value):
        self.operands = ()
        if isinstance(value, Num):
            self.value = value
        else:
            raise TypeError


class Symbol(Terminal):
    def __init__(self, value):
        self.operands = ()
        if isinstance(value, str):
            self.value = value
        else:
            raise TypeError


class Operator(Expression):
    def __repr__(self):
        return type(self).__name__ + repr(self.operands)

    def __str__(self):
        s = ""
        a = self.operands[0]
        b = self.operands[1]
        if a.prec < self.prec:
            s += f"({a})"
        else:
            s += str(a)
        s += f" {self.symbol} "
        if b.prec < self.prec:
            s += f"({b})"
        else:
            s += str(b)
        return s


class Add(Operator):
    prec = 0
    symbol = "+"


class Sub(Operator):
    prec = 0
    symbol = "-"


class Mul(Operator):
    prec = 1
    symbol = "*"


class Div(Operator):
    prec = 1
    symbol = "/"


class Pow(Operator):
    prec = 2
    symbol = "^"


def postvisitor(expr, fn, **kwargs):
    """Visit an Expression in postorder applying a function to every node.

    Parameters
    ----------
    expr: Expression
        The expression to be visited.
    fn: function(node, *o, **kwargs)
        A function to be applied at each node. The function should take
        the node to be visited as its first argument, and the results of
        visiting its operands as any further positional arguments. Any
        additional information that the visitor requires can be passed in
        as keyword arguments.
    **kwargs:
        Any additional keyword arguments to be passed to fn.
    """
    stack = []
    visited = {}
    stack.append(expr)
    while stack:
        current = stack.pop()
        unvisited = []
        for child in current.operands:
            if child not in visited:
                unvisited.append(child)
        if unvisited:
            stack.append(current)
            stack.extend(unvisited)
        else:
            visited[current] = fn(current, *[visited[child]
                                             for child in current.operands],
                                  **kwargs)
    return visited[expr]


@singledispatch
def differentiate(expr, *c, **kwargs):
    raise NotImplementedError(
        f"Cannot differentiate a {type(expr).__name__}")


@differentiate.register(Number)
def _(expr, *c, **kwards):
    return Number(0)


@differentiate.register(Symbol)
def _(expr, *c, var, **kwargs):
    if expr.value == var:
        return Number(1)
    return Number(0)


@differentiate.register(Add)
def _(expr, *c, **kwargs):
    return Add(c[0], c[1])


@differentiate.register(Sub)
def _(expr, *c, **kwargs):
    return Sub(c[0], c[1])


@differentiate.register(Mul)
def _(expr, *c, **kwargs):
    return Add(Mul(c[0], expr.operands[1]),
               Mul(c[1], expr.operands[0]))


@differentiate.register(Div)
def _(expr, *c, **kwargs):
    return Div(Sub(Mul(c[0], expr.operands[1]),
                   Mul(c[1], expr.operands[0])),
               Pow(expr.operands[1], Number(2)))


@differentiate.register(Pow)
def _(expr, *c, **kwargs):
    return Mul(expr.operands[1], Pow(expr.operands[0], Sub(expr.operands[1],
                                                           Number(1))))
