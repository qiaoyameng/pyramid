unreleased
==========

Features
--------

- Add an opt-in exception group view protocol.  When an
  ``ExceptionGroup`` is raised (for example by parallel ``asyncio``
  tasks) and an exception group view is registered with
  ``Configurator.add_exception_group_view`` (or
  ``pyramid.view.exception_group_view_config``), each leaf exception of
  the (possibly nested) group is handled by its own exception view and
  the aggregate exception group view decides the final response based on
  ``request.exception_group_results``.  Leaves without a matching
  exception view are re-raised as a remainder group with the original
  exception chain intact, and ``BaseExceptionGroup`` instances
  containing cancellations are never converted into a response.

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
