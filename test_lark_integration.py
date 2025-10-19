#!/usr/bin/env python3
"""
飞书集成测试脚本
测试消息格式和推送功能（使用模拟webhook避免实际发送）
"""

import sys
import os
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

# 添加scripts目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from market_broadcast_hourly_v2 import (
    send_lark_message,
    format_basic_analysis,
    fetch_klines,
    run_broadcast
)


def test_lark_message_format():
    """测试飞书消息格式"""
    print("=== 测试飞书消息格式 ===")
    
    try:
        # 模拟数据
        mock_data = {
            "closes": [67000.0, 67100.0, 67200.0] + [67000.0] * 297,
            "highs": [67500.0] * 300,
            "lows": [66500.0] * 300,
            "times": [1640000000000] * 300,
            "volumes": [1000.0] * 300,
            "quote_volumes": [67000000.0] * 300,
        }
        
        # 测试基础分析格式
        analysis = format_basic_analysis("BTCUSDT", mock_data)
        print("基础分析格式：")
        print(analysis)
        
        # 验证格式
        assert "BTC/USDT" in analysis, "缺少交易对标识"
        assert "$" in analysis, "缺少价格信息"
        assert "趋势指标" in analysis, "缺少趋势指标"
        assert "RSI" in analysis, "缺少RSI指标"
        assert "MACD" in analysis, "缺少MACD指标"
        assert "判断" in analysis, "缺少判断信息"
        
        print("✅ 飞书消息格式测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 飞书消息格式测试失败: {e}")
        return False


def test_lark_webhook_call():
    """测试飞书webhook调用"""
    print("\n=== 测试飞书webhook调用 ===")
    
    try:
        # 模拟requests.post
        with patch('market_broadcast_hourly_v2.requests.post') as mock_post:
            # 设置成功响应
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"code": 0, "msg": "success"}
            mock_post.return_value = mock_response
            
            # 测试发送消息
            test_content = "测试消息内容"
            send_lark_message("https://test.webhook.url", test_content)
            
            # 验证调用
            assert mock_post.called, "webhook未被调用"
            
            # 验证调用参数
            call_args = mock_post.call_args
            assert call_args[0][0] == "https://test.webhook.url", "webhook URL不正确"
            
            # 验证消息格式
            data = json.loads(call_args[1]['data'])
            assert data['msg_type'] == 'text', "消息类型不正确"
            assert data['content']['text'] == test_content, "消息内容不正确"
            
            print("✅ 飞书webhook调用测试通过")
            return True
            
    except Exception as e:
        print(f"❌ 飞书webhook调用测试失败: {e}")
        return False


def test_enhanced_broadcast_message():
    """测试增强播报消息格式"""
    print("\n=== 测试增强播报消息格式 ===")
    
    try:
        # 模拟12:00 UTC+8时间
        with patch('market_broadcast_hourly_v2.datetime') as mock_datetime:
            mock_now = datetime(2025, 1, 19, 12, 0, 0, tzinfo=timezone(timedelta(hours=8)))
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromtimestamp = datetime.fromtimestamp
            
            # 模拟requests调用以避免实际网络请求
            with patch('market_broadcast_hourly_v2.requests.get') as mock_get, \
                 patch('market_broadcast_hourly_v2.requests.post') as mock_post:
                
                # 模拟K线数据响应
                mock_kline_response = MagicMock()
                mock_kline_response.status_code = 200
                mock_kline_response.json.return_value = [
                    [1640000000000, "67000", "67500", "66500", "67200", "1000", 1640003600000, "67200000", 100, "500", "33600000", "0"]
                ] * 300
                mock_get.return_value = mock_kline_response
                
                # 模拟飞书响应
                mock_lark_response = MagicMock()
                mock_lark_response.status_code = 200
                mock_lark_response.json.return_value = {"code": 0, "msg": "success"}
                mock_post.return_value = mock_lark_response
                
                # 捕获发送的消息内容
                sent_messages = []
                def capture_message(url, **kwargs):
                    data = json.loads(kwargs['data'])
                    sent_messages.append(data['content']['text'])
                    return mock_lark_response
                
                mock_post.side_effect = capture_message
                
                # 运行播报
                run_broadcast(["BTCUSDT", "ETHUSDT", "BNBUSDT"], "https://test.webhook.url")
                
                # 验证消息内容
                if sent_messages:
                    message = sent_messages[0]
                    print("增强播报消息预览：")
                    print(message[:500] + "..." if len(message) > 500 else message)
                    
                    # 验证增强播报内容
                    assert "东半球时段数据播报" in message, "缺少半球时段标识"
                    assert "过去12小时统计" in message, "缺少半球统计"
                    assert "BTC" in message and "ETH" in message and "BNB" in message, "缺少交易对分析"
                    assert "相对强弱" in message, "缺少相对强弱分析"
                    
                    print("✅ 增强播报消息格式测试通过")
                    return True
                else:
                    print("❌ 未捕获到发送的消息")
                    return False
                    
    except Exception as e:
        print(f"❌ 增强播报消息格式测试失败: {e}")
        return False


def test_error_handling():
    """测试错误处理机制"""
    print("\n=== 测试错误处理机制 ===")
    
    try:
        # 测试网络错误处理
        with patch('market_broadcast_hourly_v2.requests.post') as mock_post:
            # 模拟网络错误
            mock_post.side_effect = Exception("Network error")
            
            # 这应该不会抛出异常，而是打印错误日志
            send_lark_message("https://test.webhook.url", "test message")
            
            print("✅ 网络错误处理测试通过")
        
        # 测试HTTP错误处理
        with patch('market_broadcast_hourly_v2.requests.post') as mock_post:
            # 模拟HTTP错误
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_post.return_value = mock_response
            
            # 这应该不会抛出异常，而是打印错误日志
            send_lark_message("https://test.webhook.url", "test message")
            
            print("✅ HTTP错误处理测试通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误处理机制测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("开始测试飞书集成功能...\n")
    
    tests = [
        test_lark_message_format,
        test_lark_webhook_call,
        test_enhanced_broadcast_message,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    exit(main())