import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from aegisos.core.dispatcher import AegisDispatcher
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.config import CONFIG, NetworkMode

@pytest.mark.asyncio
async def test_route_to_remote():
    """测试消息被路由到远程网关"""
    dispatcher = AegisDispatcher()
    
    # 使用 Mock 替换 send_to_remote 以观察其是否被调用
    dispatcher.send_to_remote = AsyncMock()
    
    # 符合规范的 URI
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
    
    # 给一点时间让事件循环处理消息
    await asyncio.sleep(0.1)
    
    # 验证 send_to_remote 是否被调用，且参数正确
    dispatcher.send_to_remote.assert_called_once_with(remote_uri, message)
    
    await dispatcher.stop()

@pytest.mark.asyncio
async def test_send_to_remote_logs_warning_on_local_mode():
    """测试在 LOCAL 模式下，发送到远程会触发警告"""
    dispatcher = AegisDispatcher()
    
    # 确保是 LOCAL 模式
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
            
            # 验证是否记录了警告日志
            mock_logger.warning.assert_any_call(
                f"Network mode is LOCAL. Cannot send to remote instance: remote-node"
            )
