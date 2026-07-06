# 📎 文件推送支持的通知渠道

## ✅ 完全支持的渠道

以下渠道**完全支持**文件推送模式，可以发送真实的 Markdown 文件附件：

### 1. Telegram
- **实现方式**：使用 Telegram Bot API 的 `sendDocument` 方法
- **文件格式**：`.md` 文件
- **文件大小限制**：2 GB（对股票分析报告来说完全够用）
- **用户体验**：用户可以点击文件预览、下载、分享
- **配置要求**：
  ```bash
  TELEGRAM_BOT_TOKEN=your_bot_token
  TELEGRAM_CHAT_ID=your_chat_id
  ```

### 2. Discord
- **实现方式**：使用 Discord Webhook 或 Bot API 的文件上传功能
- **文件格式**：`.md` 文件
- **文件大小限制**：25 MB（免费用户），500 MB（Nitro用户）
- **用户体验**：文件显示为可点击的附件，支持预览
- **配置要求**：
  ```bash
  DISCORD_WEBHOOK_URL=your_webhook_url
  # 或
  DISCORD_BOT_TOKEN=your_bot_token
  DISCORD_MAIN_CHANNEL_ID=your_channel_id
  ```

### 3. Email
- **实现方式**：使用 SMTP 的 MIME 附件功能
- **文件格式**：`.md` 文件
- **文件大小限制**：通常 25 MB（取决于邮件服务商）
- **用户体验**：作为邮件附件，可以下载、保存
- **配置要求**：
  ```bash
  EMAIL_SENDER=your_email@example.com
  EMAIL_PASSWORD=your_app_password
  EMAIL_RECEIVERS=receiver1@example.com,receiver2@example.com
  ```

### 4. Slack
- **实现方式**：使用 Slack Files API（files.getUploadURLExternal + files.completeUploadExternal）
- **文件格式**：`.md` 文件
- **文件大小限制**：根据 Slack 套餐而定
- **用户体验**：文件显示在消息中，支持预览和下载
- **配置要求**：
  ```bash
  SLACK_BOT_TOKEN=xoxb-your_bot_token
  SLACK_CHANNEL_ID=your_channel_id
  # 或
  SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
  ```

## ❌ 不支持的渠道

以下渠道**不支持**文件推送模式，原因是平台本身的限制：

### 1. 企业微信（WeChat Work）
- **限制原因**：企业微信 webhook API 只支持文本消息，不支持文件上传
- **回退行为**：发送简短摘要文本
- **错误提示**：`企业微信不支持文件推送模式，请切换到 Telegram/Discord/Email/Slack`
- **建议**：如果必须使用企业微信，请设置`NOTIFICATION_PUSH_MODE=text`

### 2. 飞书（Lark）
- **限制原因**：飞书 webhook API 只支持文本和富文本消息，不支持文件上传
- **回退行为**：发送简短摘要文本
- **错误提示**：`飞书不支持文件推送模式，请切换到 Telegram/Discord/Email/Slack`
- **建议**：如果必须使用飞书，请设置`NOTIFICATION_PUSH_MODE=text`

### 3. PushPlus
- **限制原因**：PushPlus API 只支持文本消息推送
- **回退行为**：发送完整报告文本（可能很长）
- **建议**：PushPlus 适合简短通知，不适合长报告

### 4. Server酱
- **限制原因**：Server酱 API 只支持文本和 Markdown 渲染，不支持文件
- **回退行为**：发送完整报告文本（会在微信中渲染为 Markdown）
- **建议**：Server酱的 Markdown 渲染效果较好，可以使用文本模式

### 5. Pushover
- **限制原因**：Pushover API 主要设计用于简短通知
- **回退行为**：发送简短摘要
- **建议**：Pushover 适合警报和简短通知

### 6. Ntfy
- **限制原因**：Ntfy 主要设计用于简短通知，虽然支持附件但实现复杂
- **回退行为**：发送简短摘要
- **建议**：Ntfy 适合系统监控和简短通知

### 7. Gotify
- **限制原因**：Gotify 主要设计用于简短通知
- **回退行为**：发送简短摘要
- **建议**：Gotify 适合自托管的简短通知

## 🤔 部分支持/需要进一步开发的渠道

### 1. 钉钉（DingTalk）
- **当前状态**：文本推送已实现，文件推送未实现
- **限制原因**：钉钉 webhook API 对文件上传支持有限
- **未来计划**：可能通过钉钉机器人 API 实现文件上传

### 2. 自定义 Webhook
- **当前状态**：取决于自定义 webhook 的实现
- **建议**：如果自定义 webhook 支持文件上传，可以实现相应的发送逻辑

## 📊 对比表格

| 渠道 | 文件推送支持 | 回退行为 | 推荐用于文件推送 |
|------|------------|---------|----------------|
| Telegram | ✅ 完全支持 | N/A | ⭐⭐⭐⭐⭐ |
| Discord | ✅ 完全支持 | N/A | ⭐⭐⭐⭐⭐ |
| Email | ✅ 完全支持 | N/A | ⭐⭐⭐⭐⭐ |
| Slack | ✅ 完全支持 | N/A | ⭐⭐⭐⭐⭐ |
| 企业微信 | ❌ 不支持 | 发送摘要文本 | ⭐ |
| 飞书 | ❌ 不支持 | 发送摘要文本 | ⭐ |
| PushPlus | ❌ 不支持 | 发送完整文本 | ⭐⭐ |
| Server酱 | ❌ 不支持 | 发送完整文本（Markdown渲染） | ⭐⭐⭐ |
| Pushover | ❌ 不支持 | 发送摘要 | ⭐⭐ |
| Ntfy | ❌ 不支持 | 发送摘要 | ⭐⭐ |
| Gotify | ❌ 不支持 | 发送摘要 | ⭐⭐ |
| 钉钉 | ⚠️ 未实现 | 发送文本 | ⭐⭐ |

## 🛠️ 如何解决不支持的问题

### 方案 1：切换到支持的渠道（推荐）

如果你希望使用文件推送模式，最佳方案是切换到支持的渠道：

**推荐组合**：
- **Telegram**：最方便，支持大文件，用户体验好
- **Discord**：适合团队使用，文件预览效果好
- **Email**：最正式，适合存档和分享

### 方案 2：使用文本模式

如果你必须使用不支持文件推送的渠道（如企业微信、飞书），可以切换回文本模式：

```bash
NOTIFICATION_PUSH_MODE=text
```

这样系统会发送完整的 Markdown 报告文本（可能会被截断）。

### 方案 3：混合模式（高级）

你可以配置多个通知渠道，其中一些用于文件推送，一些用于文本推送：

```bash
# 主要渠道：Telegram（文件推送）
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

# 备用渠道：企业微信（文本推送）
WECHAT_WEBHOOK_URL=...

# 使用文件推送模式
NOTIFICATION_PUSH_MODE=file
```

在这种情况下，Telegram 会收到文件附件，企业微信会收到简短摘要。

## 🔍 如何检查你的渠道是否支持

1. **查看配置**：检查你的环境变量，看看配置了哪些渠道
2. **查看日志**：运行后查看日志，如果有"不支持文件推送模式"的错误，说明该渠道不支持
3. **查看推送结果**：如果收到的是文本而不是文件附件，说明渠道不支持

## 📝 示例配置

### 示例 1：只使用 Telegram（推荐）

```bash
# Telegram 配置
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=-1001234567890

# 文件推送模式
NOTIFICATION_PUSH_MODE=file
NOTIFICATION_FILE_WITH_SUMMARY=true
```

**效果**：Telegram 会收到简短摘要 + Markdown 文件附件

### 示例 2：Telegram + Email

```bash
# Telegram 配置
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=-1001234567890

# Email 配置
EMAIL_SENDER=stock@example.com
EMAIL_PASSWORD=app_password
EMAIL_RECEIVERS=user1@example.com,user2@example.com

# 文件推送模式
NOTIFICATION_PUSH_MODE=file
```

**效果**：Telegram 和 Email 都会收到文件附件

### 示例 3：企业微信（文本模式）

```bash
# 企业微信配置
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

# 文本模式（因为企业微信不支持文件推送）
NOTIFICATION_PUSH_MODE=text
```

**效果**：企业微信会收到完整的 Markdown 报告文本

## ❓ 常见问题

### Q: 为什么我的渠道不支持文件推送？

A: 这通常是因为平台 API 的限制。例如，企业微信和飞书的 webhook API 只设计用于发送文本消息，不支持文件上传。要实现文件推送，需要使用平台的其他 API（如文件上传 API），这可能需要更复杂的认证和实现。

### Q: 我能自己实现不支持渠道的文件推送吗？

A: 可以，但需要：
1. 研究该渠道的文件上传 API
2. 在 `src/notification_sender/` 目录下实现相应的发送方法
3. 在 `src/notification.py` 的 `_send_file_to_channel` 方法中添加对该渠道的支持

### Q: 文件推送和文本推送哪个更好？

A: 这取决于你的使用场景：
- **文件推送**：适合完整报告、需要保存/分享/后续查阅的场景
- **文本推送**：适合快速浏览、使用不支持文件的渠道、或报告较短的场景

### Q: 我同时配置了支持的渠道和不支持的渠道，会怎样？

A: 系统会尝试向所有渠道发送文件。对于支持的渠道（如 Telegram），会发送文件附件；对于不支持的渠道（如企业微信），会记录错误并跳过，或者回退到发送摘要文本（取决于具体实现）。
