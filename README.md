# 交易数据播报机器人 V0.1.1

## 🆕 V0.1.1 新特性

### 半球时间播报系统
- **东半球时段**（12:00 UTC+8）：播报12:00-00:00时段的BTC、ETH合约交易量和波动率
- **西半球时段**（00:00 UTC+8）：播报00:00-12:00时段的BTC、ETH合约交易量和波动率
- 替换原有的每日08:00播报机制

## 📊 功能特性

### 核心功能
- **每小时市场播报**：BTC、ETH、BNB技术分析
- **半球时间统计**：东西半球时段的交易量和波动率分析
- **恐惧贪婪指数**：每日市场情绪指标
- **相对强弱分析**：ETH/BTC、BNB/ETH比值分析（已修复逻辑）
- **企业微信推送**：支持WeCom机器人消息推送
- **HTML静态页面**：生成美观的网页版播报

### 播报时间
- **每小时**：基础技术分析播报
- **12:00 UTC+8**：东半球时段数据 + 恐惧贪婪指数 + 相对强弱
- **00:00 UTC+8**：西半球时段数据 + 恐惧贪婪指数 + 相对强弱

## 🚀 使用方法

### 本地运行

#### 安装依赖
```bash
pip install -r requirements.txt
```

#### 单次执行
```bash
python3 scripts/market_broadcast_hourly.py --once --symbols BTCUSDT,ETHUSDT,BNBUSDT --tone aggressive
```

#### 持续运行（每小时播报）
```bash
python3 scripts/market_broadcast_hourly.py --symbols BTCUSDT,ETHUSDT,BNBUSDT --webhook "YOUR_WECHAT_WEBHOOK_URL" --tone aggressive
```

#### 生成HTML页面
```bash
python3 scripts/market_broadcast_hourly.py --symbols BTCUSDT,ETHUSDT,BNBUSDT --html_out /path/to/output/directory --tone aggressive
```

### GitHub Actions 自动化

#### 配置步骤
1. Fork此仓库到你的GitHub账户
2. 在仓库设置中添加Secrets：
   - `WECHAT_WEBHOOK_URL`：企业微信机器人Webhook地址
3. 可选：在Variables中设置：
   - `SYMBOLS`：交易对（默认：BTCUSDT,ETHUSDT,BNBUSDT）
   - `TONE`：播报语调（aggressive/balanced/conservative，默认：balanced）

#### 自动执行
- **每小时自动运行**：UTC时间每小时执行
- **手动触发**：在Actions页面手动运行
- **移动端接收**：通过企业微信接收推送消息

## 📱 移动端使用

### 企业微信推送
1. 创建企业微信群机器人
2. 获取Webhook URL
3. 配置到GitHub Secrets或本地环境变量
4. 手机端实时接收播报消息

### 网页版查看
1. 使用`--html_out`参数生成静态页面
2. 部署到GitHub Pages或其他静态托管服务
3. 手机浏览器访问查看

## ⚙️ 命令行参数

- `--once`：单次执行后退出
- `--symbols`：指定交易对（逗号分隔）
- `--webhook`：企业微信Webhook URL
- `--tone`：播报语调
  - `conservative`：保守（建议谨慎操作）
  - `balanced`：平衡（默认，中性建议）
  - `aggressive`：激进（建议积极操作）
- `--html_out`：HTML输出目录路径

## 📈 数据来源

- **价格数据**：Binance API
- **技术指标**：EMA、RSI、MACD
- **恐惧贪婪指数**：Alternative.me API
- **交易量统计**：现货和期货市场数据

## 🔄 版本更新

### V0.1.1 更新内容
- ✅ 新增半球时间播报系统
- ✅ 东半球（12:00 UTC+8）和西半球（00:00 UTC+8）时段统计
- ✅ BTC、ETH合约交易量和波动率分析
- ✅ 替换原有08:00播报机制
- ✅ 修复相对强弱分析逻辑

### V0.1.0 基础功能
- 每小时技术分析播报
- 企业微信推送
- HTML静态页面生成
- GitHub Actions自动化

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！