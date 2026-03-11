import json
from uuid import UUID
from datetime import datetime
from aegisos.core.protocol import AACPMessage, AACPIntent

def test_aacp_message_parsing():
    json_data = {
        "sender": "AgentA",
        "receiver": "AgentB",
        "intent": "REQUEST",
        "payload": {"task": "test_task"},
        "context_pointer": "path/to/context"
    }
    
    # 验证从字典解析
    message = AACPMessage(**json_data)
    assert message.sender == "AgentA"
    assert message.receiver == "AgentB"
    assert message.intent == AACPIntent.REQUEST
    assert message.payload == {"task": "test_task"}
    assert message.context_pointer == "path/to/context"
    assert isinstance(message.message_id, UUID)
    assert isinstance(message.timestamp, datetime)

    # 验证 JSON 字符串解析
    json_str = json.dumps(json_data)
    message_from_json = AACPMessage.model_validate_json(json_str)
    assert message_from_json.sender == "AgentA"
    assert message_from_json.intent == "REQUEST"

def test_aacp_message_serialization():
    message = AACPMessage(
        sender="AgentX",
        receiver="AgentY",
        intent=AACPIntent.TASK_COMPLETE,
        payload={"result": "success"}
    )
    
    json_str = message.model_dump_json()
    parsed_back = json.loads(json_str)
    
    assert parsed_back["sender"] == "AgentX"
    assert parsed_back["intent"] == "TASK_COMPLETE"
    assert "message_id" in parsed_back
    assert "timestamp" in parsed_back
