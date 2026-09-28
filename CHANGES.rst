unreleased
==========

Features
--------

- Add `Configurator.resolve_asset` and `Request.resolve_asset` methods.  See
  https://github.com/Pylons/pyramid/pull/3815.

- Add declarative request param providers for view derivers. A provider is
  registered with `Configurator.add_request_param_provider` and a view
  deriver declares the params it needs via a `request_params` attribute.
  Declared params are resolved at most once per request - the value is
  cached on the request and shared between deriver layers - and injected
  into the deriver layer as keyword arguments. Provider names and their
  dependencies are validated at configuration time, resolution failures
  are handled by exception views like any other view exception, and
  params are never resolved for views whose predicates do not match.

Bug Fixes
---------

Backward Incompatibilities
--------------------------

Deprecations
------------

Documentation Changes
---------------------
