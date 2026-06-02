"""Allow running the backend as `python -m backend`."""

from backend.server import main
import asyncio

asyncio.run(main())
