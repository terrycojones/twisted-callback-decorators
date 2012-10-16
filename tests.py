from operator import add
from twisted.internet.defer import inlineCallbacks, fail, succeed
from twisted.python.failure import Failure
from twisted.trial.unittest import TestCase
from decorate import callback, errback, ErrbackDecoratorError


@errback
def raisingChecker(failure):
    assert isinstance(failure, Failure)
    raise failure.value


@errback
def failingChecker(failure):
    assert isinstance(failure, Failure)
    return failure


@errback
def twoArgChecker(failure, y):
    assert isinstance(failure, Failure)
    return y


@errback
def twoArgCheckerKw(failure, default=None):
    assert isinstance(failure, Failure)
    return default


@errback
def threeArgCheckerMixed(failure, y, extra=0):
    assert isinstance(failure, Failure)
    return y + extra


@callback
def adder(x, y):
    return x + y


@callback
def adderKw(x=None, y=None):
    return x + y


@callback
def adderMixed(x, y=None):
    return x + y


class TestDecorators(TestCase):

    @inlineCallbacks
    def testSynchronous(self):
        """A callback must accept regular (non-Deferred) args."""
        result = yield adder(3, 4)
        self.assertEqual(7, result)

    @inlineCallbacks
    def testSynchronousKw(self):
        """A callback must accept regular (non-Deferred) keyword args."""
        result = yield adderKw(x=3, y=4)
        self.assertEqual(7, result)

    @inlineCallbacks
    def testSynchronousMixed(self):
        """A callback must accept mixed regular and keyword args."""
        result = yield adderMixed(3, y=4)
        self.assertEqual(7, result)

    @inlineCallbacks
    def testOneDeferred(self):
        """A callback must accept a regular arg and a Deferred arg."""
        result = yield adder(3, succeed(4))
        self.assertEqual(7, result)

    @inlineCallbacks
    def testOneDeferredKw(self):
        """A callback must accept a keyword arg and a keyword Deferred arg."""
        result = yield adderKw(x=3, y=succeed(4))
        self.assertEqual(7, result)

    @inlineCallbacks
    def testOneDeferredMixed(self):
        """A callback must accept a regular arg and a keyword Deferred arg."""
        result = yield adderMixed(3, y=succeed(4))
        self.assertEqual(7, result)

    @inlineCallbacks
    def testTwoDeferreds(self):
        """A callback must accept a multiple Deferred args."""
        result = yield adder(succeed(3), succeed(4))
        self.assertEqual(7, result)

    @inlineCallbacks
    def testTwoDeferredsKw(self):
        """A callback must accept a multiple Deferred keyword args."""
        result = yield adderKw(x=succeed(3), y=succeed(4))
        self.assertEqual(7, result)

    @inlineCallbacks
    def testTwoDeferredsMixed(self):
        """A callback must accept mixed and keyword Deferred args."""
        result = yield adderMixed(succeed(3), y=succeed(4))
        self.assertEqual(7, result)

    @inlineCallbacks
    def testNested1(self):
        """It must be possible to nest callbacks."""
        result = yield adder(3, adder(succeed(3), succeed(4)))
        self.assertEqual(10, result)

    @inlineCallbacks
    def testNested2(self):
        """It must be possible to nest callbacks."""
        result = yield adder(1,
                             adder(
                                 adder(succeed(2), succeed(3)),
                                 adder(succeed(4), succeed(5))))
        self.assertEqual(15, result)

    @inlineCallbacks
    def testNestedKw(self):
        """It must be possible to nest callbacks with keyword args."""
        result = yield adderKw(x=3, y=adderKw(x=succeed(3), y=succeed(4)))
        self.assertEqual(10, result)

    @inlineCallbacks
    def testNestedMixed(self):
        """It must be possible to nest callbacks with mixed args."""
        result = yield adderMixed(3, y=adderMixed(succeed(3), y=succeed(4)))
        self.assertEqual(10, result)

    @inlineCallbacks
    def testAllThree(self):
        """It must be possible to nest callbacks with mixed args."""
        result = yield adderMixed(adder(3, adderKw(
            x=succeed(3), y=succeed(4))), y=5)
        self.assertEqual(15, result)

    def testCallbackFailure(self):
        """A callback must fail if one of its arguments is a Failure."""
        d = adder(3, fail(RuntimeError('oops')))
        return self.failUnlessFailure(d, RuntimeError)

    def testRaisingChecker(self):
        """An errback function must fail if it raises an error."""
        d = raisingChecker(fail(RuntimeError('oops')))
        return self.failUnlessFailure(d, RuntimeError)

    def testFailingChecker(self):
        """An errback function must fail if it returns a Failure."""
        d = failingChecker(fail(RuntimeError('oops')))
        return self.failUnlessFailure(d, RuntimeError)

    def testCheckerPassedAFailure(self):
        """An errback function must fail if it is passed a Failure."""
        d = failingChecker(Failure(RuntimeError('oops')))
        return self.failUnlessFailure(d, RuntimeError)

    def testErrbackCalledWithNoPositionalArg(self):
        """
        An errback called with no positional arg must raise
        L{ErrbackDecoratorError}.
        """
        @errback
        def checker(args):
            # The following raise will not happen, as the wrapper detects
            # the no-positional-arg call and raises ErrbackDecoratorError
            raise Exception()
        d = checker()
        return self.failUnlessFailure(d, ErrbackDecoratorError)

    @inlineCallbacks
    def testErrbackDecoratorErrorExceptionText(self):
        """
        L{ErrbackDecoratorError} failures should have error messages that
        indicate what went wrong, including naming the wrapped function.
        """
        @errback
        def checkMessage(failure):
            self.assertEqual("@errback decorated function 'checkerFunc' "
                             "invoked with no positional arguments.",
                             failure.value.args[0])
            return 10

        @errback
        def checkerFunc(args):
            # The following raise will not happen, as the wrapper detects
            # the no-positional-arg call and raises ErrbackDecoratorError
            raise Exception()
        result = yield checkMessage(checkerFunc())
        self.assertEqual(10, result)

    def testErrbackCalledWithNoPositionalArgButAKeywordArg(self):
        """
        An errback called with no positional arg (but a keyword arg) must raise
        L{ErrbackDecoratorError}.
        """
        @errback
        def checker(args):
            # The following raise will not happen, as the wrapper detects
            # the no-positional-arg call and raises ErrbackDecoratorError
            raise Exception()
        d = checker(arg=None)
        return self.failUnlessFailure(d, ErrbackDecoratorError)

    @inlineCallbacks
    def testErrbackRecoveryWithNonDeferredArgs(self):
        """
        An errback function must return its first arg when none of its
        args are C{Deferred}s.
        """
        @errback
        def checker(arg1, arg2):
            # The following raise will not happen, as the wrapper detects
            # that no arguments are Failures and does not call the wrapped
            # function.
            raise(Exception)
        result = yield checker(3, 4)
        self.assertEqual(3, result)

    @inlineCallbacks
    def testErrbackRecoveryWithDeferredArg(self):
        """
        An errback function must be able to return a non-error result when
        one of its args is a C{Deferred}.
        """
        result = yield adder(3, twoArgChecker(
            adder(3, fail(Exception('oops'))), 12))
        self.assertEqual(15, result)

    @inlineCallbacks
    def testErrbackRecoveryKw(self):
        """An errback function must be able to return a non-error result."""
        result = yield adder(3, twoArgCheckerKw(
            adder(3, fail(Exception('oops'))), default=12))
        self.assertEqual(15, result)

    @inlineCallbacks
    def testErrbackRecoveryMixedDefaultKeywordArgNotPassed(self):
        """An errback function with a keyword argument that has a default
        value must return a correct non-error result when that argument is
        not passed."""
        result = yield adder(3, threeArgCheckerMixed(
            adder(3, fail(Exception('oops'))), 6))
        self.assertEqual(9, result)

    @inlineCallbacks
    def testErrbackRecoveryMixedDefaultKeywordArgPassed(self):
        """An errback function with a keyword argument that has a default
        value must return a correct non-error result when that argument is
        passed."""
        result = yield adder(3, threeArgCheckerMixed(
            adder(3, fail(Exception('oops'))), 6, extra=10))
        self.assertEqual(19, result)

    @inlineCallbacks
    def testErrbackNotCalledIfNoError(self):
        """An errback function must not be called if no error has occurred."""
        @errback
        def checker(failure):
            raise Exception('Inconceivable')
        result = yield checker(adder(3, 4))
        self.assertEqual(7, result)

    @inlineCallbacks
    def testErrbackNotCalledTwiceIfNoError(self):
        """An errback function must cleanly pass along a non-error."""
        @errback
        def checker(failure):
            raise Exception('Inconceivable')
        result = yield checker(checker(adder(3, 4)))
        self.assertEqual(7, result)

    @inlineCallbacks
    def testNestedWithErrback(self):
        """It must be possible to nest callbacks with errbacks."""
        @errback
        def checker(failure):
            raise Exception('Inconceivable')
        result = yield adder(1,
                             adder(
                                 checker(adder(succeed(2), succeed(3))),
                                 checker(adder(succeed(4), succeed(5)))))
        self.assertEqual(15, result)

    @inlineCallbacks
    def testNestedMultiargWithErrback(self):
        """It must be possible to nest callbacks with errbacks."""
        @errback
        def checker(failure):
            raise Exception('Inconceivable')

        @callback
        def multiAdd(*args):
            return reduce(add, args, 0)
        result = yield multiAdd(1,
                                checker(multiAdd(succeed(2), succeed(3), 4)),
                                checker(multiAdd(succeed(5), succeed(6), 7)))
        self.assertEqual(28, result)

    def testErrbackPassedAFailureAndAnArg(self):
        """An errback receiving a C{Failure} and an arg must be called."""
        @errback
        def checker(failure, arg):
            return failure

        @callback
        def cb(result):
            raise Exception('Inconceivable')
        d = cb(checker(Failure(RuntimeError('oops')), 3))
        return self.failUnlessFailure(d, RuntimeError)

    def testErrbackPassedAnArgAndAFailure(self):
        """An errback receiving an arg and a C{Failure} must be called."""
        @errback
        def checker(arg, failure):
            return failure

        @callback
        def cb(result):
            raise Exception('Inconceivable')
        d = cb(checker(3, Failure(RuntimeError('oops'))))
        return self.failUnlessFailure(d, RuntimeError)

    def testErrbackPassedTwoDeferredsBothFail(self):
        """An errback must handle multiple failing C{Deferred} args."""
        @errback
        def checker(failure1, failure2):
            self.assertTrue(isinstance(failure1, Failure))
            self.assertTrue(isinstance(failure2, Failure))
            return failure1

        d = checker(fail(RuntimeError('oops')), fail(Exception('oops')))
        return self.failUnlessFailure(d, RuntimeError)

    def testErrbackPassedTwoDeferredsFirstFails(self):
        """
        An errback must handle multiple C{Deferred} args, the first of which
        fails.
        """
        @errback
        def checker(failure1, failure2):
            self.assertTrue(isinstance(failure1, Failure))
            self.assertEqual(5, failure2)
            return failure1

        d = checker(fail(RuntimeError('oops')), succeed(5))
        return self.failUnlessFailure(d, RuntimeError)

    def testErrbackPassedTwoDeferredsSecondFails(self):
        """
        An errback must handle multiple C{Deferred} args, the second of which
        fails.
        """
        @errback
        def checker(failure1, failure2):
            self.assertEqual(5, failure1)
            self.assertTrue(isinstance(failure2, Failure))
            return failure2

        d = checker(succeed(5), fail(RuntimeError('oops')))
        return self.failUnlessFailure(d, RuntimeError)

    def testErrbackPassedTwoDeferredsOneAsAKeywordFirstFails(self):
        """
        An errback must handle multiple C{Deferred} args, including one that
        is a keyword argument, in which the positional C{Deferred} fails.
        """
        @errback
        def checker(failure1, failure2=None):
            self.assertTrue(isinstance(failure1, Failure))
            self.assertEqual(5, failure2)
            return failure1

        d = checker(fail(RuntimeError('oops')), failure2=succeed(5))
        return self.failUnlessFailure(d, RuntimeError)

    def testErrbackPassedTwoDeferredsOneAsAKeywordSecondFails(self):
        """
        An errback must handle multiple C{Deferred} args, including one that
        is a keyword argument, in which the keyword C{Deferred} fails.
        """
        @errback
        def checker(failure1, failure2=None):
            self.assertEqual(5, failure1)
            self.assertTrue(isinstance(failure2, Failure))
            return failure2

        d = checker(succeed(5), failure2=fail(RuntimeError('oops')))
        return self.failUnlessFailure(d, RuntimeError)
