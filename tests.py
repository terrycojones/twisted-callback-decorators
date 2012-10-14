from operator import add
from twisted.internet.defer import inlineCallbacks, fail, succeed
from twisted.python.failure import Failure
from twisted.trial.unittest import TestCase
from decorate import callback, errback


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

    @inlineCallbacks
    def testErrbackRecovery(self):
        """An errback function must be able to return a non-error result."""
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
