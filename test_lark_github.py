#!/usr/bin/env python3
"""
GitHub Actions中测试Lark webhook连接性的脚本
"""
import requests
import json
import os
import sys

def test_lark_webhook():
    webhook_url = os.environ.get('LARK_WEBHOOK_URL')
    
    if not webhook_url:
        print("ERROR: LARK_WEBHOOK_URL environment variable not set")
        return False
    
    print(f"Testing Lark webhook: {webhook_url[:50]}...")
    
    try:
        response = requests.post(
            webhook_url,
            headers={'Content-Type': 'application/json'},
            json={
                'msg_type': 'text',
                'content': {
                    'text': 'GitHub Actions测试消息 - Lark连接性测试'
                }
            },
            timeout=10
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Lark webhook test PASSED")
            return True
        else:
            print("❌ Lark webhook test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Lark webhook test FAILED with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_lark_webhook()
    sys.exit(0 if success else 1)