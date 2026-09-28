unreleased
==========

Features
--------

- Add declarative request arguments for view derivers. A deriver may declare
  a ``request_arguments`` attribute naming values computed from the current
  request, backed by providers registered via the new
  ``Configurator.add_request_argument_provider`` method. Providers are
  validated at configuration time, resolved at most once per request, shared
  between deriver layers, and failures are handled by exception views.

- Add `Configurator.resolve_asset` and `Request.resolve_asset` methods.  See
  https://github.com/Pylons/pyramid/pull/3815.

Bug Fixes
---------

Backward Incompatibilities
--------------------------

Deprecations
------------

Documentation Changes
---------------------
