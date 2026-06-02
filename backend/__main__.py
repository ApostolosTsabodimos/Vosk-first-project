"""Allow running the backend as `python -m backend`."""

import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

from backend.server import main

asyncio.run(main())
