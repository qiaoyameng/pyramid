unreleased
==========

Features
--------

- Add `Configurator.resolve_asset` and `Request.resolve_asset` methods.  See
  https://github.com/Pylons/pyramid/pull/3815.

- Add an optional digest rendering mode via the ``digest_etag`` argument to
  ``pyramid.renderers.render_to_response`` and
  ``RendererHelper.render_to_response``.  The rendered output is buffered
  exactly once (small outputs in memory, large outputs in a temporary file)
  while a SHA-256 digest of the encoded response bytes is computed and used
  as the response ``ETag`` (unless an explicit ``ETag`` was already set,
  which takes precedence).  Conditional GET/HEAD requests with a matching
  ``If-None-Match`` header receive a ``304 Not Modified`` response.

Bug Fixes
---------

Backward Incompatibilities
--------------------------

Deprecations
------------

Documentation Changes
---------------------
