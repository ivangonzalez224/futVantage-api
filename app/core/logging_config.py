"""Application-wide logging setup.

Without this, Python's root logger defaults to WARNING, and uvicorn
only configures its own loggers (`uvicorn.error`, `uvicorn.access`) —
not ours. That silently swallowed `logger.info(...)` calls like the one
in `app.core.email`'s dev password-reset stand-in, which is how this
gap got noticed in the first place.
"""

import logging


def configure_logging() -> None:
    """Configures the root logger once, at application startup."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
