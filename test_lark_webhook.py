#!/usr/bin/env python3
"""
测试Lark机器人webhook连通性的脚本
"""

import requests
import json
import os
import sys

def test_lark_webhook(webhook_url: str):
    """测试Lark webhook连通性"""
    
    # 测试1: 简单文本消息
    print("🔍 测试1: 发送简单文本消息...")
    simple_msg = {
        "msg_type": "text",
        "content": {
            "text": "测试消息 - 交易数据播报机器人连通性测试"
        }
    }
    
    try:
        resp = requests.post(
            webhook_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(simple_msg, ensure_ascii=False),
            timeout=10
        )
        
        print(f"   状态码: {resp.status_code}")
        print(f"   响应内容: {resp.text}")
        
        if resp.status_code == 200:
            result = resp.json()
            if result.get("code") == 0:
                print("   ✅ 简单文本消息发送成功!")
            else:
                print(f"   ❌ 消息发送失败: code={result.get('code')}, msg={result.get('msg')}")
                return False
        else:
            print(f"   ❌ HTTP请求失败: {resp.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
        return False
    
    print()
    
    # 测试2: 富文本消息（与实际播报格式相同）
    print("🔍 测试2: 发送富文本消息...")
    rich_msg = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": "交易数据播报测试",
                    "content": [
                        [{"tag": "text", "text": "【BTC/USDT - 1小时级别】", "style": ["bold"]}],
                        [{"tag": "text", "text": "趋势指标：测试中..."}],
                        [{"tag": "text", "text": "RSI：测试数据"}],
                        [{"tag": "text", "text": "判断：连通性测试成功"}]
                    ]
                }
            }
        }
    }
    
    try:
        resp = requests.post(
            webhook_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(rich_msg, ensure_ascii=False),
            timeout=10
        )
        
        print(f"   状态码: {resp.status_code}")
        print(f"   响应内容: {resp.text}")
        
        if resp.status_code == 200:
            result = resp.json()
            if result.get("code") == 0:
                print("   ✅ 富文本消息发送成功!")
                return True
            else:
                print(f"   ❌ 消息发送失败: code={result.get('code')}, msg={result.get('msg')}")
                return False
        else:
            print(f"   ❌ HTTP请求失败: {resp.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
        return False

def main():
    print("🤖 Lark机器人Webhook连通性测试")
    print("=" * 50)
    
    # 从环境变量或命令行参数获取webhook URL
    webhook_url = os.environ.get("LARK_WEBHOOK_URL")
    
    if len(sys.argv) > 1:
        webhook_url = sys.argv[1]
    
    if not webhook_url:
        print("❌ 错误: 未找到LARK_WEBHOOK_URL")
        print("使用方法:")
        print("  1. 设置环境变量: export LARK_WEBHOOK_URL='your_webhook_url'")
        print("  2. 或者直接传参: python test_lark_webhook.py 'your_webhook_url'")
        sys.exit(1)
    
    print(f"📡 测试Webhook地址: {webhook_url[:50]}...")
    print()
    
    success = test_lark_webhook(webhook_url)
    
    print()
    print("=" * 50)
    if success:
        print("🎉 测试完成: Webhook连通性正常!")
        print("💡 如果群里仍然收不到消息，请检查:")
        print("   1. 机器人的安全设置（关键词、IP白名单、签名校验）")
        print("   2. 机器人是否被正确添加到群组")
        print("   3. 群组权限设置")
    else:
        print("❌ 测试失败: Webhook连通性异常!")
        print("💡 可能的原因:")
        print("   1. Webhook地址错误")
        print("   2. 机器人安全设置阻止了消息")
        print("   3. 网络连接问题")
        print("   4. 机器人权限不足")

if __name__ == "__main__":
    main()