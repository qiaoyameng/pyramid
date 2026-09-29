import sys
import unittest
from zope.interface import Interface, implementer

from pyramid import testing
from pyramid.interfaces import IRequest, IResponse

py311plus = sys.version_info[:2] >= (3, 11)


class BaseTest:
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _registerView(self, reg, app, name):
        from pyramid.interfaces import IViewClassifier

        for_ = (IViewClassifier, IRequest, IContext)
        from pyramid.interfaces import IView

        reg.registerAdapter(app, for_, IView, name)

    def _makeEnviron(self, **extras):
        environ = {
            'wsgi.url_scheme': 'http',
            'wsgi.version': (1, 0),
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '8080',
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/',
        }
        environ.update(extras)
        return environ

    def _makeRequest(self, **environ):
        from pyramid.registry import Registry
        from pyramid.request import Request

        environ = self._makeEnviron(**environ)
        request = Request(environ)
        request.registry = Registry()
        return request

    def _makeContext(self):
        from zope.interface import directlyProvides

        context = DummyContext()
        directlyProvides(context, IContext)
        return context


class Test_notfound_view_config(BaseTest, unittest.TestCase):
    def _makeOne(self, **kw):
        from pyramid.view import notfound_view_config

        return notfound_view_config(**kw)

    def test_ctor(self):
        inst = self._makeOne(
            attr='attr', path_info='path_info', append_slash=True
        )
        self.assertEqual(
            inst.__dict__,
            {'attr': 'attr', 'path_info': 'path_info', 'append_slash': True},
        )

    def test_it_function(self):
        def view(request):  # pragma: no cover
            pass

        decorator = self._makeOne(
            attr='attr', renderer='renderer', append_slash=True
        )
        venusian = DummyVenusian()
        decorator.venusian = venusian
        wrapped = decorator(view)
        self.assertTrue(wrapped is view)
        config = call_venusian(venusian)
        settings = config.settings
        self.assertEqual(
            settings,
            [
                {
                    'attr': 'attr',
                    'venusian': venusian,
                    'append_slash': True,
                    'renderer': 'renderer',
                    '_info': 'codeinfo',
                    'view': None,
                }
            ],
        )

    def test_it_class(self):
        decorator = self._makeOne()
        venusian = DummyVenusian()
        decorator.venusian = venusian
        decorator.venusian.info.scope = 'class'

        class view:
            pass

        wrapped = decorator(view)
        self.assertTrue(wrapped is view)
        config = call_venusian(venusian)
        settings = config.settings
        self.assertEqual(len(settings), 1)
        self.assertEqual(len(settings[0]), 4)
        self.assertEqual(settings[0]['venusian'], venusian)
        self.assertEqual(settings[0]['view'], None)  # comes from call_venusian
        self.assertEqual(settings[0]['attr'], 'view')
        self.assertEqual(settings[0]['_info'], 'codeinfo')

    def test_call_with_venusian_args(self):
        decorator = self._makeOne(_depth=1, _category='foo')
        venusian = DummyVenusian()
        decorator.venusian = venusian

        def foo():  # pragma: no cover
            pass

        decorator(foo)
        attachments = venusian.attachments
        category = attachments[0][2]
        depth = attachments[0][3]
        self.assertEqual(depth, 2)
        self.assertEqual(category, 'foo')


class Test_forbidden_view_config(BaseTest, unittest.TestCase):
    def _makeOne(self, **kw):
        from pyramid.view import forbidden_view_config

        return forbidden_view_config(**kw)

    def test_ctor(self):
        inst = self._makeOne(attr='attr', path_info='path_info')
        self.assertEqual(
            inst.__dict__, {'attr': 'attr', 'path_info': 'path_info'}
        )

    def test_it_function(self):
        def view(request):  # pragma: no cover
            pass

        decorator = self._makeOne(attr='attr', renderer='renderer')
        venusian = DummyVenusian()
        decorator.venusian = venusian
        wrapped = decorator(view)
        self.assertTrue(wrapped is view)
        config = call_venusian(venusian)
        settings = config.settings
        self.assertEqual(
            settings,
            [
                {
                    'attr': 'attr',
                    'venusian': venusian,
                    'renderer': 'renderer',
                    '_info': 'codeinfo',
                    'view': None,
                }
            ],
        )

    def test_it_class(self):
        decorator = self._makeOne()
        venusian = DummyVenusian()
        decorator.venusian = venusian
        decorator.venusian.info.scope = 'class'

        class view:
            pass

        wrapped = decorator(view)
        self.assertTrue(wrapped is view)
        config = call_venusian(venusian)
        settings = config.settings
        self.assertEqual(len(settings), 1)
        self.assertEqual(len(settings[0]), 4)
        self.assertEqual(settings[0]['venusian'], venusian)
        self.assertEqual(settings[0]['view'], None)  # comes from call_venusian
        self.assertEqual(settings[0]['attr'], 'view')
        self.assertEqual(settings[0]['_info'], 'codeinfo')

    def test_call_with_venusian_args(self):
        decorator = self._makeOne(_depth=1, _category='foo')
        venusian = DummyVenusian()
        decorator.venusian = venusian

        def foo():  # pragma: no cover
            pass

        decorator(foo)
        attachments = venusian.attachments
        category = attachments[0][2]
        depth = attachments[0][3]
        self.assertEqual(depth, 2)
        self.assertEqual(category, 'foo')


class Test_exception_view_config(BaseTest, unittest.TestCase):
    def _makeOne(self, *args, **kw):
        from pyramid.view import exception_view_config

        return exception_view_config(*args, **kw)

    def test_ctor(self):
        inst = self._makeOne(context=Exception, path_info='path_info')
        self.assertEqual(
            inst.__dict__, {'context': Exception, 'path_info': 'path_info'}
        )

    def test_ctor_positional_exception(self):
        inst = self._makeOne(Exception, path_info='path_info')
        self.assertEqual(
            inst.__dict__, {'context': Exception, 'path_info': 'path_info'}
        )

    def test_ctor_positional_extras(self):
        from pyramid.exceptions import ConfigurationError

        self.assertRaises(
            ConfigurationError, lambda: self._makeOne(Exception, True)
        )

    def test_it_function(self):
        def view(request):  # pragma: no cover
            pass

        decorator = self._makeOne(context=Exception, renderer='renderer')
        venusian = DummyVenusian()
        decorator.venusian = venusian
        wrapped = decorator(view)
        self.assertTrue(wrapped is view)
        config = call_venusian(venusian)
        settings = config.settings
        self.assertEqual(
            settings,
            [
                {
                    'venusian': venusian,
                    'context': Exception,
                    'renderer': 'renderer',
                    '_info': 'codeinfo',
                    'view': None,
                }
            ],
        )

    def test_it_class(self):
        decorator = self._makeOne()
        venusian = DummyVenusian()
        decorator.venusian = venusian
        decorator.venusian.info.scope = 'class'

        class view:
            pass

        wrapped = decorator(view)
        self.assertTrue(wrapped is view)
        config = call_venusian(venusian)
        settings = config.settings
        self.assertEqual(len(settings), 1)
        self.assertEqual(len(settings[0]), 4)
        self.assertEqual(settings[0]['venusian'], venusian)
        self.assertEqual(settings[0]['view'], None)  # comes from call_venusian
        self.assertEqual(settings[0]['attr'], 'view')
        self.assertEqual(settings[0]['_info'], 'codeinfo')

    def test_call_with_venusian_args(self):
        decorator = self._makeOne(_depth=1, _category='foo')
        venusian = DummyVenusian()
        decorator.venusian = venusian

        def foo():  # pragma: no cover
            pass

        decorator(foo)
        attachments = venusian.attachments
        category = attachments[0][2]
        depth = attachments[0][3]
        self.assertEqual(depth, 2)
        self.assertEqual(category, 'foo')


class Test_exception_group_view_config(BaseTest, unittest.TestCase):
    def _makeOne(self, *args, **kw):
        from pyramid.view import exception_group_view_config

        return exception_group_view_config(*args, **kw)

    def test_ctor(self):
        inst = self._makeOne(context=Exception, path_info='path_info')
        self.assertEqual(
            inst.__dict__, {'context': Exception, 'path_info': 'path_info'}
        )

    def test_ctor_positional_exception(self):
        inst = self._makeOne(Exception, path_info='path_info')
        self.assertEqual(
            inst.__dict__, {'context': Exception, 'path_info': 'path_info'}
        )

    def test_ctor_positional_extras(self):
        from pyramid.exceptions import ConfigurationError

        self.assertRaises(
            ConfigurationError, lambda: self._makeOne(Exception, True)
        )

    def test_it_function(self):
        def view(request):  # pragma: no cover
            pass

        decorator = self._makeOne(context=Exception, renderer='renderer')
        venusian = DummyVenusian()
        decorator.venusian = venusian
        wrapped = decorator(view)
        self.assertTrue(wrapped is view)
        config = call_venusian(venusian)
        settings = config.settings
        self.assertEqual(
            settings,
            [
                {
                    'venusian': venusian,
                    'context': Exception,
                    'renderer': 'renderer',
                    '_info': 'codeinfo',
                    'view': None,
                }
            ],
        )

    def test_it_class(self):
        decorator = self._makeOne()
        venusian = DummyVenusian()
        decorator.venusian = venusian
        decorator.venusian.info.scope = 'class'

        class view:
            pass

        wrapped = decorator(view)
        self.assertTrue(wrapped is view)
        config = call_venusian(venusian)
        settings = config.settings
        self.assertEqual(len(settings), 1)
        self.assertEqual(len(settings[0]), 4)
        self.assertEqual(settings[0]['venusian'], venusian)
        self.assertEqual(settings[0]['view'], None)  # comes from call_venusian
        self.assertEqual(settings[0]['attr'], 'view')
        self.assertEqual(settings[0]['_info'], 'codeinfo')

    def test_call_with_venusian_args(self):
        decorator = self._makeOne(_depth=1, _category='foo')
        venusian = DummyVenusian()
        decorator.venusian = venusian

        def foo():  # pragma: no cover
            pass

        decorator(foo)
        attachments = venusian.attachments
        category = attachments[0][2]
        depth = attachments[0][3]
        self.assertEqual(depth, 2)
        self.assertEqual(category, 'foo')


class RenderViewToResponseTests(BaseTest, unittest.TestCase):
    def _callFUT(self, *arg, **kw):
        from pyramid.view import render_view_to_response

        return render_view_to_response(*arg, **kw)

    def test_call_no_view_registered(self):
        request = self._makeRequest()
        context = self._makeContext()
        result = self._callFUT(context, request, name='notregistered')
        self.assertEqual(result, None)

    def test_call_no_registry_on_request(self):
        request = self._makeRequest()
        del request.registry
        context = self._makeContext()
        result = self._callFUT(context, request, name='notregistered')
        self.assertEqual(result, None)

    def test_call_view_registered_secure(self):
        request = self._makeRequest()
        context = self._makeContext()
        response = DummyResponse()
        view = make_view(response)
        self._registerView(request.registry, view, 'registered')
        response = self._callFUT(
            context, request, name='registered', secure=True
        )
        self.assertEqual(response.status, '200 OK')

    def test_call_view_registered_insecure_no_call_permissive(self):
        context = self._makeContext()
        request = self._makeRequest()
        response = DummyResponse()
        view = make_view(response)
        self._registerView(request.registry, view, 'registered')
        response = self._callFUT(
            context, request, name='registered', secure=False
        )
        self.assertEqual(response.status, '200 OK')

    def test_call_view_registered_insecure_with_call_permissive(self):
        context = self._makeContext()
        request = self._makeRequest()
        response = DummyResponse()
        view = make_view(response)

        def anotherview(context, request):
            return DummyResponse('anotherview')

        view.__call_permissive__ = anotherview
        self._registerView(request.registry, view, 'registered')
        response = self._callFUT(
            context, request, name='registered', secure=False
        )
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.app_iter, ['anotherview'])

    def test_call_view_with_request_iface_on_request(self):
        # See https://github.com/Pylons/pyramid/issues/1643
        from zope.interface import Interface

        class IWontBeFound(Interface):
            pass

        context = self._makeContext()
        request = self._makeRequest()
        request.request_iface = IWontBeFound
        response = DummyResponse('aview')
        view = make_view(response)
        self._registerView(request.registry, view, 'aview')
        response = self._callFUT(context, request, name='aview')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.app_iter, ['aview'])


class RenderViewToIterableTests(BaseTest, unittest.TestCase):
    def _callFUT(self, *arg, **kw):
        from pyramid.view import render_view_to_iterable

        return render_view_to_iterable(*arg, **kw)

    def test_call_no_view_registered(self):
        request = self._makeRequest()
        context = self._makeContext()
        result = self._callFUT(context, request, name='notregistered')
        self.assertEqual(result, None)

    def test_call_view_registered_secure(self):
        request = self._makeRequest()
        context = self._makeContext()
        response = DummyResponse()
        view = make_view(response)
        self._registerView(request.registry, view, 'registered')
        iterable = self._callFUT(
            context, request, name='registered', secure=True
        )
        self.assertEqual(iterable, ())

    def test_call_view_registered_insecure_no_call_permissive(self):
        context = self._makeContext()
        request = self._makeRequest()
        response = DummyResponse()
        view = make_view(response)
        self._registerView(request.registry, view, 'registered')
        iterable = self._callFUT(
            context, request, name='registered', secure=False
        )
        self.assertEqual(iterable, ())

    def test_call_view_registered_insecure_with_call_permissive(self):
        context = self._makeContext()
        request = self._makeRequest()
        response = DummyResponse()
        view = make_view(response)

        def anotherview(context, request):
            return DummyResponse(b'anotherview')

        view.__call_permissive__ = anotherview
        self._registerView(request.registry, view, 'registered')
        iterable = self._callFUT(
            context, request, name='registered', secure=False
        )
        self.assertEqual(iterable, [b'anotherview'])

    def test_verify_output_bytestring(self):
        from pyramid.config import Configurator
        from pyramid.request import Request
        from pyramid.view import render_view

        config = Configurator(settings={})

        def view(request):
            request.response.text = '<body></body>'
            return request.response

        config.add_view(name='test', view=view)
        config.commit()

        r = Request({})
        r.registry = config.registry
        self.assertEqual(render_view(object(), r, 'test'), b'<body></body>')

    def test_call_request_has_no_registry(self):
        request = self._makeRequest()
        del request.registry
        registry = self.config.registry
        context = self._makeContext()
        response = DummyResponse()
        view = make_view(response)
        self._registerView(registry, view, 'registered')
        iterable = self._callFUT(
            context, request, name='registered', secure=True
        )
        self.assertEqual(iterable, ())


class RenderViewTests(BaseTest, unittest.TestCase):
    def _callFUT(self, *arg, **kw):
        from pyramid.view import render_view

        return render_view(*arg, **kw)

    def test_call_no_view_registered(self):
        request = self._makeRequest()
        context = self._makeContext()
        result = self._callFUT(context, request, name='notregistered')
        self.assertEqual(result, None)

    def test_call_view_registered_secure(self):
        request = self._makeRequest()
        context = self._makeContext()
        response = DummyResponse()
        view = make_view(response)
        self._registerView(request.registry, view, 'registered')
        s = self._callFUT(context, request, name='registered', secure=True)
        self.assertEqual(s, b'')

    def test_call_view_registered_insecure_no_call_permissive(self):
        context = self._makeContext()
        request = self._makeRequest()
        response = DummyResponse()
        view = make_view(response)
        self._registerView(request.registry, view, 'registered')
        s = self._callFUT(context, request, name='registered', secure=False)
        self.assertEqual(s, b'')

    def test_call_view_registered_insecure_with_call_permissive(self):
        context = self._makeContext()
        request = self._makeRequest()
        response = DummyResponse()
        view = make_view(response)

        def anotherview(context, request):
            return DummyResponse(b'anotherview')

        view.__call_permissive__ = anotherview
        self._registerView(request.registry, view, 'registered')
        s = self._callFUT(context, request, name='registered', secure=False)
        self.assertEqual(s, b'anotherview')


class TestViewConfigDecorator(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _getTargetClass(self):
        from pyramid.view import view_config

        return view_config

    def _makeOne(self, *arg, **kw):
        return self._getTargetClass()(*arg, **kw)

    def test_create_defaults(self):
        decorator = self._makeOne()
        self.assertEqual(list(decorator.__dict__.keys()), ['_info'])

    def test_create_info(self):
        target = self._getTargetClass()
        decorator = target()
        info = decorator._info
        self.assertEqual(info[2], 'test_create_info')
        self.assertEqual(info[3], 'decorator = target()')

    def test_create_info_depth(self):
        target = self._getTargetClass()

        def make():
            return target(_depth=1)

        decorator = make()
        info = decorator._info
        self.assertEqual(info[2], 'test_create_info_depth')
        self.assertEqual(info[3], 'decorator = make()')

    def test_create_context_trumps_for(self):
        decorator = self._makeOne(context='123', for_='456')
        self.assertEqual(decorator.context, '123')

    def test_create_for_trumps_context_None(self):
        decorator = self._makeOne(context=None, for_='456')
        self.assertEqual(decorator.context, '456')

    def test_create_nondefaults(self):
        decorator = self._makeOne(
            name=None,
            request_type=None,
            for_=None,
            permission='foo',
            mapper='mapper',
            decorator='decorator',
            match_param='match_param',
        )
        self.assertEqual(decorator.name, None)
        self.assertEqual(decorator.request_type, None)
        self.assertEqual(decorator.context, None)
        self.assertEqual(decorator.permission, 'foo')
        self.assertEqual(decorator.mapper, 'mapper')
        self.assertEqual(decorator.decorator, 'decorator')
        self.assertEqual(decorator.match_param, 'match_param')

    def test_create_with_other_predicates(self):
        decorator = self._makeOne(foo=1)
        self.assertEqual(decorator.foo, 1)

    def test_create_decorator_tuple(self):
        decorator = self._makeOne(decorator=('decorator1', 'decorator2'))
        self.assertEqual(decorator.decorator, ('decorator1', 'decorator2'))

    def test_call_function(self):
        decorator = self._makeOne()
        venusian = DummyVenusian()
        decorator.venusian = venusian

        def foo():  # pragma: no cover
            pass

        wrapped = decorator(foo)
        self.assertTrue(wrapped is foo)
        config = call_venusian(venusian)
        settings = config.settings
        self.assertEqual(len(settings), 1)
        self.assertEqual(len(settings), 1)
        self.assertEqual(len(settings[0]), 3)
        self.assertEqual(settings[0]['venusian'], venusian)
        self.assertEqual(settings[0]['view'], None)  # comes from call_venusian

    def test_call_class(self):
        decorator = self._makeOne()
        venusian = DummyVenusian()
        decorator.venusian = venusian
        decorator.venusian.info.scope = 'class'

        class foo:
            pass

        wrapped = decorator(foo)
        self.assertTrue(wrapped is foo)
        config = call_venusian(venusian)
        settings = config.settings
        self.assertEqual(len(settings), 1)
        self.assertEqual(len(settings[0]), 4)
        self.assertEqual(settings[0]['venusian'], venusian)
        self.assertEqual(settings[0]['view'], None)  # comes from call_venusian
        self.assertEqual(settings[0]['attr'], 'foo')

    def test_call_class_attr_already_set(self):
        decorator = self._makeOne(attr='abc')
        venusian = DummyVenusian()
        decorator.venusian = venusian
        decorator.venusian.info.scope = 'class'

        class foo:
            pass

        wrapped = decorator(foo)
        self.assertTrue(wrapped is foo)
        config = call_venusian(venusian)
        settings = config.settings
        self.assertEqual(len(settings), 1)
        self.assertEqual(len(settings[0]), 4)
        self.assertEqual(settings[0]['venusian'], venusian)
        self.assertEqual(settings[0]['view'], None)  # comes from call_venusian
        self.assertEqual(settings[0]['attr'], 'abc')

    def test_stacking(self):
        decorator1 = self._makeOne(name='1')
        venusian1 = DummyVenusian()
        decorator1.venusian = venusian1
        venusian2 = DummyVenusian()
        decorator2 = self._makeOne(name='2')
        decorator2.venusian = venusian2

        def foo():  # pragma: no cover
            pass

        wrapped1 = decorator1(foo)
        wrapped2 = decorator2(wrapped1)
        self.assertTrue(wrapped1 is foo)
        self.assertTrue(wrapped2 is foo)
        config1 = call_venusian(venusian1)
        self.assertEqual(len(config1.settings), 1)
        self.assertEqual(config1.settings[0]['name'], '1')
        config2 = call_venusian(venusian2)
        self.assertEqual(len(config2.settings), 1)
        self.assertEqual(config2.settings[0]['name'], '2')

    def test_call_as_method(self):
        decorator = self._makeOne()
        venusian = DummyVenusian()
        decorator.venusian = venusian
        decorator.venusian.info.scope = 'class'

        def foo(self):  # pragma: no cover
            pass

        def bar(self):  # pragma: no cover
            pass

        class foo:
            foomethod = decorator(foo)
            barmethod = decorator(bar)

        config = call_venusian(venusian)
        settings = config.settings
        self.assertEqual(len(settings), 2)
        self.assertEqual(settings[0]['attr'], 'foo')
        self.assertEqual(settings[1]['attr'], 'bar')

    def test_with_custom_predicates(self):
        decorator = self._makeOne(custom_predicates=(1,))
        venusian = DummyVenusian()
        decorator.venusian = venusian

        def foo(context, request):  # pragma: no cover
            pass

        decorated = decorator(foo)
        self.assertTrue(decorated is foo)
        config = call_venusian(venusian)
        settings = config.settings
        self.assertEqual(settings[0]['custom_predicates'], (1,))

    def test_call_with_renderer_string(self):
        import tests

        decorator = self._makeOne(renderer='fixtures/minimal.pt')
        venusian = DummyVenusian()
        decorator.venusian = venusian

        def foo():  # pragma: no cover
            pass

        wrapped = decorator(foo)
        self.assertTrue(wrapped is foo)
        config = call_venusian(venusian)
        settings = config.settings
        self.assertEqual(len(settings), 1)
        renderer = settings[0]['renderer']
        self.assertEqual(renderer, 'fixtures/minimal.pt')
        self.assertEqual(config.pkg, tests)

    def test_call_with_renderer_dict(self):
        import tests

        decorator = self._makeOne(renderer={'a': 1})
        venusian = DummyVenusian()
        decorator.venusian = venusian

        def foo():  # pragma: no cover
            pass

        wrapped = decorator(foo)
        self.assertTrue(wrapped is foo)
        config = call_venusian(venusian)
        settings = config.settings
        self.assertEqual(len(settings), 1)
        self.assertEqual(settings[0]['renderer'], {'a': 1})
        self.assertEqual(config.pkg, tests)

    def test_call_with_renderer_IRendererInfo(self):
        from pyramid.interfaces import IRendererInfo
        import tests

        @implementer(IRendererInfo)
        class DummyRendererHelper:
            pass

        renderer_helper = DummyRendererHelper()
        decorator = self._makeOne(renderer=renderer_helper)
        venusian = DummyVenusian()
        decorator.venusian = venusian

        def foo():  # pragma: no cover
            pass

        wrapped = decorator(foo)
        self.assertTrue(wrapped is foo)
        context = DummyVenusianContext()
        config = call_venusian(venusian, context)
        settings = config.settings
        self.assertEqual(len(settings), 1)
        renderer = settings[0]['renderer']
        self.assertTrue(renderer is renderer_helper)
        self.assertEqual(config.pkg, tests)

    def test_call_withdepth(self):
        decorator = self._makeOne(_depth=1)
        venusian = DummyVenusian()
        decorator.venusian = venusian

        def foo():  # pragma: no cover
            pass

        decorator(foo)
        attachments = venusian.attachments
        depth = attachments[0][3]
        self.assertEqual(depth, 2)

    def test_call_withoutcategory(self):
        decorator = self._makeOne()
        venusian = DummyVenusian()
        decorator.venusian = venusian

        def foo():  # pragma: no cover
            pass

        decorator(foo)
        attachments = venusian.attachments
        category = attachments[0][2]
        self.assertEqual(category, 'pyramid')

    def test_call_withcategory(self):
        decorator = self._makeOne(_category='not_pyramid')
        venusian = DummyVenusian()
        decorator.venusian = venusian

        def foo():  # pragma: no cover
            pass

        decorator(foo)
        attachments = venusian.attachments
        category = attachments[0][2]
        self.assertEqual(category, 'not_pyramid')


class Test_append_slash_notfound_view(BaseTest, unittest.TestCase):
    def _callFUT(self, context, request):
        from pyramid.view import append_slash_notfound_view

        return append_slash_notfound_view(context, request)

    def _registerMapper(self, reg, match=True):
        from pyramid.interfaces import IRoutesMapper

        class DummyRoute:
            def __init__(self, val):
                self.val = val

            def match(self, path):
                return self.val

        class DummyMapper:
            def __init__(self):
                self.routelist = [DummyRoute(match)]

            def get_routes(self):
                return self.routelist

        mapper = DummyMapper()
        reg.registerUtility(mapper, IRoutesMapper)
        return mapper

    def test_context_is_not_exception(self):
        request = self._makeRequest(PATH_INFO='/abc')
        request.exception = ExceptionResponse()
        context = DummyContext()
        response = self._callFUT(context, request)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.app_iter, ['Not Found'])

    def test_no_mapper(self):
        request = self._makeRequest(PATH_INFO='/abc')
        context = ExceptionResponse()
        response = self._callFUT(context, request)
        self.assertEqual(response.status, '404 Not Found')

    def test_no_path(self):
        request = self._makeRequest()
        context = ExceptionResponse()
        self._registerMapper(request.registry, True)
        response = self._callFUT(context, request)
        self.assertEqual(response.status, '404 Not Found')

    def test_mapper_path_already_slash_ending(self):
        request = self._makeRequest(PATH_INFO='/abc/')
        context = ExceptionResponse()
        self._registerMapper(request.registry, True)
        response = self._callFUT(context, request)
        self.assertEqual(response.status, '404 Not Found')

    def test_no_route_matches(self):
        request = self._makeRequest(PATH_INFO='/abc')
        context = ExceptionResponse()
        mapper = self._registerMapper(request.registry, True)
        mapper.routelist[0].val = None
        response = self._callFUT(context, request)
        self.assertEqual(response.status, '404 Not Found')

    def test_matches(self):
        request = self._makeRequest(PATH_INFO='/abc')
        context = ExceptionResponse()
        self._registerMapper(request.registry, True)
        response = self._callFUT(context, request)
        self.assertEqual(response.status, '307 Temporary Redirect')
        self.assertEqual(response.location, '/abc/')

    def test_matches_with_script_name(self):
        request = self._makeRequest(PATH_INFO='/abc', SCRIPT_NAME='/foo')
        context = ExceptionResponse()
        self._registerMapper(request.registry, True)
        response = self._callFUT(context, request)
        self.assertEqual(response.status, '307 Temporary Redirect')
        self.assertEqual(response.location, '/foo/abc/')

    def test_with_query_string(self):
        request = self._makeRequest(PATH_INFO='/abc', QUERY_STRING='a=1&b=2')
        context = ExceptionResponse()
        self._registerMapper(request.registry, True)
        response = self._callFUT(context, request)
        self.assertEqual(response.status, '307 Temporary Redirect')
        self.assertEqual(response.location, '/abc/?a=1&b=2')


class TestAppendSlashNotFoundViewFactory(BaseTest, unittest.TestCase):
    def _makeOne(self, notfound_view):
        from pyramid.view import AppendSlashNotFoundViewFactory

        return AppendSlashNotFoundViewFactory(notfound_view)

    def test_custom_notfound_view(self):
        request = self._makeRequest(PATH_INFO='/abc')
        context = ExceptionResponse()

        def custom_notfound(context, request):
            return 'OK'

        view = self._makeOne(custom_notfound)
        response = view(context, request)
        self.assertEqual(response, 'OK')


class Test_default_exceptionresponse_view(unittest.TestCase):
    def _callFUT(self, context, request):
        from pyramid.view import default_exceptionresponse_view

        return default_exceptionresponse_view(context, request)

    def test_is_exception(self):
        context = Exception()
        result = self._callFUT(context, None)
        self.assertTrue(result is context)

    def test_is_not_exception_context_is_false_still_chose(self):
        request = DummyRequest()
        request.exception = 0
        result = self._callFUT(None, request)
        self.assertTrue(result is None)

    def test_is_not_exception_no_request_exception(self):
        context = object()
        request = DummyRequest()
        request.exception = None
        result = self._callFUT(context, request)
        self.assertTrue(result is context)

    def test_is_not_exception_request_exception(self):
        context = object()
        request = DummyRequest()
        request.exception = 'abc'
        result = self._callFUT(context, request)
        self.assertEqual(result, 'abc')


class Test_view_defaults(unittest.TestCase):
    def test_it(self):
        from pyramid.view import view_defaults

        @view_defaults(route_name='abc', renderer='def')
        class Foo:
            pass

        self.assertEqual(Foo.__view_defaults__['route_name'], 'abc')
        self.assertEqual(Foo.__view_defaults__['renderer'], 'def')

    def test_it_inheritance_not_overridden(self):
        from pyramid.view import view_defaults

        @view_defaults(route_name='abc', renderer='def')
        class Foo:
            pass

        class Bar(Foo):
            pass

        self.assertEqual(Bar.__view_defaults__['route_name'], 'abc')
        self.assertEqual(Bar.__view_defaults__['renderer'], 'def')

    def test_it_inheritance_overriden(self):
        from pyramid.view import view_defaults

        @view_defaults(route_name='abc', renderer='def')
        class Foo:
            pass

        @view_defaults(route_name='ghi')
        class Bar(Foo):
            pass

        self.assertEqual(Bar.__view_defaults__['route_name'], 'ghi')
        self.assertFalse('renderer' in Bar.__view_defaults__)

    def test_it_inheritance_overriden_empty(self):
        from pyramid.view import view_defaults

        @view_defaults(route_name='abc', renderer='def')
        class Foo:
            pass

        @view_defaults()
        class Bar(Foo):
            pass

        self.assertEqual(Bar.__view_defaults__, {})


class TestViewMethodsMixin(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, environ=None):
        from pyramid.decorator import reify
        from pyramid.view import ViewMethodsMixin

        if environ is None:
            environ = {}

        class Request(ViewMethodsMixin):
            def __init__(self, environ):
                self.environ = environ

            @reify
            def response(self):
                return DummyResponse()

        request = Request(environ)
        request.registry = self.config.registry
        return request

    def test_it(self):
        def exc_view(exc, request):
            self.assertTrue(exc is dummy_exc)
            self.assertTrue(request.exception is dummy_exc)
            return DummyResponse(b'foo')

        self.config.add_view(exc_view, context=RuntimeError)
        request = self._makeOne()
        dummy_exc = RuntimeError()
        try:
            raise dummy_exc
        except RuntimeError:
            response = request.invoke_exception_view()
            self.assertEqual(response.app_iter, [b'foo'])
        else:  # pragma: no cover
            self.fail()

    def test_it_hides_attrs(self):
        def exc_view(exc, request):
            self.assertTrue(exc is not orig_exc)
            self.assertTrue(request.exception is not orig_exc)
            self.assertTrue(request.exc_info is not orig_exc_info)
            self.assertTrue(request.response is not orig_response)
            request.response.app_iter = [b'bar']
            return request.response

        self.config.add_view(exc_view, context=RuntimeError)
        request = self._makeOne()
        orig_exc = request.exception = DummyContext()
        orig_exc_info = request.exc_info = DummyContext()
        orig_response = request.response = DummyResponse(b'foo')
        try:
            raise RuntimeError
        except RuntimeError as ex:
            response = request.invoke_exception_view()
            self.assertEqual(response.app_iter, [b'bar'])
            self.assertTrue(request.exception is ex)
            self.assertTrue(request.exc_info[1] is ex)
            self.assertTrue(request.response is orig_response)
        else:  # pragma: no cover
            self.fail()

    def test_it_supports_alternate_requests(self):
        def exc_view(exc, request):
            self.assertTrue(request is other_req)
            from pyramid.threadlocal import get_current_request

            self.assertTrue(get_current_request() is other_req)
            return DummyResponse(b'foo')

        self.config.add_view(exc_view, context=RuntimeError)
        request = self._makeOne()
        other_req = self._makeOne()
        try:
            raise RuntimeError
        except RuntimeError:
            response = request.invoke_exception_view(request=other_req)
            self.assertEqual(response.app_iter, [b'foo'])
        else:  # pragma: no cover
            self.fail()

    def test_it_supports_threadlocal_registry(self):
        def exc_view(exc, request):
            return DummyResponse(b'foo')

        self.config.add_view(exc_view, context=RuntimeError)
        request = self._makeOne()
        del request.registry
        try:
            raise RuntimeError
        except RuntimeError:
            response = request.invoke_exception_view()
            self.assertEqual(response.app_iter, [b'foo'])
        else:  # pragma: no cover
            self.fail()

    def test_it_raises_if_no_registry(self):
        request = self._makeOne()
        del request.registry
        from pyramid.threadlocal import manager

        manager.push({'registry': None, 'request': request})
        try:
            raise RuntimeError
        except RuntimeError:
            try:
                request.invoke_exception_view()
            except RuntimeError as e:
                self.assertEqual(e.args[0], "Unable to retrieve registry")
        else:  # pragma: no cover
            self.fail()
        finally:
            manager.pop()

    def test_it_supports_alternate_exc_info(self):
        def exc_view(exc, request):
            self.assertTrue(request.exc_info is exc_info)
            return DummyResponse(b'foo')

        self.config.add_view(exc_view, context=RuntimeError)
        request = self._makeOne()
        try:
            raise RuntimeError
        except RuntimeError:
            exc_info = sys.exc_info()
        response = request.invoke_exception_view(exc_info=exc_info)
        self.assertEqual(response.app_iter, [b'foo'])

    def test_it_rejects_secured_view(self):
        from pyramid.exceptions import Forbidden

        def exc_view(exc, request):  # pragma: no cover
            pass

        self.config.testing_securitypolicy(permissive=False)
        self.config.add_view(exc_view, context=RuntimeError, permission='view')
        request = self._makeOne()
        try:
            raise RuntimeError
        except RuntimeError:
            self.assertRaises(Forbidden, request.invoke_exception_view)
        else:  # pragma: no cover
            self.fail()

    def test_it_allows_secured_view(self):
        def exc_view(exc, request):
            return DummyResponse(b'foo')

        self.config.testing_securitypolicy(permissive=False)
        self.config.add_view(exc_view, context=RuntimeError, permission='view')
        request = self._makeOne()
        try:
            raise RuntimeError
        except RuntimeError:
            response = request.invoke_exception_view(secure=False)
            self.assertEqual(response.app_iter, [b'foo'])
        else:  # pragma: no cover
            self.fail()

    def test_it_raises_if_not_found(self):
        from pyramid.httpexceptions import HTTPNotFound

        request = self._makeOne()
        dummy_exc = RuntimeError()
        try:
            raise dummy_exc
        except RuntimeError:
            self.assertRaises(HTTPNotFound, request.invoke_exception_view)
        else:  # pragma: no cover
            self.fail()

    def test_it_reraises_if_not_found(self):
        request = self._makeOne()
        dummy_exc = RuntimeError()
        try:
            raise dummy_exc
        except RuntimeError:
            self.assertRaises(
                RuntimeError,
                lambda: request.invoke_exception_view(reraise=True),
            )
        else:  # pragma: no cover
            self.fail()

    def test_it_raises_predicate_mismatch(self):
        from pyramid.exceptions import PredicateMismatch

        def exc_view(exc, request):  # pragma: no cover
            pass

        self.config.add_view(
            exc_view, context=Exception, request_method='POST'
        )
        request = self._makeOne()
        request.method = 'GET'
        dummy_exc = RuntimeError()
        try:
            raise dummy_exc
        except RuntimeError:
            self.assertRaises(PredicateMismatch, request.invoke_exception_view)
        else:  # pragma: no cover
            self.fail()

    def test_it_reraises_after_predicate_mismatch(self):
        def exc_view(exc, request):  # pragma: no cover
            pass

        self.config.add_view(
            exc_view, context=Exception, request_method='POST'
        )
        request = self._makeOne()
        request.method = 'GET'
        dummy_exc = RuntimeError()
        try:
            raise dummy_exc
        except RuntimeError:
            self.assertRaises(
                RuntimeError,
                lambda: request.invoke_exception_view(reraise=True),
            )
        else:  # pragma: no cover
            self.fail()


@unittest.skipUnless(py311plus, 'exception groups require Python 3.11+')
class TestExceptionGroupViewProtocol(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, environ=None):
        from pyramid.decorator import reify
        from pyramid.view import ViewMethodsMixin

        if environ is None:
            environ = {}

        class Request(ViewMethodsMixin):
            def __init__(self, environ):
                self.environ = environ

            @reify
            def response(self):
                return DummyResponse()

        request = Request(environ)
        request.registry = self.config.registry
        return request

    def _exc_info(self, exc):
        try:
            raise exc
        except BaseException:
            return sys.exc_info()

    def test_nested_group_leaves_handled_once_aggregate_decides(self):
        handled = []
        aggregated = []

        def leaf_view(exc, request):
            handled.append(exc)
            return DummyResponse(b'leaf')

        def group_view(exc, request):
            aggregated.append(exc)
            results = request.exception_group_results
            body = repr(
                [(r.path, type(r.leaf).__name__) for r in results]
            ).encode()
            return DummyResponse(body)

        self.config.add_exception_view(leaf_view, context=ValueError)
        self.config.add_exception_view(leaf_view, context=KeyError)
        self.config.add_exception_group_view(group_view)
        request = self._makeOne()
        inner = ExceptionGroup('inner', [ValueError('v1'), KeyError('k1')])
        group = ExceptionGroup('outer', [inner, ValueError('v2')])
        exc_info = self._exc_info(group)
        response = request.invoke_exception_view(exc_info=exc_info)
        # each leaf was handled exactly once
        self.assertEqual(len(handled), 3)
        self.assertEqual(len(set(map(id, handled))), 3)
        # the aggregate view decided the final response, seeing the group
        # path of every leaf
        self.assertEqual(aggregated, [group])
        self.assertEqual(
            response.app_iter,
            [
                b"[((0, 0), 'ValueError'), ((0, 1), 'KeyError'),"
                b" ((1,), 'ValueError')]"
            ],
        )
        self.assertTrue(request.exception is group)
        self.assertTrue(request.exc_info is exc_info)
        self.assertEqual(len(request.exception_group_results), 3)

    def test_leaf_views_honor_predicates(self):
        def post_only_view(exc, request):
            return DummyResponse(b'post')

        def fallback_view(exc, request):
            return DummyResponse(b'fallback: ' + type(exc).__name__.encode())

        def group_view(exc, request):
            bodies = [
                r.response.app_iter[0]
                for r in request.exception_group_results
            ]
            return DummyResponse(b';'.join(bodies))

        self.config.add_exception_view(
            post_only_view, context=ValueError, request_method='POST'
        )
        self.config.add_exception_view(fallback_view, context=Exception)
        self.config.add_exception_group_view(group_view)
        request = self._makeOne()
        request.method = 'GET'
        group = ExceptionGroup('g', [ValueError('v'), KeyError('k')])
        response = request.invoke_exception_view(
            exc_info=self._exc_info(group)
        )
        self.assertEqual(
            response.app_iter,
            [b'fallback: ValueError;fallback: KeyError'],
        )

        request = self._makeOne()
        request.method = 'POST'
        group = ExceptionGroup('g', [ValueError('v'), KeyError('k')])
        response = request.invoke_exception_view(
            exc_info=self._exc_info(group)
        )
        self.assertEqual(response.app_iter, [b'post;fallback: KeyError'])

    def test_raising_leaf_view_propagates_without_retry(self):
        calls = []

        def ok_view(exc, request):
            calls.append(('ok', exc))
            return DummyResponse(b'ok')

        def boom_view(exc, request):
            calls.append(('boom', exc))
            raise RuntimeError('boom')

        def group_view(exc, request):  # pragma: no cover
            raise AssertionError('must not be called')

        self.config.add_exception_view(ok_view, context=KeyError)
        self.config.add_exception_view(boom_view, context=ValueError)
        self.config.add_exception_group_view(group_view)
        request = self._makeOne()
        group = ExceptionGroup('g', [KeyError('k'), ValueError('v')])
        with self.assertRaises(RuntimeError) as cm:
            request.invoke_exception_view(exc_info=self._exc_info(group))
        self.assertEqual(str(cm.exception), 'boom')
        # each leaf was processed at most once; nothing was retried
        self.assertEqual([name for name, exc in calls], ['ok', 'boom'])

    def test_reraise_reraises_original_group_on_view_error(self):
        def boom_view(exc, request):
            raise RuntimeError('boom')

        def group_view(exc, request):  # pragma: no cover
            raise AssertionError('must not be called')

        self.config.add_exception_view(boom_view, context=ValueError)
        self.config.add_exception_group_view(group_view)
        request = self._makeOne()
        group = ExceptionGroup('g', [ValueError('v')])
        exc_info = self._exc_info(group)
        with self.assertRaises(ExceptionGroup) as cm:
            request.invoke_exception_view(exc_info=exc_info, reraise=True)
        self.assertTrue(cm.exception is group)

    def test_unmatched_leaves_reraised_with_structure_and_chain(self):
        handled = []

        def leaf_view(exc, request):
            handled.append(exc)
            return DummyResponse(b'leaf')

        def group_view(exc, request):  # pragma: no cover
            raise AssertionError('must not be called')

        self.config.add_exception_view(leaf_view, context=ValueError)
        self.config.add_exception_group_view(group_view)
        request = self._makeOne()
        cause = ValueError('cause')
        inner = ExceptionGroup('inner', [ValueError('v'), KeyError('k')])
        group = ExceptionGroup('outer', [inner, RuntimeError('r')])
        group.__cause__ = cause
        with self.assertRaises(ExceptionGroup) as cm:
            request.invoke_exception_view(exc_info=self._exc_info(group))
        remainder = cm.exception
        # only the unmatched leaves remain, nested structure preserved
        self.assertEqual(len(remainder.exceptions), 2)
        sub = remainder.exceptions[0]
        self.assertIsInstance(sub, ExceptionGroup)
        self.assertEqual(list(sub.exceptions), [inner.exceptions[1]])
        self.assertIsInstance(remainder.exceptions[1], RuntimeError)
        # the original exception chain stays traceable
        self.assertTrue(remainder.__cause__ is cause)
        self.assertTrue(remainder.__traceback__ is not None)
        # the matched leaf was handled exactly once
        self.assertEqual(handled, [inner.exceptions[0]])

    def test_base_exception_group_is_never_split(self):
        def leaf_view(exc, request):  # pragma: no cover
            raise AssertionError('must not be called')

        def group_view(exc, request):  # pragma: no cover
            raise AssertionError('must not be called')

        self.config.add_exception_view(leaf_view, context=ValueError)
        self.config.add_exception_group_view(group_view)
        request = self._makeOne()
        cancelled = KeyboardInterrupt()
        group = BaseExceptionGroup('g', [ValueError('v'), cancelled])
        exc_info = self._exc_info(group)
        # the cancellation is not converted into a response; the original
        # group is reraised
        with self.assertRaises(BaseExceptionGroup) as cm:
            request.invoke_exception_view(exc_info=exc_info, reraise=True)
        self.assertTrue(cm.exception is group)

    def test_base_exception_group_not_found_without_reraise(self):
        from pyramid.httpexceptions import HTTPNotFound

        def group_view(exc, request):  # pragma: no cover
            raise AssertionError('must not be called')

        self.config.add_exception_group_view(group_view)
        request = self._makeOne()
        group = BaseExceptionGroup('g', [KeyboardInterrupt()])
        exc_info = self._exc_info(group)
        self.assertRaises(
            HTTPNotFound,
            request.invoke_exception_view,
            exc_info=exc_info,
        )

    def test_no_aggregate_view_falls_back_to_normal_handling(self):
        def group_level_view(exc, request):
            return DummyResponse(b'whole group')

        self.config.add_exception_view(
            group_level_view, context=ExceptionGroup
        )
        request = self._makeOne()
        group = ExceptionGroup('g', [ValueError('v')])
        response = request.invoke_exception_view(
            exc_info=self._exc_info(group)
        )
        self.assertEqual(response.app_iter, [b'whole group'])

    def test_no_leaf_matched_falls_back_to_normal_handling(self):
        def group_level_view(exc, request):
            return DummyResponse(b'whole group')

        def group_view(exc, request):  # pragma: no cover
            raise AssertionError('must not be called')

        self.config.add_exception_view(
            group_level_view, context=ExceptionGroup
        )
        self.config.add_exception_group_view(group_view)
        request = self._makeOne()
        group = ExceptionGroup('g', [ValueError('v'), RuntimeError('r')])
        response = request.invoke_exception_view(
            exc_info=self._exc_info(group)
        )
        self.assertEqual(response.app_iter, [b'whole group'])

    def test_aggregate_view_decides_final_response(self):
        def leaf_view(exc, request):
            response = DummyResponse(b'leaf')
            response.status = '200 OK'
            return response

        def group_view(exc, request):
            response = DummyResponse(b'aggregate')
            response.status = '500 Internal Server Error'
            return response

        self.config.add_exception_view(leaf_view, context=Exception)
        self.config.add_exception_group_view(group_view)
        request = self._makeOne()
        group = ExceptionGroup('g', [ValueError('v'), KeyError('k')])
        response = request.invoke_exception_view(
            exc_info=self._exc_info(group)
        )
        # the final response comes from the aggregate view, not from
        # whichever leaf happened to be first
        self.assertEqual(response.app_iter, [b'aggregate'])
        self.assertEqual(response.status, '500 Internal Server Error')

    def test_secure_false_is_passed_to_leaf_views(self):
        from pyramid.exceptions import Forbidden

        def leaf_view(exc, request):
            return DummyResponse(b'leaf')

        def group_view(exc, request):
            return DummyResponse(b'aggregate')

        self.config.testing_securitypolicy(permissive=False)
        self.config.add_view(leaf_view, context=ValueError, permission='view')
        self.config.add_exception_group_view(group_view)
        request = self._makeOne()
        group = ExceptionGroup('g', [ValueError('v')])
        exc_info = self._exc_info(group)
        self.assertRaises(
            Forbidden, request.invoke_exception_view, exc_info=exc_info
        )
        response = request.invoke_exception_view(
            exc_info=exc_info, secure=False
        )
        self.assertEqual(response.app_iter, [b'aggregate'])


class TestExceptionGroupLeafResult(unittest.TestCase):
    def test_repr(self):
        from pyramid.view import ExceptionGroupLeafResult

        result = ExceptionGroupLeafResult(
            leaf=ValueError('v'), path=(0, 1), response='response'
        )
        r = repr(result)
        self.assertIn('ExceptionGroupLeafResult', r)
        self.assertIn('(0, 1)', r)
        self.assertIn('ValueError', r)


class ExceptionResponse(Exception):
    status = '404 Not Found'
    app_iter = ['Not Found']
    headerlist = []


class DummyContext:
    pass


def make_view(response):
    def view(context, request):
        return response

    return view


class DummyRequest:
    exception = None
    request_iface = IRequest

    def __init__(self, environ=None):
        if environ is None:
            environ = {}
        self.environ = environ


@implementer(IResponse)
class DummyResponse:
    headerlist = ()
    app_iter = ()
    status = '200 OK'
    environ = None

    def __init__(self, body=None):
        if body is None:
            self.app_iter = ()
        else:
            self.app_iter = [body]


class IContext(Interface):
    pass


class DummyVenusianInfo:
    scope = 'notaclass'
    module = sys.modules['tests']
    codeinfo = 'codeinfo'


class DummyVenusian:
    def __init__(self, info=None):
        if info is None:
            info = DummyVenusianInfo()
        self.info = info
        self.attachments = []

    def attach(self, wrapped, callback, category=None, depth=1):
        self.attachments.append((wrapped, callback, category, depth))
        return self.info


class DummyRegistry:
    pass


class DummyConfig:
    def __init__(self):
        self.settings = []
        self.registry = DummyRegistry()

    def add_view(self, **kw):
        self.settings.append(kw)

    add_notfound_view = add_forbidden_view = add_exception_view = add_view
    add_exception_group_view = add_view

    def with_package(self, pkg):
        self.pkg = pkg
        return self


class DummyVenusianContext:
    def __init__(self):
        self.config = DummyConfig()


def call_venusian(venusian, context=None):
    if context is None:
        context = DummyVenusianContext()
    for wrapped, callback, category, depth in venusian.attachments:
        callback(context, None, None)
    return context.config
