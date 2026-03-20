import os
import json
import logging
from enum import Enum
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field

logger = logging.getLogger("AegisConfig")

class NetworkMode(str, Enum):
    LOCAL = "local"
    TAILSCALE = "tailscale"
    NOSTR = "nostr"
    LIBP2P = "libp2p"

class AegisConfig(BaseModel):
    """
    AegisOS global configuration management.
    Priority: Environment Variables > aegisos.json > Defaults.
    """
    # --- System ---
    instance_id: str = Field(default="local-node")
    network_mode: NetworkMode = Field(default=NetworkMode.LOCAL)
    log_level: str = Field(default="INFO")

    # --- Runtime Guardrails (Phase 2) ---
    agent_max_steps: int = Field(default=10, description="Max reasoning steps per message/reflexion loop")
    task_timeout: int = Field(default=300, description="Default task execution timeout in seconds")

    # --- LLM configuration ---
    openai_api_key: Optional[str] = None
    openai_model: str = Field(default="gpt-4o")
    openai_base_url: Optional[str] = None

    anthropic_api_key: Optional[str] = None
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022")

    @classmethod
    def load(cls) -> "AegisConfig":
        """Load configuration from file and environment."""
        config_dict = {}

        # 1. Load from JSON if exists
        config_path = os.getenv("AEGIS_CONFIG_PATH", "aegisos.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config_dict = json.load(f)
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load config from {config_path}: {e}")

        # 2. Environment Variables override
        env_mapping = {
            "AEGIS_INSTANCE_ID": "instance_id",
            "AEGIS_NETWORK_MODE": "network_mode",
            "AEGIS_LOG_LEVEL": "log_level",
            "AEGIS_MAX_STEPS": "agent_max_steps",
            "AEGIS_TASK_TIMEOUT": "task_timeout",
            "OPENAI_API_KEY": "openai_api_key",
            "OPENAI_MODEL": "openai_model",
            "OPENAI_BASE_URL": "openai_base_url",
            "ANTHROPIC_API_KEY": "anthropic_api_key",
            "ANTHROPIC_MODEL": "anthropic_model",
        }

        for env_key, config_key in env_mapping.items():
            val = os.getenv(env_key)
            if val is not None:
                # Basic type conversion for numbers
                if config_key in ["agent_max_steps", "task_timeout"]:
                    config_dict[config_key] = int(val)
                else:
                    config_dict[config_key] = val

        return cls(**config_dict)

# Global singleton configuration object, initialized on first import
CONFIG = AegisConfig.load()
