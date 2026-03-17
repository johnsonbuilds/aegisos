import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class NetworkMode(str, Enum):
    LOCAL = "local"
    TAILSCALE = "tailscale"
    NOSTR = "nostr"
    LIBP2P = "libp2p"

class AegisConfig(BaseModel):
    """
    AegisOS global configuration management
    """
    # Current instance ID (used for multi-node communication identification)
    instance_id: str = Field(
        default_factory=lambda: os.getenv("AEGIS_INSTANCE_ID", "local-node"),
        description="Unique identifier for this instance"
    )
    
    # Network mode, defaults to local
    network_mode: NetworkMode = Field(
        default_factory=lambda: NetworkMode(os.getenv("AEGIS_NETWORK_MODE", "local")),
        description="Underlying network engine"
    )

    # Log level
    log_level: str = Field(
        default_factory=lambda: os.getenv("AEGIS_LOG_LEVEL", "INFO"),
        description="Global log level"
    )

    # LLM configuration
    openai_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    openai_model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))
    openai_base_url: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_BASE_URL"))

    anthropic_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    anthropic_model: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"))

# Global singleton configuration object
CONFIG = AegisConfig()
