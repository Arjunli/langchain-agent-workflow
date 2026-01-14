"""快速测试API接口"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """测试健康检查"""
    print("=" * 50)
    print("测试健康检查接口...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        print("✓ 健康检查通过\n")
        return True
    except Exception as e:
        print(f"✗ 健康检查失败: {e}\n")
        return False


def test_root():
    """测试根路径"""
    print("=" * 50)
    print("测试根路径...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print("✓ 根路径测试通过\n")
        return True
    except Exception as e:
        print(f"✗ 根路径测试失败: {e}\n")
        return False


def test_chat():
    """测试聊天接口"""
    print("=" * 50)
    print("测试聊天接口...")
    try:
        data = {
            "message": "你好，请简单介绍一下你自己"
        }
        print(f"发送消息: {data['message']}")
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=data,
            timeout=30
        )
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应码: {result.get('code')}")
        print(f"消息: {result.get('message')}")
        
        if result.get('data'):
            chat_data = result['data']
            print(f"\nAI响应: {chat_data.get('response', '')[:200]}...")
            print(f"会话ID: {chat_data.get('conversation_id')}")
            if chat_data.get('workflow_id'):
                print(f"工作流ID: {chat_data.get('workflow_id')}")
        
        print(f"\n追踪ID: {result.get('trace_id')}")
        print("✓ 聊天接口测试通过\n")
        return True
    except Exception as e:
        print(f"✗ 聊天接口测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_chat_with_context():
    """测试带上下文的聊天"""
    print("=" * 50)
    print("测试带上下文的聊天接口...")
    try:
        data = {
            "message": "记住我的名字是张三",
            "conversation_id": "test_conv_001",
            "context": {
                "user_id": "test_user",
                "session_id": "test_session"
            }
        }
        print(f"发送消息: {data['message']}")
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=data,
            timeout=30
        )
        result = response.json()
        print(f"响应码: {result.get('code')}")
        if result.get('data'):
            print(f"AI响应: {result['data'].get('response', '')[:200]}...")
        print("✓ 带上下文的聊天测试通过\n")
        return True
    except Exception as e:
        print(f"✗ 带上下文的聊天测试失败: {e}\n")
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("API 接口测试")
    print("=" * 50 + "\n")
    
    results = []
    
    # 基础测试
    results.append(("健康检查", test_health()))
    results.append(("根路径", test_root()))
    
    # 功能测试
    results.append(("聊天接口", test_chat()))
    results.append(("带上下文聊天", test_chat_with_context()))
    
    # 汇总结果
    print("=" * 50)
    print("测试结果汇总:")
    print("=" * 50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查服务状态和配置")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
