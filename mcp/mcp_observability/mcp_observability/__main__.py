"""Entry point for running the observability MCP server as a module."""
from mcp_observability import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
