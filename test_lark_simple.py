#!/usr/bin/env python3
"""
简单的Lark webhook测试脚本
"""

import requests
import json
import sys

def test_lark_webhook():
    """测试Lark webhook连通性"""
    
    # 请用户提供webhook URL
    if len(sys.argv) > 1:
        webhook_url = sys.argv[1]
    else:
        webhook_url = input("请输入Lark webhook URL: ").strip()
    
    if not webhook_url:
        print("❌ 错误: 未提供webhook URL")
        return False
    
    print(f"🔍 测试Lark webhook连通性...")
    print(f"URL: {webhook_url[:50]}...")
    
    # 发送简单测试消息
    test_msg = {
        "msg_type": "text",
        "content": {
            "text": "🤖 测试消息 - 交易数据播报机器人连通性测试\n时间: " + str(datetime.now())
        }
    }
    
    try:
        resp = requests.post(
            webhook_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_msg, ensure_ascii=False),
            timeout=10
        )
        
        print(f"状态码: {resp.status_code}")
        print(f"响应内容: {resp.text}")
        
        if resp.status_code == 200:
            result = resp.json()
            if result.get("code") == 0:
                print("✅ 测试消息发送成功!")
                return True
            else:
                print(f"❌ 消息发送失败: code={result.get('code')}, msg={result.get('msg')}")
                return False
        else:
            print(f"❌ HTTP请求失败: {resp.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    from datetime import datetime
    success = test_lark_webhook()
    sys.exit(0 if success else 1)