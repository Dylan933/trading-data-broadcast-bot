#!/usr/bin/env python3
"""
临时播报脚本 - 获取并显示详细技术分析数据
"""

import sys
import os
sys.path.append('scripts')

from market_broadcast_hourly_v2 import (
    fetch_klines, 
    calculate_technical_analysis, 
    format_basic_analysis,
    fetch_fear_greed_index,
    calculate_hemisphere_stats,
    calculate_relative_strength
)
from datetime import datetime, timezone, timedelta

def main():
    print("🚀 动量数据播报机器人 - 临时播报")
    print("=" * 50)
    
    # 获取当前时间
    beijing_tz = timezone(timedelta(hours=8))
    current_time = datetime.now(beijing_tz)
    print(f"📅 播报时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')} UTC+8")
    print()
    
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    data_map = {}
    
    # 获取数据并进行技术分析
    for symbol in symbols:
        print(f"📊 正在分析 {symbol}...")
        try:
            data = fetch_klines(symbol)
            data_map[symbol] = data
            
            # 格式化基础分析
            analysis_text = format_basic_analysis(symbol, data)
            print(analysis_text)
            print("-" * 30)
            
        except Exception as e:
            print(f"❌ {symbol} 数据获取失败: {e}")
            print("-" * 30)
    
    # 检查是否为增强播报时间 (12:00 或 00:00 UTC+8)
    current_hour = current_time.hour
    if current_hour in [12, 0]:
        print("\n🌍 增强播报数据")
        print("=" * 30)
        
        # 半球时段统计
        if "BTCUSDT" in data_map and "ETHUSDT" in data_map:
            try:
                btc_stats = calculate_hemisphere_stats(data_map["BTCUSDT"])
                eth_stats = calculate_hemisphere_stats(data_map["ETHUSDT"])
                
                hemisphere = "东半球" if current_hour == 12 else "西半球"
                print(f"📈 {hemisphere}时段统计 (过去12小时)")
                print(f"BTC合约交易量: {btc_stats['volume']:,.0f}")
                print(f"BTC波动率: {btc_stats['volatility']:.2f}%")
                print(f"ETH合约交易量: {eth_stats['volume']:,.0f}")
                print(f"ETH波动率: {eth_stats['volatility']:.2f}%")
                print()
            except Exception as e:
                print(f"❌ 半球统计计算失败: {e}")
        
        # 恐惧贪婪指数
        try:
            fgi_data = fetch_fear_greed_index()
            if fgi_data:
                print(f"😱 恐惧贪婪指数: {fgi_data['value']} ({fgi_data['classification']})")
                print(f"更新时间: {fgi_data['timestamp']}")
                print()
        except Exception as e:
            print(f"❌ 恐惧贪婪指数获取失败: {e}")
        
        # 相对强弱分析
        try:
            pairs = [("BTC", "ETH"), ("BTC", "BNB"), ("ETH", "BNB")]
            relative_strength = calculate_relative_strength(pairs, data_map)
            print("💪 相对强弱分析")
            print(relative_strength)
        except Exception as e:
            print(f"❌ 相对强弱分析失败: {e}")
    
    print("\n✅ 播报完成")

if __name__ == "__main__":
    main()