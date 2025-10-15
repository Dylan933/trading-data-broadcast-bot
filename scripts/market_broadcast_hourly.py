#!/usr/bin/env python3
"""
Hourly market broadcast for Binance symbols, formatted per user's template.

Default: BTCUSDT on 1h interval. Prints:
【SYMBOL/USDT - 1小时级别】
趋势指标：EMA(50)>EMA(200)/< 等
RSI：值（区间描述）
MACD：动能增强/减弱
判断：基于EMA/RSI/MACD的简评
关键支撑/压力：Donchian(20)
时间：本地(UTC+8)
最新价：价格

Run options:
  --once    Run a single broadcast and exit
  --symbols BTCUSDT,ETHUSDT   Comma separated list

Note: Requests will respect HTTP(S)_PROXY environment variables (e.g., 127.0.0.1:7890)
"""

import argparse
import os
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple

import requests
import json


BINANCE_API = "https://api.binance.com/api/v3/klines"


def ema(series, period):
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


def fmt_price(x):
    return f"${x:,.2f}" if x is not None else "—"


def fetch_klines(symbol: str, interval: str = "1h", limit: int = 300) -> Dict[str, List[float]]:
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

FAPI = "https://fapi.binance.com/fapi/v1/klines"

def fetch_futures_klines(symbol: str, interval: str = "1h", limit: int = 300) -> Dict[str, List[float]]:
    """Fetch USDT-M futures klines to compute volume stats."""
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    resp = requests.get(FAPI, params=params, timeout=20)
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

def sum_last_n(vols: List[float], n: int) -> float:
    if not vols:
        return 0.0
    return float(sum(vols[-n:]))


def _escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )


def write_html(messages: List[str], now_cn_str: str, out_dir: str | None):
    """Render current broadcast to a simple static HTML page.

    - Writes index.html under out_dir
    - Each message rendered as a card with <pre> preserving line breaks
    """
    if not out_dir:
        return
    try:
        os.makedirs(out_dir, exist_ok=True)
        cards = []
        for msg in messages:
            cards.append(f"<div class=\"card\"><pre>{_escape_html(msg)}</pre></div>")
        body = "\n".join(cards) if cards else "<p>暂无内容</p>"
        html = f"""<!doctype html>
<html lang=\"zh\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>市场播报</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif; margin: 24px; background: #f7f8fa; }}
    h1 {{ margin: 0 0 8px; font-size: 22px; }}
    .meta {{ color: #666; margin-bottom: 16px; }}
    .card {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 12px 16px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }}
    pre {{ white-space: pre-wrap; word-wrap: break-word; margin: 0; }}
  </style>
</head>
<body>
  <h1>市场播报</h1>
  <div class=\"meta\">更新时间：{_escape_html(now_cn_str)} (UTC+8)</div>
  {body}
</body>
</html>"""
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
    except Exception as e:
        print(f"[ERROR] write_html: {e}")


# Fear & Greed Index (Crypto) from alternative.me
def _classify_fgi(value: int) -> str:
    try:
        v = int(value)
    except Exception:
        return "—"
    if v <= 24:
        return "极度恐惧"
    if v <= 44:
        return "恐惧"
    if v <= 55:
        return "中性"
    if v <= 74:
        return "贪婪"
    return "极度贪婪"


def fetch_fear_greed_index() -> Dict[str, str] | None:
    """Fetch latest Crypto Fear & Greed Index.

    Source: https://api.alternative.me/fng/?limit=1&format=json
    Returns dict with keys: value (int), classification (str), updated (str UTC+8)
    """
    try:
        url = "https://api.alternative.me/fng/?limit=1&format=json"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        js = resp.json()
        data = js.get("data", [])
        if not data:
            return None
        item = data[0]
        raw_val = item.get("value")
        try:
            val = int(float(raw_val)) if raw_val is not None else None
        except Exception:
            val = None
        cls = item.get("value_classification") if item.get("value_classification") else (_classify_fgi(val) if val is not None else "—")
        ts = int(item.get("timestamp", 0))
        updated = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M") if ts else "—"
        if val is None:
            return None
        return {"value": str(val), "classification": cls, "updated": updated}
    except Exception:
        return None


def format_from_data(
    symbol: str,
    data: Dict[str, List[float]],
    lookback_sr: int = 20,
    fut_data: Dict[str, List[float]] | None = None,
    tone: str = "balanced",
):
    closes = data.get("closes", [])
    highs = data.get("highs", [])
    lows = data.get("lows", [])
    times = data.get("times", [])
    spot_vols = data.get("volumes", [])
    spot_quote_vols = data.get("quote_volumes", [])

    ema50_series = ema(closes, 50)
    ema200_series = ema(closes, 200)
    ema50 = ema50_series[-1] if ema50_series else None
    ema200 = ema200_series[-1] if ema200_series else None

    rsi_series = rsi_wilder(closes, 14)
    rsi = rsi_series[-1] if rsi_series else None

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

    trend = "数据不足，无法计算EMA趋势。"
    if ema50 is not None and ema200 is not None:
        if ema50 > ema200:
            trend = "EMA(50)>EMA(200)，趋势向上。"
        elif ema50 < ema200:
            trend = "EMA(50)<EMA(200)，趋势向下。"
        else:
            trend = "EMA(50)≈EMA(200)，趋势震荡。"

    if rsi is not None:
        if rsi >= 70:
            rsi_desc = f"{rsi:.2f}（超买）"
        elif rsi >= 65:
            rsi_desc = f"{rsi:.2f}（接近超买）"
        elif rsi <= 30:
            rsi_desc = f"{rsi:.2f}（超卖）"
        elif rsi <= 35:
            rsi_desc = f"{rsi:.2f}（接近超卖）"
        else:
            rsi_desc = f"{rsi:.2f}（中性）"
    else:
        rsi_desc = "—"

    macd_desc = "—"
    if macd_hist is not None and macd_hist_prev is not None:
        if macd_hist >= 0:
            macd_desc = "正向动能增强" if macd_hist > macd_hist_prev else "正向动能减弱"
        else:
            macd_desc = "负向动能增强" if macd_hist < macd_hist_prev else "负向动能减弱"

    judgement = "—"
    if (
        ema50 is not None
        and ema200 is not None
        and rsi is not None
        and macd_hist is not None
        and macd_hist_prev is not None
    ):
        is_up = ema50 > ema200
        is_down = ema50 < ema200
        momentum_weaken = macd_hist < macd_hist_prev
        momentum_improve = macd_hist > macd_hist_prev
        high_rsi = rsi >= 60
        low_rsi = rsi <= 40

        if tone not in {"conservative", "balanced", "aggressive"}:
            tone = "balanced"

        if is_up:
            if momentum_weaken and high_rsi:
                if tone == "aggressive":
                    judgement = "顺势逢回踩轻仓做多，若失守支撑及时止损。"
                elif tone == "conservative":
                    judgement = "保持观望或逢高减仓，等待动能恢复/关键位企稳后再介入。"
                else:
                    judgement = "短期可能回调，但中期趋势仍偏强。"
            else:
                if tone == "aggressive":
                    judgement = "顺势跟随，可分批做多；若有效突破压力，尝试追随。"
                elif tone == "conservative":
                    judgement = "不追涨，等待回踩确认再考虑；严格执行止盈/止损纪律。"
                else:
                    judgement = "中期趋势偏强，短线关注回踩/震荡机会。"
        elif is_down:
            if momentum_improve and low_rsi:
                if tone == "aggressive":
                    judgement = "反弹博短，轻仓快进快出；压力位附近考虑做空。"
                elif tone == "conservative":
                    judgement = "反弹以减仓为主，谨慎抄底，等待明确反转信号。"
                else:
                    judgement = "短期或有反弹，中期趋势仍偏弱。"
            else:
                if tone == "aggressive":
                    judgement = "顺势做空为主，跌破支撑可跟随加空。"
                elif tone == "conservative":
                    judgement = "以风险控制为先，反弹不接力；耐心等待底部结构成形。"
                else:
                    judgement = "中期趋势偏弱，反弹以减仓为主。"
        else:
            if tone == "aggressive":
                judgement = "区间内高抛低吸，若出现明确突破则快速跟随。"
            elif tone == "conservative":
                judgement = "减少交易频次，等待趋势明朗后再参与。"
            else:
                judgement = "趋势震荡，区间交易为主。"

    # Support/Resistance: Donchian 20
    if len(highs) >= lookback_sr:
        resistance = max(highs[-lookback_sr:])
        support = min(lows[-lookback_sr:])
    else:
        resistance = max(highs) if highs else None
        support = min(lows) if lows else None

    last_close = closes[-1]
    last_time_ms = times[-1]
    # 使用当前实时时间而不是K线时间戳，确保时间准确
    cn_time = datetime.now(timezone(timedelta(hours=8)))

    lines = [
        f"➡️【{symbol.replace('USDT','')}/USDT - 1小时级别】",
        f"时间：{cn_time.strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)",
        f"最新价格：{fmt_price(last_close)}",
        f"关键支撑：{fmt_price(support)}；压力：{fmt_price(resistance)}。",
        f"趋势指标：{trend}",
        f"RSI：{rsi_desc}",
        f"MACD：{macd_desc}",
        f"判断：{judgement}",
    ]
    # 成交额与相对强弱仅在每日08:00(UTC+8)追加，由 run_once 控制
    return "\n".join(lines)


def relative_strength_report(pairs: List[Tuple[str, str]], data_map: Dict[str, Dict[str, List[float]]]) -> str:
    lines = ["相对强弱："]
    for base, quote in pairs:
        base_disp = base.replace("USDT", "")
        quote_disp = quote.replace("USDT", "")
        if base not in data_map or quote not in data_map:
            lines.append(f"- {base_disp}/{quote_disp}：数据缺失")
            continue
        base_cl = data_map[base].get("closes", [])
        quote_cl = data_map[quote].get("closes", [])
        n = min(len(base_cl), len(quote_cl))
        if n < 2:
            lines.append(f"- {base_disp}/{quote_disp}：数据不足")
            continue
        ratio_series = [b / q for b, q in zip(base_cl[-n:], quote_cl[-n:])]
        last_ratio = ratio_series[-1]
        prev_ratio = ratio_series[-2]
        change_pct = ((last_ratio - prev_ratio) / prev_ratio) * 100 if prev_ratio != 0 else 0.0

        rs_ema50 = ema(ratio_series, 50)
        rs_ema200 = ema(ratio_series, 200)
        
        # 综合判断：结合短期动量和长期趋势
        short_term = "走强" if change_pct > 0 else "走弱" if change_pct < 0 else "持平"
        
        if rs_ema50 and rs_ema200:
            if rs_ema50[-1] > rs_ema200[-1]:
                long_term = f"{base_disp}长期占优"
            elif rs_ema50[-1] < rs_ema200[-1]:
                long_term = f"{quote_disp}长期占优"
            else:
                long_term = "长期均衡"
                
            # 综合短期和长期
            if change_pct > 0:
                trend_text = f"{base_disp}短期{short_term}，{long_term}"
            elif change_pct < 0:
                trend_text = f"{quote_disp}短期{short_term}，{long_term}"
            else:
                trend_text = f"短期{short_term}，{long_term}"
        else:
            if change_pct > 0:
                trend_text = f"{base_disp}短期{short_term}"
            elif change_pct < 0:
                trend_text = f"{quote_disp}短期{short_term}"
            else:
                trend_text = "短期持平，数据不足判断长期趋势"

        lines.append(
            f"- {base_disp}/{quote_disp}：比值 {last_ratio:.4f}（1小时变动 {change_pct:+.2f}%），趋势：{trend_text}"
        )
    return "\n".join(lines)


def sleep_until_next_hour():
    now = datetime.now()
    # seconds until next hour boundary
    secs = 3600 - (now.minute * 60 + now.second)
    if secs <= 0:
        secs = 3600
    time.sleep(secs)


def send_wecom_markdown(webhook_url: str, content: str):
    try:
        resp = requests.post(
            webhook_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps({"msgtype": "markdown", "markdown": {"content": content}}),
            timeout=10,
        )
        if resp.status_code != 200 or resp.json().get("errcode") not in (0, None):
            print(f"[WARN] WeCom push failed: status={resp.status_code}, body={resp.text}")
        else:
            print("[INFO] WeCom push sent.")
    except Exception as e:
        print(f"[ERROR] WeCom push error: {e}")


def run_once(symbols: List[str], webhook_url: str | None = None, tone: str = "balanced", html_out: str | None = None):
    messages = []
    data_map: Dict[str, Dict[str, List[float]]] = {}
    fut_map: Dict[str, Dict[str, List[float]]] = {}
    # Fetch data for all symbols first
    for sym in symbols:
        try:
            data_map[sym] = fetch_klines(sym)
        except Exception as e:
            print(f"[ERROR] {sym}: {e}")
        try:
            fut_map[sym] = fetch_futures_klines(sym)
        except Exception as e:
            print(f"[ERROR] futures {sym}: {e}")
    # Format per-symbol messages
    for sym in symbols:
        try:
            if sym in data_map:
                msg = format_from_data(sym, data_map[sym], fut_data=fut_map.get(sym), tone=tone)
                print(msg)
                messages.append(msg)
        except Exception as e:
            print(f"[ERROR] format {sym}: {e}")
    # Hemisphere-based additions at 12:00 and 00:00 (UTC+8)
    now_cn = datetime.now(timezone(timedelta(hours=8)))
    if now_cn.hour in [12, 0]:  # 12:00 (Eastern) and 00:00 (Western)
        hemisphere = "东半球" if now_cn.hour == 12 else "西半球"
        time_range = "12:00-00:00" if now_cn.hour == 12 else "00:00-12:00"
        
        # Calculate hemisphere trading volume and volatility for BTC and ETH
        hemisphere_symbols = ["BTCUSDT", "ETHUSDT"]
        for sym in hemisphere_symbols:
            if sym in symbols and sym in data_map and sym in fut_map:
                try:
                    # Get 12-hour data (half day)
                    spot_data = data_map[sym]
                    fut_data = fut_map[sym]
                    
                    # 12-hour volume (last 12 hours)
                    spot_vol_12h = sum_last_n(spot_data.get("quote_volumes", []), 12)
                    fut_vol_12h = sum_last_n(fut_data.get("quote_volumes", []), 12)
                    
                    # 12-hour volatility calculation (standard deviation of returns)
                    closes = spot_data.get("closes", [])
                    if len(closes) >= 13:  # Need at least 13 points for 12 returns
                        returns = [(closes[i] / closes[i-1] - 1) * 100 for i in range(-12, 0)]
                        volatility = (sum([(r - sum(returns)/len(returns))**2 for r in returns]) / len(returns))**0.5
                    else:
                        volatility = 0.0
                    
                    vol_line = f"{hemisphere}时段（{time_range} UTC+8）{sym.replace('USDT', '')}合约数据：交易量≈${fut_vol_12h:,.0f}；波动率{volatility:.2f}%"
                    print(vol_line)
                    messages.append(vol_line)
                except Exception as e:
                    print(f"[ERROR] hemisphere data {sym}: {e}")
        
        # Fear & Greed Index (keep at both times)
        fgi = fetch_fear_greed_index()
        if fgi:
            fgi_line = f"恐惧贪婪指数：{fgi['value']}（{fgi['classification']}，更新于 {fgi['updated']}）"
        else:
            fgi_line = "恐惧贪婪指数：数据源不可用"
        print(fgi_line)
        messages.append(fgi_line)
        
        # Relative strength section at both hemisphere times
        pairs: List[Tuple[str, str]] = []
        symset = set(symbols)
        # ETH/BTC and BNB/ETH
        if {"ETHUSDT", "BTCUSDT"}.issubset(symset):
            pairs.append(("ETHUSDT", "BTCUSDT"))
        if {"BNBUSDT", "ETHUSDT"}.issubset(symset):
            pairs.append(("BNBUSDT", "ETHUSDT"))
        if pairs:
            try:
                rs_text = relative_strength_report(pairs, data_map)
                print(rs_text)
                messages.append(rs_text)
            except Exception as e:
                print(f"[ERROR] relative strength: {e}")
    # Aggregate, write HTML, and push to WeCom if configured
    now_cn_str = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M')
    write_html(messages, now_cn_str, html_out)
    if webhook_url:
        content = f"**市场播报（{now_cn_str}）**\n\n" + "\n\n".join(messages)
        send_wecom_markdown(webhook_url, content)


def run_hourly(symbols: List[str], webhook_url: str | None = None, tone: str = "balanced", html_out: str | None = None):
    # Initial run immediately, then align to next hour, then hourly
    run_once(symbols, webhook_url, tone, html_out)
    while True:
        try:
            sleep_until_next_hour()
            run_once(symbols, webhook_url, tone, html_out)
        except KeyboardInterrupt:
            print("[INFO] Stopped by user.")
            break
        except Exception as e:
            print(f"[ERROR] loop: {e}")
            time.sleep(30)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run a single broadcast and exit")
    parser.add_argument(
        "--symbols",
        type=str,
        default="BTCUSDT,ETHUSDT,BNBUSDT",
        help="Comma separated Binance symbols (e.g., BTCUSDT,ETHUSDT,BNBUSDT)",
    )
    parser.add_argument(
        "--webhook",
        type=str,
        default=os.environ.get("WECHAT_WEBHOOK_URL"),
        help="WeCom (企业微信群机器人) webhook URL to push markdown messages",
    )
    parser.add_argument(
        "--tone",
        type=str,
        choices=["conservative", "balanced", "aggressive"],
        default="balanced",
        help="播报语气：conservative|balanced|aggressive（仅影响文案措辞）",
    )
    parser.add_argument(
        "--html_out",
        type=str,
        default=None,
        help="将播报内容输出为静态HTML页面（目录路径）",
    )
    args = parser.parse_args()
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    if args.once:
        run_once(symbols, args.webhook, tone=args.tone, html_out=args.html_out)
    else:
        run_hourly(symbols, args.webhook, tone=args.tone, html_out=args.html_out)


if __name__ == "__main__":
    main()