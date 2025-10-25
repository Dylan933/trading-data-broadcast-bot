#!/usr/bin/env python3
"""
动量数据播报机器人 V0.1.1 - 重构版
基于新需求文档的精简实现：
1. 每小时UTC+8整点播报BTC、ETH、BNB技术分析
2. 12:00和00:00 UTC+8增强播报（半球数据+恐惧贪婪指数+相对强弱）
3. 仅通过飞书推送
"""

import argparse
import os
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple
import requests
import json


# API配置
BINANCE_API = "https://api.binance.com/api/v3/klines"
BINANCE_FUTURES_API = "https://fapi.binance.com/fapi/v1/klines"
FEAR_GREED_API = "https://api.alternative.me/fng/?limit=1&format=json"


def ema(series, period):
    """计算指数移动平均线"""
    if len(series) < period:
        return None
    k = 2 / (period + 1)
    ema_vals = []
    sma = sum(series[:period]) / period
    ema_vals.append(sma)
    for price in series[period:]:
        ema_vals.append(price * k + ema_vals[-1] * (1 - k))
    return ema_vals


def rsi_wilder(prices, period=14):
    """计算RSI指标"""
    if len(prices) < period + 1:
        return None
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    rsis = []
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else float("inf")
        rsi = 100 - (100 / (1 + rs))
        rsis.append(rsi)
    return rsis


def fetch_klines(symbol: str, interval: str = "1h", limit: int = 300) -> Dict[str, List[float]]:
    """获取现货K线数据"""
    try:
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        resp = requests.get(BINANCE_API, params=params, timeout=20)
        resp.raise_for_status()
        klines = resp.json()
        return {
            "closes": [float(k[4]) for k in klines],
            "highs": [float(k[2]) for k in klines],
            "lows": [float(k[3]) for k in klines],
            "times": [int(k[0]) for k in klines],
            "volumes": [float(k[5]) for k in klines],
            "quote_volumes": [float(k[7]) for k in klines],
        }
    except Exception as e:
        print(f"[ERROR] 获取{symbol}现货数据失败: {e}")
        raise


def fetch_futures_klines(symbol: str, interval: str = "1h", limit: int = 300) -> Dict[str, List[float]]:
    """获取合约K线数据"""
    try:
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        resp = requests.get(BINANCE_FUTURES_API, params=params, timeout=20)
        resp.raise_for_status()
        klines = resp.json()
        return {
            "closes": [float(k[4]) for k in klines],
            "highs": [float(k[2]) for k in klines],
            "lows": [float(k[3]) for k in klines],
            "times": [int(k[0]) for k in klines],
            "volumes": [float(k[5]) for k in klines],
            "quote_volumes": [float(k[7]) for k in klines],
        }
    except Exception as e:
        print(f"[ERROR] 获取{symbol}合约数据失败: {e}")
        raise


def fetch_fear_greed_index() -> Dict[str, str] | None:
    """获取恐惧贪婪指数"""
    try:
        resp = requests.get(FEAR_GREED_API, timeout=10)
        resp.raise_for_status()
        js = resp.json()
        data = js.get("data", [])
        if not data:
            return None
        
        item = data[0]
        raw_val = item.get("value")
        val = int(float(raw_val)) if raw_val is not None else None
        
        # 分类恐惧贪婪指数
        if val is None:
            return None
        elif val <= 24:
            classification = "极度恐惧"
        elif val <= 44:
            classification = "恐惧"
        elif val <= 55:
            classification = "中性"
        elif val <= 74:
            classification = "贪婪"
        else:
            classification = "极度贪婪"
        
        # 处理时间戳 - 修复未来时间戳问题
        ts = int(item.get("timestamp", 0))
        if ts > 0:
            # 检查时间戳是否为未来时间，如果是则使用当前时间
            current_ts = int(datetime.now().timestamp())
            if ts > current_ts:
                print(f"[WARN] 恐惧贪婪指数时间戳异常: {ts}, 使用当前时间")
                ts = current_ts
            updated = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")
        else:
            updated = "未知"
        
        return {"value": str(val), "classification": classification, "updated": updated}
    except Exception as e:
        print(f"[ERROR] 获取恐惧贪婪指数失败: {e}")
        return None


def calculate_technical_analysis(data: Dict[str, List[float]]) -> Dict[str, str]:
    """计算技术分析指标"""
    closes = data.get("closes", [])
    
    # EMA计算
    ema50_series = ema(closes, 50)
    ema200_series = ema(closes, 200)
    ema50 = ema50_series[-1] if ema50_series else None
    ema200 = ema200_series[-1] if ema200_series else None
    
    # RSI计算
    rsi_series = rsi_wilder(closes, 14)
    current_rsi = rsi_series[-1] if rsi_series else None
    
    # MACD计算
    ema12_series = ema(closes, 12)
    ema26_series = ema(closes, 26)
    macd_line_series = None
    if ema12_series and ema26_series:
        macd_line_series = [ema12_series[i] - ema26_series[i] for i in range(len(ema26_series))]
    signal_series = ema(macd_line_series, 9) if macd_line_series else None
    hist_series = None
    if macd_line_series and signal_series:
        hist_series = [macd_line_series[i + (len(macd_line_series) - len(signal_series))] - s for i, s in enumerate(signal_series)]
    macd_hist = hist_series[-1] if hist_series else None
    macd_hist_prev = hist_series[-2] if hist_series and len(hist_series) >= 2 else None
    
    # 趋势判断
    if ema50 is not None and ema200 is not None:
        if ema50 > ema200:
            trend = "EMA(50)>EMA(200)，趋势向上"
        elif ema50 < ema200:
            trend = "EMA(50)<EMA(200)，趋势向下"
        else:
            trend = "EMA(50)≈EMA(200)，趋势震荡"
    else:
        trend = "数据不足"
    
    # RSI描述
    if current_rsi is not None:
        if current_rsi >= 70:
            rsi_desc = f"{current_rsi:.1f}（超买）"
        elif current_rsi >= 65:
            rsi_desc = f"{current_rsi:.1f}（接近超买）"
        elif current_rsi <= 30:
            rsi_desc = f"{current_rsi:.1f}（超卖）"
        elif current_rsi <= 35:
            rsi_desc = f"{current_rsi:.1f}（接近超卖）"
        else:
            rsi_desc = f"{current_rsi:.1f}（中性）"
    else:
        rsi_desc = "数据不足"
    
    # MACD描述
    if macd_hist is not None and macd_hist_prev is not None:
        if macd_hist >= 0:
            macd_desc = "正向动能增强" if macd_hist > macd_hist_prev else "正向动能减弱"
        else:
            macd_desc = "负向动能增强" if macd_hist < macd_hist_prev else "负向动能减弱"
    else:
        macd_desc = "数据不足"
    
    # 综合判断
    if all([ema50, ema200, current_rsi, macd_hist, macd_hist_prev]):
        is_up = ema50 > ema200
        momentum_weaken = macd_hist < macd_hist_prev
        high_rsi = current_rsi >= 60
        low_rsi = current_rsi <= 40
        
        if is_up:
            if momentum_weaken and high_rsi:
                judgement = "短期可能回调，但中期趋势仍偏强"
            else:
                judgement = "中期趋势偏强，关注回踩机会"
        else:
            if not momentum_weaken and low_rsi:
                judgement = "短期可能反弹，但中期趋势偏弱"
            else:
                judgement = "中期趋势偏弱，谨慎操作"
    else:
        judgement = "数据不足，无法判断"
    
    return {
        "trend": trend,
        "rsi": rsi_desc,
        "macd": macd_desc,
        "judgement": judgement,
        "price": f"${closes[-1]:,.2f}" if closes else "—"
    }


def format_basic_analysis(symbol: str, data: Dict[str, List[float]]) -> str:
    """格式化基础技术分析播报"""
    analysis = calculate_technical_analysis(data)
    base_symbol = symbol.replace("USDT", "")
    
    return f"""📈 {base_symbol}/USDT: {analysis['price']}
趋势指标：{analysis['trend']}
RSI：{analysis['rsi']}
MACD：{analysis['macd']}
判断：{analysis['judgement']}"""


def calculate_hemisphere_stats(data: Dict[str, List[float]], hours: int = 12) -> Dict[str, float]:
    """计算半球时段统计数据 - 修复数据访问错误"""
    try:
        # 修复：正确访问字典中的列表数据
        closes = data.get("closes", [])
        volumes = data.get("volumes", [])
        quote_volumes = data.get("quote_volumes", [])  # 使用quote_volumes作为USDT交易量
        
        if len(closes) < hours:
            print(f"[WARN] 价格数据不足: {len(closes)} < {hours}")
            return {"volume": 0.0, "volatility": 0.0}
        
        # 获取最近12小时数据
        recent_closes = closes[-hours:]
        
        # 计算交易量（优先使用quote_volumes，即USDT交易量）
        total_volume = 0.0
        if quote_volumes and len(quote_volumes) >= hours:
            recent_quote_volumes = quote_volumes[-hours:]
            total_volume = sum(recent_quote_volumes)
            print(f"[DEBUG] 使用quote_volumes计算交易量: {total_volume:,.0f}")
        elif volumes and len(volumes) >= hours:
            recent_volumes = volumes[-hours:]
            # 使用最新价格估算USDT交易量
            latest_price = recent_closes[-1] if recent_closes else 1
            total_volume = sum(recent_volumes) * latest_price
            print(f"[DEBUG] 使用volumes*price估算交易量: {total_volume:,.0f}")
        else:
            print(f"[WARN] 交易量数据不足，使用默认值")
        
        # 计算波动率（价格标准差）
        volatility = 0.0
        if len(recent_closes) > 1:
            returns = [(recent_closes[i] / recent_closes[i-1] - 1) for i in range(1, len(recent_closes))]
            if returns:
                volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5 * 100
        
        print(f"[DEBUG] 半球统计结果: volume={total_volume:,.0f}, volatility={volatility:.2f}%")
        return {"volume": total_volume, "volatility": volatility}
    except Exception as e:
        print(f"[ERROR] 计算半球统计数据失败: {e}")
        return {"volume": 0.0, "volatility": 0.0}


def calculate_relative_strength(pairs: List[Tuple[str, str]], data_map: Dict[str, Dict[str, List[float]]]) -> str:
    """计算相对强弱分析"""
    try:
        results = []
        for base_sym, quote_sym in pairs:
            base_name = base_sym.replace("USDT", "")
            quote_name = quote_sym.replace("USDT", "")
            
            if base_sym in data_map and quote_sym in data_map:
                base_closes = data_map[base_sym].get("closes", [])
                quote_closes = data_map[quote_sym].get("closes", [])
                
                if len(base_closes) >= 24 and len(quote_closes) >= 24:
                    try:
                        # 计算24小时相对强弱
                        base_change = (base_closes[-1] / base_closes[-24] - 1) * 100
                        quote_change = (quote_closes[-1] / quote_closes[-24] - 1) * 100
                        relative_strength = base_change - quote_change
                        
                        if relative_strength > 0:
                            stronger = base_name
                            results.append(f"- {base_name}/{quote_name}：+{relative_strength:.1f}%（{stronger}相对强势）")
                        else:
                            stronger = quote_name
                            results.append(f"- {base_name}/{quote_name}：{relative_strength:.1f}%（{stronger}相对强势）")
                    except (ZeroDivisionError, IndexError) as e:
                        print(f"[WARN] {base_name}/{quote_name}计算失败: {e}")
                        results.append(f"- {base_name}/{quote_name}：计算错误")
                else:
                    results.append(f"- {base_name}/{quote_name}：数据不足")
            else:
                results.append(f"- {base_name}/{quote_name}：数据缺失")
        
        if results:
            return "💪 相对强弱：\n" + "\n".join(results)
        else:
            return "💪 相对强弱：\n- ETH/BTC：数据缺失\n- BNB/ETH：数据缺失"
    except Exception as e:
        print(f"[ERROR] 相对强弱分析失败: {e}")
        return "💪 相对强弱：\n- ETH/BTC：数据缺失\n- BNB/ETH：数据缺失"


def send_lark_message(webhook_url: str, content: str):
    """发送消息到飞书机器人"""
    try:
        msg = {
            "msg_type": "text",
            "content": {
                "text": content
            }
        }
        
        resp = requests.post(
            webhook_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(msg, ensure_ascii=False),
            timeout=10,
        )
        
        if resp.status_code != 200:
            print(f"[ERROR] 飞书推送失败: status={resp.status_code}, body={resp.text}")
        else:
            result = resp.json()
            if result.get("code") == 0:
                print("[INFO] 飞书推送成功")
            else:
                print(f"[ERROR] 飞书推送失败: code={result.get('code')}, msg={result.get('msg')}")
    except Exception as e:
        print(f"[ERROR] 飞书推送异常: {e}")


def send_telegram_message(bot_token: str, chat_id: str, content: str):
    """发送消息到Telegram机器人"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        # 简化消息格式，避免HTML解析问题
        # 移除所有HTML标签，使用纯文本格式
        clean_content = content.replace('**', '').replace('<b>', '').replace('</b>', '')
        
        payload = {
            "chat_id": chat_id,
            "text": clean_content,
            "disable_web_page_preview": True
        }
        
        resp = requests.post(url, json=payload, timeout=10)
        
        if resp.status_code != 200:
            print(f"[ERROR] Telegram推送失败: status={resp.status_code}, body={resp.text}")
        else:
            result = resp.json()
            if result.get("ok") is True:
                print("[INFO] Telegram推送成功")
            else:
                print(f"[ERROR] Telegram推送失败: {result}")
                
    except Exception as e:
        print(f"[ERROR] Telegram推送异常: {e}")


def run_broadcast(symbols: List[str], lark_webhook_url: str | None = None, telegram_bot_token: str | None = None, telegram_chat_id: str | None = None):
    """执行一次播报"""
    try:
        now_cn = datetime.now(timezone(timedelta(hours=8)))
        print(f"[INFO] 开始播报 - {now_cn.strftime('%Y-%m-%d %H:%M:%S')} UTC+8")
        
        # 获取所有数据
        data_map = {}
        for symbol in symbols:
            try:
                data_map[symbol] = fetch_klines(symbol)
                print(f"[INFO] 获取{symbol}数据成功")
            except Exception as e:
                print(f"[ERROR] 获取{symbol}数据失败: {e}")
        
        # 生成基础技术分析
        basic_messages = []
        for symbol in symbols:
            if symbol in data_map:
                try:
                    analysis = format_basic_analysis(symbol, data_map[symbol])
                    basic_messages.append(analysis)
                    print(f"[INFO] {symbol}技术分析完成")
                except Exception as e:
                    print(f"[ERROR] {symbol}技术分析失败: {e}")
        
        # 构建完整消息
        all_messages = []
        
        # 添加播报标题和时间
        now_str = now_cn.strftime('%Y-%m-%d %H:%M')
        title = f"🕐 市场播报 ({now_str} UTC+8)"
        all_messages.append(title)
        
        # 检查是否需要增强播报
        is_enhanced_time = now_cn.hour in [12, 0]
        if is_enhanced_time:
            print(f"[INFO] 执行增强播报 - {now_cn.hour}:00 UTC+8")
            
            # 半球时段描述
            if now_cn.hour == 12:
                period_desc = "🌍 东半球时段数据播报 (00:00-12:00 UTC+8)"
            else:
                period_desc = "🌍 西半球时段数据播报 (12:00-24:00 UTC+8)"
            
            all_messages.append(period_desc)
            
            # 半球时段统计
            hemisphere_stats = []
            for symbol in ["BTCUSDT", "ETHUSDT", "BNBUSDT"]:
                if symbol in data_map:
                    try:
                        stats = calculate_hemisphere_stats(data_map[symbol])
                        base_name = symbol.replace("USDT", "")
                        # 修复数据格式化问题
                        volume_str = f"{stats['volume']:,.0f}" if stats['volume'] > 0 else "数据缺失"
                        volatility_str = f"{stats['volatility']:.2f}%" if stats['volatility'] > 0 else "数据缺失"
                        stat_msg = f"- {base_name} 交易量：{volume_str} USDT，波动率：{volatility_str}"
                        hemisphere_stats.append(stat_msg)
                        print(f"[INFO] {symbol}半球统计完成: 交易量={stats['volume']}, 波动率={stats['volatility']}")
                    except Exception as e:
                        print(f"[ERROR] {symbol}半球统计失败: {e}")
                        base_name = symbol.replace("USDT", "")
                        hemisphere_stats.append(f"- {base_name} 交易量：数据缺失 USDT，波动率：数据缺失")
                else:
                    base_name = symbol.replace("USDT", "")
                    hemisphere_stats.append(f"- {base_name} 交易量：数据缺失 USDT，波动率：数据缺失")
            
            if hemisphere_stats:
                all_messages.append("📊 过去12小时统计：")
                all_messages.extend(hemisphere_stats)
            
            # 恐惧贪婪指数
            try:
                fear_greed = fetch_fear_greed_index()
                if fear_greed:
                    fgi_msg = f"😨 恐惧贪婪指数：{fear_greed['value']} ({fear_greed['classification']}，更新于 {fear_greed['updated']})"
                    all_messages.append(fgi_msg)
                    print("[INFO] 恐惧贪婪指数获取成功")
                else:
                    all_messages.append("😨 恐惧贪婪指数：数据获取失败")
                    print("[WARN] 恐惧贪婪指数数据为空")
            except Exception as e:
                print(f"[ERROR] 恐惧贪婪指数获取失败: {e}")
                all_messages.append("😨 恐惧贪婪指数：数据获取失败")
            
            # 相对强弱分析
            try:
                pairs = []
                available_symbols = set(data_map.keys())
                if {"ETHUSDT", "BTCUSDT"}.issubset(available_symbols):
                    pairs.append(("ETHUSDT", "BTCUSDT"))
                if {"BNBUSDT", "ETHUSDT"}.issubset(available_symbols):
                    pairs.append(("BNBUSDT", "ETHUSDT"))
                
                relative_strength = calculate_relative_strength(pairs, data_map)
                all_messages.append(relative_strength)
                print("[INFO] 相对强弱分析完成")
            except Exception as e:
                print(f"[ERROR] 相对强弱分析失败: {e}")
                all_messages.append("💪 相对强弱：\n- ETH/BTC：数据缺失\n- BNB/ETH：数据缺失")
        
        # 添加基础技术分析
        if basic_messages:
            all_messages.extend(basic_messages)
        
        # 发送到飞书
        if lark_webhook_url and all_messages:
            try:
                content = "\n\n".join(all_messages)
                send_lark_message(lark_webhook_url, content)
                print(f"[INFO] 飞书消息发送完成，内容长度: {len(content)}")
            except Exception as e:
                print(f"[ERROR] 飞书推送失败: {e}")
        
        # 发送到Telegram
        if telegram_bot_token and telegram_chat_id and all_messages:
            try:
                content = "\n\n".join(all_messages)
                send_telegram_message(telegram_bot_token, telegram_chat_id, content)
                print(f"[INFO] Telegram消息发送完成，内容长度: {len(content)}")
            except Exception as e:
                print(f"[ERROR] Telegram推送失败: {e}")
        
        print("[INFO] 播报完成")
        
    except Exception as e:
        print(f"[ERROR] 播报执行失败: {e}")


def sleep_until_next_hour():
    """等待到下一个整点"""
    now = datetime.now()
    secs = 3600 - (now.minute * 60 + now.second)
    if secs <= 0:
        secs = 3600
    print(f"[INFO] 等待 {secs} 秒到下一个整点")
    time.sleep(secs)


def main():
    parser = argparse.ArgumentParser(description="动量数据播报机器人 V0.1.1")
    parser.add_argument("--once", action="store_true", help="执行一次播报后退出")
    parser.add_argument(
        "--symbols",
        type=str,
        default="BTCUSDT,ETHUSDT,BNBUSDT",
        help="交易对列表，逗号分隔 (默认: BTCUSDT,ETHUSDT,BNBUSDT)",
    )
    parser.add_argument(
        "--lark-webhook",
        type=str,
        default=os.environ.get("LARK_WEBHOOK_URL"),
        help="飞书机器人Webhook URL",
    )
    parser.add_argument(
        "--telegram-bot-token",
        type=str,
        default=os.environ.get("TELEGRAM_BOT_TOKEN"),
        help="Telegram机器人Token",
    )
    parser.add_argument(
        "--telegram-chat-id",
        type=str,
        default=os.environ.get("TELEGRAM_CHAT_ID"),
        help="Telegram聊天ID",
    )
    
    args = parser.parse_args()
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    
    print(f"[INFO] 动量数据播报机器人启动")
    print(f"[INFO] 监控交易对: {', '.join(symbols)}")
    print(f"[INFO] 飞书推送: {'已配置' if args.lark_webhook else '未配置'}")
    print(f"[INFO] Telegram推送: {'已配置' if args.telegram_bot_token and args.telegram_chat_id else '未配置'}")
    
    if args.once:
        run_broadcast(symbols, args.lark_webhook, args.telegram_bot_token, args.telegram_chat_id)
    else:
        # 立即执行一次，然后每小时执行
        run_broadcast(symbols, args.lark_webhook, args.telegram_bot_token, args.telegram_chat_id)
        while True:
            try:
                sleep_until_next_hour()
                run_broadcast(symbols, args.lark_webhook, args.telegram_bot_token, args.telegram_chat_id)
            except KeyboardInterrupt:
                print("[INFO] 用户中断，程序退出")
                break
            except Exception as e:
                print(f"[ERROR] 循环执行异常: {e}")
                time.sleep(30)


if __name__ == "__main__":
    main()