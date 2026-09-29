unreleased
==========

Features
--------

- Add ``Configurator.tentative_include``, a context manager which includes
  a configuration callable and allows the pending configuration actions
  (and introspectables) it produced to be rolled back atomically before
  they are committed.  This supports probing candidate plugins: a
  rolled-back plugin frees its discriminators (e.g. route names) so that
  another plugin may use them, while a kept block behaves exactly like a
  normal ``include``.  Rolling back a block whose actions have already
  been committed raises ``ConfigurationError``.

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
