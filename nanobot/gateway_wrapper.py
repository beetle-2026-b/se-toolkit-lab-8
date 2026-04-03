"""Wrapper that patches nanobot channel registry before starting gateway."""

import sys
import os

# Add nanobot directory to path so we can import local modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def apply_patches():
    """Patch nanobot channel registry to include webchat."""
    try:
        import nanobot.channels.registry as registry
        from nanobot_webchat import WebChatChannel
        
        # Patch discover_plugins
        original_discover_plugins = registry.discover_plugins
        def patched_discover_plugins():
            plugins = original_discover_plugins()
            plugins["webchat"] = WebChatChannel
            return plugins
        registry.discover_plugins = patched_discover_plugins
        
        # Patch discover_all
        original_discover_all = registry.discover_all
        def patched_discover_all():
            result = original_discover_all()
            if "webchat" not in result:
                from nanobot.channels.base import BaseChannel
                if issubclass(WebChatChannel, BaseChannel):
                    result["webchat"] = WebChatChannel
            return result
        registry.discover_all = patched_discover_all
        
        print("WebChat channel registered", flush=True)
    except Exception as e:
        print(f"Warning: Could not register webchat channel: {e}", flush=True)

# Apply patches before importing anything else
apply_patches()

# Now run nanobot gateway
import sys
import os

# Add the venv site-packages to the path
venv_site = "/app/.venv/lib/python3.14/site-packages"
if venv_site not in sys.path:
    sys.path.insert(0, venv_site)

from nanobot.cli.commands import gateway as gateway_cmd

# Parse args and run gateway
config_idx = None
workspace_idx = None
for i, arg in enumerate(sys.argv):
    if arg == "--config" and i + 1 < len(sys.argv):
        config_idx = i + 1
    if arg == "--workspace" and i + 1 < len(sys.argv):
        workspace_idx = i + 1

config_path = sys.argv[config_idx] if config_idx else "/app/nanobot/config.json"
workspace_path = sys.argv[workspace_idx] if workspace_idx else "/app/nanobot/workspace"

import asyncio
asyncio.run(gateway_cmd(config=config_path, workspace=workspace_path))
