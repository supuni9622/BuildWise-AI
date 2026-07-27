"""Root pytest configuration.

Loading this conftest causes pytest to add the ``tests/`` directory to
``sys.path`` (since it has no ``__init__.py``), which makes the shared
``fixtures`` helper package importable from any test module, e.g.::

    from fixtures.planning import build_planning_inputs
"""
