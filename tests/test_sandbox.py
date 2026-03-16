import pytest
import os
import shutil
import asyncio
from aegisos.core.sandbox import SandboxRunner

@pytest.fixture
def sandbox_env():
    # 创建临时测试目录
    test_dir = "_test_sandbox"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    yield test_dir
    # 清理
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

@pytest.mark.asyncio
async def test_sandbox_normal(sandbox_env):
    """测试正常执行"""
    runner = SandboxRunner(sandbox_env)
    code = "print('Hello Sandbox')"
    result = await runner.run_python(code)
    
    assert result.exit_code == 0
    assert result.stdout == "Hello Sandbox"
    assert result.stderr == ""
    assert result.timed_out is False

@pytest.mark.asyncio
async def test_sandbox_error(sandbox_env):
    """测试代码报错捕获"""
    runner = SandboxRunner(sandbox_env)
    code = "raise ValueError('Oops')"
    result = await runner.run_python(code)
    
    assert result.exit_code != 0
    assert "ValueError: Oops" in result.stderr
    assert result.stdout == ""

@pytest.mark.asyncio
async def test_sandbox_timeout(sandbox_env):
    """测试超时终止"""
    runner = SandboxRunner(sandbox_env)
    # 模拟死循环
    code = "import time\nwhile True: time.sleep(0.1)"
    result = await runner.run_python(code, timeout=1)
    
    assert result.timed_out is True
    assert result.exit_code == -1
    assert "Timed Out" in result.stderr
