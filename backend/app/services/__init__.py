"""External-service adapters.

Each adapter is split into an interface (the abstract or Protocol you depend
on) and one or more implementations (a stub for local dev/tests, a live
implementation that hits the real third-party API). Switching between them
happens via the `app.services.registry` module, which inspects settings.
"""
