import unittest

from pyramid import testing
from pyramid.response import Response


class ExceptionGroupViewProtocolTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeRequest(self, method='GET'):
        from pyramid.request import Request

        request = Request.blank('/', environ={'REQUEST_METHOD': method})
        request.registry = self.config.registry
        return request

    def _exc_info(self, exc):
        try:
            raise exc
        except BaseException:
            import sys

            return sys.exc_info()

    def test_nested_group_leaves_matched_individually(self):
        calls = []
        captured = {}

        def value_view(exc, request):
            calls.append(('value', exc))
            self.assertIs(request.exception, exc)
            return Response('value', status=400)

        def key_view(exc, request):
            calls.append(('key', exc))
            self.assertIs(request.exception, exc)
            return Response('key', status=400)

        def group_view(results, request):
            captured['results'] = results
            return Response('aggregated', status=200)

        self.config.add_exception_view(value_view, context=ValueError)
        self.config.add_exception_view(key_view, context=KeyError)
        self.config.add_exception_group_view(group_view)

        v1, v2, k = ValueError('v1'), ValueError('v2'), KeyError('k')
        inner = ExceptionGroup('inner', [k, v2])
        group = ExceptionGroup('outer', [v1, inner])

        request = self._makeRequest()
        response = request.invoke_exception_view(
            exc_info=self._exc_info(group)
        )

        self.assertEqual(response.text, 'aggregated')
        # every leaf was processed exactly once, depth-first
        self.assertEqual(
            calls, [('value', v1), ('key', k), ('value', v2)]
        )
        results = captured['results']
        self.assertIs(results.group, group)
        self.assertEqual(len(results.leaves), 3)
        # group paths are preserved per leaf
        self.assertEqual(results.leaves[0].path, (group,))
        self.assertEqual(results.leaves[1].path, (group, inner))
        self.assertEqual(results.leaves[2].path, (group, inner))
        # all leaves matched
        self.assertEqual(len(results.matched), 3)
        self.assertEqual(results.unmatched, [])
        # request state reflects the group after a successful render
        self.assertIs(request.exception, group)

    def test_context_predicates_select_view_per_leaf(self):
        calls = []

        class MessagePredicate:
            def __init__(self, val, config):
                self.val = val

            def text(self):
                return 'message = %s' % self.val

            phash = text

            def __call__(self, context, request):
                return context.args[0] == self.val

        def boom_view(exc, request):
            calls.append('boom')
            return Response('boom', status=400)

        def plain_view(exc, request):
            calls.append('plain')
            return Response('plain', status=400)

        self.config.add_view_predicate('message', MessagePredicate)
        self.config.add_exception_view(
            boom_view, context=ValueError, message='boom'
        )
        self.config.add_exception_view(plain_view, context=ValueError)
        self.config.add_exception_group_view()

        group = ExceptionGroup(
            'group', [ValueError('boom'), ValueError('other')]
        )
        request = self._makeRequest()
        response = request.invoke_exception_view(
            exc_info=self._exc_info(group)
        )

        # both leaves matched, each exactly once, same status so the
        # default group view returns the first response
        self.assertEqual(sorted(calls), ['boom', 'plain'])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.text, 'boom')

    def test_predicate_mismatch_leaf_falls_back_to_less_specific_view(self):
        calls = []

        def post_view(exc, request):
            calls.append('post')
            return Response('post', status=400)

        def any_view(exc, request):
            calls.append('any')
            return Response('any', status=400)

        self.config.add_exception_view(
            post_view, context=ValueError, request_method='POST'
        )
        self.config.add_exception_view(any_view, context=ValueError)
        self.config.add_exception_group_view()

        group = ExceptionGroup('group', [ValueError('x')])
        request = self._makeRequest(method='GET')
        response = request.invoke_exception_view(
            exc_info=self._exc_info(group)
        )
        self.assertEqual(calls, ['any'])
        self.assertEqual(response.text, 'any')

    def test_unmatched_leaves_reraised_preserving_structure(self):
        def value_view(exc, request):
            return Response('value', status=400)

        self.config.add_exception_view(value_view, context=ValueError)
        self.config.add_exception_group_view()

        v, t = ValueError('v'), TypeError('t')
        try:
            raise t
        except TypeError:
            pass  # give the leaf a traceback
        inner = ExceptionGroup('inner', [t])
        group = ExceptionGroup('outer', [v, inner])

        request = self._makeRequest()
        exc_info = self._exc_info(group)
        with self.assertRaises(ExceptionGroup) as cm:
            request.invoke_exception_view(exc_info=exc_info)

        derived = cm.exception
        self.assertIsNot(derived, group)
        # only the unmatched leaf remains, nesting structure preserved
        self.assertEqual(len(derived.exceptions), 1)
        derived_inner = derived.exceptions[0]
        self.assertIsInstance(derived_inner, ExceptionGroup)
        self.assertEqual(derived_inner.exceptions, (t,))
        self.assertIs(derived_inner.exceptions[0], t)
        # the original exception chain stays traceable
        self.assertIs(derived.__cause__, group)
        # the leaf keeps its own traceback
        self.assertIsNotNone(t.__traceback__)

    def test_all_unmatched_reraises_original_group(self):
        self.config.add_exception_group_view()

        group = ExceptionGroup('group', [TypeError('t'), KeyError('k')])
        request = self._makeRequest()
        exc_info = self._exc_info(group)
        with self.assertRaises(ExceptionGroup) as cm:
            request.invoke_exception_view(exc_info=exc_info)
        self.assertIs(cm.exception, group)

    def test_baseexception_leaves_are_not_swallowed_into_500(self):
        def value_view(exc, request):
            return Response('value', status=400)

        self.config.add_exception_view(value_view, context=ValueError)
        self.config.add_exception_group_view()

        cancelled = KeyboardInterrupt('cancel')
        group = BaseExceptionGroup(
            'group', [ValueError('v'), cancelled]
        )
        request = self._makeRequest()
        exc_info = self._exc_info(group)
        with self.assertRaises(BaseExceptionGroup) as cm:
            request.invoke_exception_view(exc_info=exc_info)

        derived = cm.exception
        self.assertEqual(derived.exceptions, (cancelled,))
        self.assertIs(derived.__cause__, group)

    def test_raising_exception_view_propagates_and_leaf_handled_once(self):
        calls = []

        def value_view(exc, request):
            calls.append('value')
            return Response('value', status=400)

        def key_view(exc, request):
            calls.append('key')
            raise RuntimeError('view exploded')

        self.config.add_exception_view(value_view, context=ValueError)
        self.config.add_exception_view(key_view, context=KeyError)
        self.config.add_exception_group_view()

        group = ExceptionGroup('group', [ValueError('v'), KeyError('k')])
        request = self._makeRequest()
        with self.assertRaises(RuntimeError):
            request.invoke_exception_view(exc_info=self._exc_info(group))

        # each leaf was processed at most once; no retries happened
        self.assertEqual(calls, ['value', 'key'])

    def test_default_group_view_does_not_pick_first_leaf_status(self):
        def value_view(exc, request):
            return Response('value', status=400)

        def key_view(exc, request):
            return Response('key', status=404)

        self.config.add_exception_view(value_view, context=ValueError)
        self.config.add_exception_view(key_view, context=KeyError)
        self.config.add_exception_group_view()

        group = ExceptionGroup('group', [ValueError('v'), KeyError('k')])
        request = self._makeRequest()
        response = request.invoke_exception_view(
            exc_info=self._exc_info(group)
        )
        self.assertEqual(response.status_code, 500)
        self.assertIn('conflicting response statuses', response.text)

    def test_default_group_view_same_status_returns_response(self):
        def value_view(exc, request):
            return Response('value', status=400)

        def key_view(exc, request):
            return Response('key', status=400)

        self.config.add_exception_view(value_view, context=ValueError)
        self.config.add_exception_view(key_view, context=KeyError)
        self.config.add_exception_group_view()

        group = ExceptionGroup('group', [ValueError('v'), KeyError('k')])
        request = self._makeRequest()
        response = request.invoke_exception_view(
            exc_info=self._exc_info(group)
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.text, 'value')

    def test_no_group_view_registered_treats_group_as_plain_exception(self):
        def exc_view(exc, request):
            return Response('plain', status=500)

        self.config.add_exception_view(exc_view, context=Exception)

        group = ExceptionGroup('group', [ValueError('v')])
        request = self._makeRequest()
        response = request.invoke_exception_view(
            exc_info=self._exc_info(group)
        )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.text, 'plain')

    def test_end_to_end_through_router(self):
        def body_view(request):
            raise ExceptionGroup('group', [ValueError('v'), KeyError('k')])

        def value_view(exc, request):
            return Response('value', status=400)

        def key_view(exc, request):
            return Response('key', status=400)

        self.config.add_route('home', '/')
        self.config.add_view(body_view, route_name='home')
        self.config.add_exception_view(value_view, context=ValueError)
        self.config.add_exception_view(key_view, context=KeyError)
        self.config.add_exception_group_view()
        app = self.config.make_wsgi_app()

        environ = {
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '',
            'PATH_INFO': '/',
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '80',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.input': None,
            'wsgi.errors': None,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
        }
        captured = {}

        def start_response(status, headers):
            captured['status'] = status

        body = b''.join(app(environ, start_response))
        self.assertTrue(captured['status'].startswith('400'))
        self.assertEqual(body, b'value')


class AddExceptionGroupViewDirectiveTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _get_utility(self):
        from pyramid.interfaces import IExceptionGroupView

        return self.config.registry.queryUtility(IExceptionGroupView)

    def test_registers_default_view(self):
        from pyramid.excgroup import default_exception_group_view

        self.config.add_exception_group_view()
        self.assertIs(self._get_utility(), default_exception_group_view)

    def test_registers_custom_view(self):
        def group_view(results, request):
            return Response('custom')

        self.config.add_exception_group_view(group_view)
        self.assertIs(self._get_utility(), group_view)

    def test_not_registered_by_default(self):
        self.assertIsNone(self._get_utility())


class ExceptionGroupResultsTests(unittest.TestCase):
    def test_derive_unmatched_none_when_all_matched(self):
        from pyramid.excgroup import ExceptionGroupResults, LeafResult

        group = ExceptionGroup('group', [ValueError('v')])
        results = ExceptionGroupResults(
            group, [LeafResult(group.exceptions[0], (group,), Response())]
        )
        self.assertIsNone(results.derive_unmatched())

    def test_walk_leaves_paths(self):
        from pyramid.excgroup import walk_leaves

        v, k = ValueError('v'), KeyError('k')
        inner = ExceptionGroup('inner', [k])
        group = ExceptionGroup('outer', [v, inner])
        self.assertEqual(
            list(walk_leaves(group)),
            [(v, (group,)), (k, (group, inner))],
        )
