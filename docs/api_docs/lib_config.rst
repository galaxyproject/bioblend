====================================
Configuration documents for BioBlend
====================================

BioBlend
--------

.. automodule:: bioblend
    :members:

Config
------

.. automodule:: bioblend.config
    :members:
    :undoc-members:

Connection settings
-------------------

The following properties are available on both ``GalaxyInstance`` and
``ToolShedInstance`` objects, and control how requests are retried and how
connections are reused.

.. autoclass:: bioblend.galaxyclient.GalaxyClient
    :members: max_total_retry_delay, max_retry_after, max_429_retries,
              use_session, close, max_get_attempts, get_retry_delay
