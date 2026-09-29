unreleased
==========

Features
--------

- Add an optional exception group view protocol.  When an exception group
  view is registered via
  ``Configurator.add_exception_group_view``, an ``ExceptionGroup`` raised
  during request processing is no longer treated as a single opaque
  exception: each leaf exception is matched against the registered
  exception views individually (honoring their predicates), and the
  exception group view decides the final response from the per-leaf
  results.  Unmatched leaves (including ``BaseException`` leaves such as
  cancellations) are reraised for upstream handlers instead of being
  swallowed into an HTTP error response.  See ``pyramid.excgroup``.

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
