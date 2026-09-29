unreleased
==========

Features
--------

- Add ``Configurator.tentative_include``, which includes a configuration
  callable but keeps the resulting configuration block revocable until the
  next ``commit``.  The returned ``pyramid.config.TentativeInclude`` block
  may be kept (the default) or discarded, which removes the block's pending
  actions and introspectables, allowing a rival plugin to be included in
  its place.  Discarding a block whose actions have already been committed
  raises ``ConfigurationError``.

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
