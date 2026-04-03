#!/usr/bin/env python3
"""
Entrypoint for nanobot Docker deployment.

Reads config.json, injects environment variable values for:
- LLM provider (API key, base URL, model)
- Gateway (host, port)
- Webchat (host, port)
- MCP server (backend URL, backend API key)

Writes resolved config to a temp file, then execs `nanobot gateway`.
"""

import json
import os
import sys
import tempfile


def register_webchat_channel():
    """Manually register the webchat channel since entry_points may not work in Docker."""
    try:
        import nanobot.channels.registry as registry
        from nanobot_webchat import WebChatChannel
        
        # Monkey-patch discover_plugins to include webchat
        original_discover_plugins = registry.discover_plugins
        def patched_discover_plugins():
            plugins = original_discover_plugins()
            plugins["webchat"] = WebChatChannel
            return plugins
        
        registry.discover_plugins = patched_discover_plugins
        print("WebChat channel registered via monkey-patch", flush=True)
        
        # Also patch discover_all to force include webchat
        original_discover_all = registry.discover_all
        def patched_discover_all():
            result = original_discover_all()
            if "webchat" not in result:
                from nanobot.channels.base import BaseChannel
                if issubclass(WebChatChannel, BaseChannel):
                    result["webchat"] = WebChatChannel
                    print("WebChat channel added to discover_all result", flush=True)
            return result
        
        registry.discover_all = patched_discover_all
    except Exception as e:
        print(f"Warning: Could not register webchat channel: {e}", flush=True)


def resolve_config(config_path: str) -> str:
    """Load config.json, inject env vars, write resolved config to temp file."""
    with open(config_path) as f:
        config = json.load(f)

    # LLM provider
    llm_key = os.environ.get("LLM_API_KEY", "")
    llm_base = os.environ.get("LLM_API_BASE_URL", "")
    llm_model = os.environ.get("LLM_API_MODEL", "")

    if "providers" in config and "custom" in config["providers"]:
        if llm_key:
            config["providers"]["custom"]["api_key"] = llm_key
        if llm_base:
            config["providers"]["custom"]["api_base"] = llm_base

    if "agents" in config and "defaults" in config["agents"]:
        if llm_model:
            config["agents"]["defaults"]["model"] = f"custom/{llm_model}"

    # Gateway
    gateway_host = os.environ.get("NANOBOT_GATEWAY_CONTAINER_ADDRESS", "")
    gateway_port = os.environ.get("NANOBOT_GATEWAY_CONTAINER_PORT", "")
    if "gateway" in config:
        if gateway_host:
            config["gateway"]["host"] = gateway_host
        if gateway_port:
            config["gateway"]["port"] = int(gateway_port)

    # Webchat channel
    webchat_host = os.environ.get("NANOBOT_WEBCHAT_CONTAINER_ADDRESS", "")
    webchat_port = os.environ.get("NANOBOT_WEBCHAT_CONTAINER_PORT", "")
    if "channels" not in config:
        config["channels"] = {}
    config["channels"]["webchat"] = {
        "enabled": True,
        "allow_from": ["*"],
        "host": webchat_host or "0.0.0.0",
        "port": int(webchat_port or 8765),
    }

    # MCP server env vars
    backend_url = os.environ.get("NANOBOT_LMS_BACKEND_URL", "")
    backend_key = os.environ.get("NANOBOT_LMS_API_KEY", "")
    if "tools" in config and "mcp_servers" in config["tools"]:
        if "lms" in config["tools"]["mcp_servers"]:
            lms_server = config["tools"]["mcp_servers"]["lms"]
            # Update the command to use the container-internal backend URL
            if backend_url:
                # Use venv Python and the backend URL
                lms_server["command"] = "/app/nanobot/.venv/bin/python"
                lms_server["args"] = ["-m", "mcp_lms", backend_url]
            if backend_key:
                lms_server["env"] = {
                    "NANOBOT_LMS_API_KEY": backend_key
                }

    # Write resolved config
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, dir="/tmp"
    )
    json.dump(config, tmp, indent=2)
    tmp.close()
    return tmp.name


def main():
    config_path = os.environ.get("NANOBOT_CONFIG_PATH", "/app/nanobot/config.json")
    workspace = os.environ.get("NANOBOT_WORKSPACE", "/app/nanobot/workspace")

    resolved = resolve_config(config_path)
    print(f"Resolved config: {resolved}", flush=True)

    # Run gateway via wrapper that patches channel registry
    # Use the venv Python to ensure nanobot module is found
    venv_python = "/app/nanobot/.venv/bin/python"
    print(f"Using Python: {venv_python}", flush=True)
    print(f"Python exists: {os.path.exists(venv_python)}", flush=True)
    
    os.execvp(venv_python, [venv_python, "/app/nanobot/gateway_wrapper.py", "gateway", "--config", resolved, "--workspace", workspace])


if __name__ == "__main__":
    main()
