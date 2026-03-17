import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from aegisos.core.dispatcher import AegisDispatcher
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.config import CONFIG, NetworkMode

@pytest.mark.asyncio
async def test_route_to_remote():
    """Test that messages are routed to a remote gateway"""
    dispatcher = AegisDispatcher()
    
    # Use Mock to replace send_to_remote to observe if it's called
    dispatcher.send_to_remote = AsyncMock()
    
    # Properly formatted URI
    local_sender = "boss@local-node"
    remote_uri = "worker_001@remote-node"
    
    message = AACPMessage(
        sender=local_sender,
        receiver=remote_uri,
        intent=AACPIntent.INFORM,
        payload={"data": "hello remote"}
    )
    
    await dispatcher.start()
    await dispatcher.send_message(message)
    
    # Give the event loop some time to process the message
    await asyncio.sleep(0.1)
    
    # Verify if send_to_remote was called with the correct arguments
    dispatcher.send_to_remote.assert_called_once_with(remote_uri, message)
    
    await dispatcher.stop()

@pytest.mark.asyncio
async def test_send_to_remote_logs_warning_on_local_mode():
    """Test that sending to remote triggers a warning in LOCAL mode"""
    dispatcher = AegisDispatcher()
    
    # Ensure it's in LOCAL mode
    with patch("aegisos.core.dispatcher.CONFIG.network_mode", NetworkMode.LOCAL):
        with patch("aegisos.core.dispatcher.logger") as mock_logger:
            local_sender = "boss@local-node"
            remote_uri = "worker_001@remote-node"
            message = AACPMessage(
                sender=local_sender,
                receiver=remote_uri,
                intent=AACPIntent.INFORM,
                payload={"data": "hello"}
            )
            
            await dispatcher.send_to_remote(remote_uri, message)
            
            # Verify if a warning log was recorded
            mock_logger.warning.assert_any_call(
                f"Network mode is LOCAL. Cannot send to remote instance: remote-node"
            )
