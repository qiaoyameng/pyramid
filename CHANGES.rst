unreleased
==========

Features
--------

- Add `Configurator.resolve_asset` and `Request.resolve_asset` methods.  See
  https://github.com/Pylons/pyramid/pull/3815.

- Add an optional digest rendering mode to
  ``pyramid.renderers.render_to_response`` and
  ``RendererHelper.render_to_response`` via a new ``digest`` flag.  The
  renderer is executed exactly once while a SHA-256 digest is computed over
  the actual encoded response bytes; small bodies are kept in memory and
  large bodies are spooled to a temporary file.  The digest is used as the
  response ``ETag`` (an explicitly set ``ETag`` takes precedence) and
  conditional ``GET`` requests with a matching ``If-None-Match`` header are
  answered with ``304 Not Modified``.

Bug Fixes
---------

Backward Incompatibilities
--------------------------

Deprecations
------------

Documentation Changes
---------------------

