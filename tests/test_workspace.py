import pytest
import os
import shutil
from pathlib import Path
from aegisos.core.workspace import WorkspaceManager

@pytest.fixture
def temp_workspace():
    # 使用一个独立的测试工作区目录
    base_dir = "tests/_test_workspace"
    manager = WorkspaceManager(base_dir=base_dir)
    yield manager
    # 测试完成后清理
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)

@pytest.mark.asyncio
async def test_workspace_write_read(temp_workspace):
    filename = "test.txt"
    content = "hello aegisos"
    
    # 测试写入
    rel_path = await temp_workspace.write_file(filename, content)
    assert rel_path == filename
    
    # 测试读取
    read_content = await temp_workspace.read_file(rel_path)
    assert read_content == content

@pytest.mark.asyncio
async def test_path_traversal_prevention(temp_workspace):
    # 尝试访问父目录
    with pytest.raises(PermissionError):
        await temp_workspace.read_file("../outside.txt")
    
    with pytest.raises(PermissionError):
        await temp_workspace.write_file("../../hack.txt", "evil")

@pytest.mark.asyncio
async def test_session_id_persistence():
    # 测试手动传入 session_id
    session_id = "test-session-123"
    manager = WorkspaceManager(base_dir="tests/_test_workspace", session_id=session_id)
    assert manager.session_id == session_id
    assert str(manager.root_path).endswith(session_id)
    
    # 清理
    shutil.rmtree("tests/_test_workspace")

@pytest.mark.asyncio
async def test_list_files(temp_workspace):
    await temp_workspace.write_file("file1.txt", "c1")
    await temp_workspace.write_file("subdir/file2.txt", "c2")
    
    files = await temp_workspace.list_files()
    assert len(files) == 2
    assert "file1.txt" in files
    assert "subdir/file2.txt" in files
