import sys
import unittest

from pyramid import testing


py311plus = sys.version_info[:2] >= (3, 11)


class Test_excview_tween_factory(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, handler, registry=None):
        from pyramid.tweens import excview_tween_factory

        if registry is None:
            registry = self.config.registry
        return excview_tween_factory(handler, registry)

    def test_it_passthrough_no_exception(self):
        dummy_response = DummyResponse()

        def handler(request):
            return dummy_response

        tween = self._makeOne(handler)
        request = DummyRequest()
        result = tween(request)
        self.assertTrue(result is dummy_response)
        self.assertIsNone(request.exception)
        self.assertIsNone(request.exc_info)

    def test_it_catches_notfound(self):
        from pyramid.httpexceptions import HTTPNotFound
        from pyramid.request import Request

        self.config.add_notfound_view(lambda exc, request: exc)

        def handler(request):
            raise HTTPNotFound

        tween = self._makeOne(handler)
        request = Request.blank('/')
        request.registry = self.config.registry
        result = tween(request)
        self.assertEqual(result.status, '404 Not Found')
        self.assertIsInstance(request.exception, HTTPNotFound)
        self.assertEqual(request.exception, request.exc_info[1])

    def test_it_catches_with_predicate(self):
        from pyramid.request import Request
        from pyramid.response import Response

        def excview(request):
            return Response('foo')

        self.config.add_view(excview, context=ValueError, request_method='GET')

        def handler(request):
            raise ValueError

        tween = self._makeOne(handler)
        request = Request.blank('/')
        request.registry = self.config.registry
        result = tween(request)
        self.assertTrue(b'foo' in result.body)
        self.assertIsInstance(request.exception, ValueError)
        self.assertEqual(request.exception, request.exc_info[1])

    def test_it_reraises_on_mismatch(self):
        from pyramid.request import Request

        def excview(request):  # pragma: no cover
            pass

        self.config.add_view(excview, context=ValueError, request_method='GET')

        def handler(request):
            raise ValueError

        tween = self._makeOne(handler)
        request = Request.blank('/')
        request.registry = self.config.registry
        request.method = 'POST'
        self.assertRaises(ValueError, lambda: tween(request))
        self.assertIsNone(request.exception)
        self.assertIsNone(request.exc_info)

    def test_it_reraises_on_no_match(self):
        from pyramid.request import Request

        def handler(request):
            raise ValueError

        tween = self._makeOne(handler)
        request = Request.blank('/')
        request.registry = self.config.registry
        self.assertRaises(ValueError, lambda: tween(request))
        self.assertIsNone(request.exception)
        self.assertIsNone(request.exc_info)

    @unittest.skipUnless(py311plus, 'exception groups require Python 3.11+')
    def test_it_handles_exception_group(self):
        from pyramid.request import Request
        from pyramid.response import Response

        handled = []

        def leaf_view(exc, request):
            handled.append(exc)
            return Response('handled %s' % exc, status=418)

        def group_view(exc, request):
            results = request.exception_group_results
            return Response('aggregated %d leaves' % len(results), status=500)

        self.config.add_exception_view(leaf_view, context=ValueError)
        self.config.add_exception_view(leaf_view, context=KeyError)
        self.config.add_exception_group_view(group_view)

        def handler(request):
            inner = ExceptionGroup('inner', [ValueError('v1'), KeyError('k')])
            raise ExceptionGroup('outer', [inner, ValueError('v2')])

        tween = self._makeOne(handler)
        request = Request.blank('/')
        request.registry = self.config.registry
        result = tween(request)
        self.assertEqual(result.status_int, 500)
        self.assertEqual(result.body, b'aggregated 3 leaves')
        # each leaf was handled exactly once
        self.assertEqual(len(handled), 3)
        self.assertEqual(len(set(map(id, handled))), 3)
        self.assertIsInstance(request.exception, ExceptionGroup)

    @unittest.skipUnless(py311plus, 'exception groups require Python 3.11+')
    def test_it_reraises_unmatched_leaves_of_exception_group(self):
        from pyramid.request import Request
        from pyramid.response import Response

        def leaf_view(exc, request):
            return Response('handled', status=200)

        def group_view(exc, request):  # pragma: no cover
            raise AssertionError('must not be called')

        self.config.add_exception_view(leaf_view, context=ValueError)
        self.config.add_exception_group_view(group_view)

        def handler(request):
            raise ExceptionGroup('g', [ValueError('v'), RuntimeError('r')])

        tween = self._makeOne(handler)
        request = Request.blank('/')
        request.registry = self.config.registry
        with self.assertRaises(ExceptionGroup) as cm:
            tween(request)
        # only the unmatched leaf is reraised for outer layers
        remainder = cm.exception
        self.assertEqual(len(remainder.exceptions), 1)
        self.assertIsInstance(remainder.exceptions[0], RuntimeError)

    @unittest.skipUnless(py311plus, 'exception groups require Python 3.11+')
    def test_it_does_not_swallow_base_exception_group(self):
        from pyramid.request import Request
        from pyramid.response import Response

        def leaf_view(exc, request):  # pragma: no cover
            return Response('handled', status=500)

        def group_view(exc, request):  # pragma: no cover
            raise AssertionError('must not be called')

        self.config.add_exception_view(leaf_view, context=Exception)
        self.config.add_exception_group_view(group_view)

        def handler(request):
            raise BaseExceptionGroup(
                'g', [ValueError('v'), KeyboardInterrupt()]
            )

        tween = self._makeOne(handler)
        request = Request.blank('/')
        request.registry = self.config.registry
        # a BaseExceptionGroup is not an Exception; the tween never
        # catches it, so the cancellation propagates instead of
        # becoming a 500
        with self.assertRaises(BaseExceptionGroup):
            tween(request)


class DummyRequest:
    exception = None
    exc_info = None


class DummyResponse:
    pass
