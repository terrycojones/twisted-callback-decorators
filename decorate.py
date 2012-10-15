from functools import wraps
from twisted.internet.defer import (
    Deferred, DeferredList, fail, maybeDeferred, succeed)
from twisted.python.failure import Failure


def _replace(value, location, args):
    args[location] = value
    return value


def callback(func):
    """
    A decorator that turns a regular function into one that can accept
    arguments that are C{Deferred}s.  If the deferreds (if any) all fire
    without error, the decorated function is called with the result of the
    deferreds, and a deferred is returned that fires with the result. If
    any of the deferreds fails, a deferred is returned that will fail with
    the failure.
    """
    @wraps(func)
    def wrapper(*args, **kw):
        fargs = []
        fkw = {}
        deferreds = []
        for index, arg in enumerate(args):
            if isinstance(arg, Deferred):
                fargs.append(None)
                deferreds.append(arg.addCallback(_replace, index, fargs))
            else:
                fargs.append(arg)
        for key, arg in kw.iteritems():
            if isinstance(arg, Deferred):
                deferreds.append(arg.addCallback(_replace, key, fkw))
            else:
                fkw[key] = arg
        if deferreds:
            def getSubFailure(failure):
                return failure.value.subFailure
            return DeferredList(
                deferreds, fireOnOneErrback=True, consumeErrors=True
            ).addCallbacks(callback=lambda _: func(*fargs, **fkw),
                           errback=getSubFailure)
        else:
            return maybeDeferred(func, *args, **kw)
    return wrapper


class ErrbackDecoratorError(Exception):
    """
    Raised if a function decorated with L{errback} is called with no
    positional arguments.
    """


def errback(func):
    """
    A decorator that turns a regular function into one that can accept
    arguments that are C{Deferred}s.  If any of the deferreds (if any)
    fail, the decorated function is called with the result of the
    deferreds, and a deferred is returned that fires with the result. If
    all the deferreds succeed, the wrapped function is not called and a
    deferred is returned that will succeed with just the first argument. In
    this last case, the decorator acts like a pass-through that returns its
    non-failure result.
    """
    @wraps(func)
    def wrapper(*args, **kw):
        if not args:
            return fail(ErrbackDecoratorError(
                '@errback decorated function %r invoked with '
                'no positional arguments.' % wrapper.__name__))
        fargs = []
        fkw = {}
        deferreds = []
        for index, arg in enumerate(args):
            if isinstance(arg, Deferred):
                fargs.append(None)
                deferreds.append(arg.addBoth(_replace, index, fargs))
            else:
                fargs.append(arg)
        for key, arg in kw.iteritems():
            if isinstance(arg, Deferred):
                deferreds.append(arg.addBoth(_replace, key, fkw))
            else:
                fkw[key] = arg
        if deferreds:
            def finish(ignore):
                if any(isinstance(v, Failure) for v in fargs + fkw.values()):
                    return func(*fargs, **fkw)
                else:
                    return fargs[0]
            return DeferredList(deferreds, consumeErrors=True).addCallback(
                finish)
        else:
            if any(isinstance(v, Failure) for v in fargs + fkw.values()):
                return maybeDeferred(func, *fargs, **fkw)
            else:
                return succeed(fargs[0])
    return wrapper


__all__ = ['callback', 'errback', 'ErrbackDecoratorError']
