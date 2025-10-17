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
- **飞书推送**：支持Lark（飞书）机器人消息推送
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
# 仅企业微信推送
python3 scripts/market_broadcast_hourly.py --symbols BTCUSDT,ETHUSDT,BNBUSDT --webhook "YOUR_WECHAT_WEBHOOK_URL" --tone aggressive

# 仅飞书推送
python3 scripts/market_broadcast_hourly.py --symbols BTCUSDT,ETHUSDT,BNBUSDT --lark-webhook "YOUR_LARK_WEBHOOK_URL" --tone aggressive

# 同时推送到企业微信和飞书
python3 scripts/market_broadcast_hourly.py --symbols BTCUSDT,ETHUSDT,BNBUSDT --webhook "YOUR_WECHAT_WEBHOOK_URL" --lark-webhook "YOUR_LARK_WEBHOOK_URL" --tone aggressive
```

#### 生成HTML页面
```bash
python3 scripts/market_broadcast_hourly.py --symbols BTCUSDT,ETHUSDT,BNBUSDT --html_out /path/to/output/directory --tone aggressive
```

### GitHub Actions 自动化

#### 配置步骤
1. Fork此仓库到你的GitHub账户
2. 在仓库设置中添加Secrets：
   - `WECHAT_WEBHOOK_URL`：企业微信机器人Webhook地址（可选）
   - `LARK_WEBHOOK_URL`：飞书机器人Webhook地址（可选）
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

### 飞书推送
1. 在飞书群聊中添加自定义机器人
2. 获取Webhook URL（格式：`https://open.feishu.cn/open-apis/bot/v2/hook/xxx`）
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
- `--lark-webhook`：飞书Webhook URL
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

## 🔧 飞书机器人配置详细说明

### 1. 创建飞书自定义机器人
1. 在飞书群聊中，点击右上角设置按钮
2. 选择"群机器人" → "添加机器人" → "自定义机器人"
3. 设置机器人名称和描述（如：交易数据播报机器人）
4. 配置安全设置（推荐使用关键词验证，设置关键词如"交易"、"播报"等）
5. 复制生成的Webhook URL

### 2. Webhook URL格式
```
https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### 3. 消息格式支持
- 支持富文本格式（类似Markdown）
- 自动转换**粗体**文本
- 保持原有的技术分析格式和结构

### 4. 安全配置建议
- **关键词验证**：设置"交易"、"播报"、"BTC"等关键词
- **IP白名单**：如果使用GitHub Actions，可配置GitHub的IP段
- **签名验证**：高安全要求场景下可启用

## 🔄 版本更新

### V0.1.1 更新内容
- ✅ 新增半球时间播报系统
- ✅ 东半球（12:00 UTC+8）和西半球（00:00 UTC+8）时段统计
- ✅ BTC、ETH合约交易量和波动率分析
- ✅ 替换原有08:00播报机制
- ✅ 修复相对强弱分析逻辑
- ✅ 新增飞书（Lark）消息推送支持

### V0.1.0 基础功能
- 每小时技术分析播报
- 企业微信推送
- HTML静态页面生成
- GitHub Actions自动化

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！# trading-data-broadcast-bot
