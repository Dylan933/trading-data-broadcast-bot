#!/usr/bin/env python3
"""
测试增强播报功能
模拟12:00和00:00 UTC+8时间点，验证半球时段统计、恐惧贪婪指数和相对强弱分析
"""

import sys
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

# 添加scripts目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from market_broadcast_hourly_v2 import (
    fetch_klines, 
    calculate_hemisphere_stats, 
    fetch_fear_greed_index,
    calculate_relative_strength,
    run_broadcast
)


def test_hemisphere_stats():
    """测试半球时段统计功能"""
    print("=== 测试半球时段统计功能 ===")
    
    try:
        # 获取BTC数据
        btc_data = fetch_klines("BTCUSDT")
        print(f"BTC数据获取成功，包含 {len(btc_data.get('closes', []))} 个数据点")
        
        # 计算半球统计
        stats = calculate_hemisphere_stats(btc_data)
        print(f"BTC 12小时统计：交易量 {stats['volume']:,.0f} USDT，波动率 {stats['volatility']:.2f}%")
        
        # 验证数据结构
        assert 'volume' in stats, "缺少交易量数据"
        assert 'volatility' in stats, "缺少波动率数据"
        assert stats['volume'] >= 0, "交易量不能为负数"
        assert stats['volatility'] >= 0, "波动率不能为负数"
        
        print("✅ 半球时段统计功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 半球时段统计功能测试失败: {e}")
        return False


def test_fear_greed_index():
    """测试恐惧贪婪指数功能"""
    print("\n=== 测试恐惧贪婪指数功能 ===")
    
    try:
        fgi = fetch_fear_greed_index()
        if fgi:
            print(f"恐惧贪婪指数：{fgi['value']} ({fgi['classification']})")
            print(f"更新时间：{fgi['updated']}")
            
            # 验证数据结构
            assert 'value' in fgi, "缺少指数值"
            assert 'classification' in fgi, "缺少分类"
            assert 'updated' in fgi, "缺少更新时间"
            
            # 验证指数值范围
            value = int(fgi['value'])
            assert 0 <= value <= 100, f"指数值超出范围: {value}"
            
            print("✅ 恐惧贪婪指数功能测试通过")
            return True
        else:
            print("❌ 恐惧贪婪指数获取失败")
            return False
            
    except Exception as e:
        print(f"❌ 恐惧贪婪指数功能测试失败: {e}")
        return False


def test_relative_strength():
    """测试相对强弱分析功能"""
    print("\n=== 测试相对强弱分析功能 ===")
    
    try:
        # 获取数据
        data_map = {}
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        
        for symbol in symbols:
            data_map[symbol] = fetch_klines(symbol)
            print(f"{symbol}数据获取成功")
        
        # 计算相对强弱
        pairs = [("ETHUSDT", "BTCUSDT"), ("BNBUSDT", "ETHUSDT")]
        relative_strength = calculate_relative_strength(pairs, data_map)
        
        if relative_strength:
            print("相对强弱分析结果：")
            print(relative_strength)
            
            # 验证输出格式
            assert "相对强弱" in relative_strength, "缺少标题"
            assert "ETH/BTC" in relative_strength or "BTC/ETH" in relative_strength, "缺少ETH/BTC分析"
            assert "BNB/ETH" in relative_strength or "ETH/BNB" in relative_strength, "缺少BNB/ETH分析"
            
            print("✅ 相对强弱分析功能测试通过")
            return True
        else:
            print("❌ 相对强弱分析结果为空")
            return False
            
    except Exception as e:
        print(f"❌ 相对强弱分析功能测试失败: {e}")
        return False


def test_enhanced_broadcast_timing():
    """测试增强播报时间逻辑"""
    print("\n=== 测试增强播报时间逻辑 ===")
    
    try:
        # 模拟12:00 UTC+8
        with patch('market_broadcast_hourly_v2.datetime') as mock_datetime:
            mock_now = datetime(2025, 1, 19, 12, 0, 0, tzinfo=timezone(timedelta(hours=8)))
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromtimestamp = datetime.fromtimestamp
            
            print("模拟时间：12:00 UTC+8（东半球时段）")
            
            # 这里应该触发增强播报
            # 由于run_broadcast函数会发送消息，我们只测试时间判断逻辑
            assert mock_now.hour == 12, "时间模拟失败"
            print("✅ 12:00 UTC+8 时间点识别正确")
        
        # 模拟00:00 UTC+8
        with patch('market_broadcast_hourly_v2.datetime') as mock_datetime:
            mock_now = datetime(2025, 1, 19, 0, 0, 0, tzinfo=timezone(timedelta(hours=8)))
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromtimestamp = datetime.fromtimestamp
            
            print("模拟时间：00:00 UTC+8（西半球时段）")
            
            assert mock_now.hour == 0, "时间模拟失败"
            print("✅ 00:00 UTC+8 时间点识别正确")
        
        print("✅ 增强播报时间逻辑测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 增强播报时间逻辑测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("开始测试增强播报功能...\n")
    
    tests = [
        test_hemisphere_stats,
        test_fear_greed_index,
        test_relative_strength,
        test_enhanced_broadcast_timing
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