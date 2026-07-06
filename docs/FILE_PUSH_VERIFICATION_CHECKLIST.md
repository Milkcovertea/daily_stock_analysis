# 📎 文件推送功能验证清单

## 修复的问题总结

本次修复解决了以下关键问题：

### 1. 参数错误（致命）
**问题**：`send_file()` 方法调用 `get_notification_route_config(route_type, severity)` 时传递了 2 个参数，但该函数只接受 1 个参数。

**修复**：
```python
# 修复前
route_config = get_notification_route_config(route_type, severity)

# 修复后
route_config = get_notification_route_config(route_type)
```

**位置**：`src/notification.py` 第 2862 行

### 2. 渠道配置逻辑错误（致命）
**问题**：`send_file()` 方法错误地将 `route_config`（字典）传递给 `split_notification_route_channels()`，而该函数期望的是渠道列表。

**修复**：
```python
# 修复前
route_config = get_notification_route_config(route_type)
explicit_channels, use_all = split_notification_route_channels(route_config)

# 修复后
route_config = get_notification_route_config(route_type)
configured_channels = getattr(self._config, route_config["config_attr"], []) or []
valid_channels, invalid_channels = split_notification_route_channels(configured_channels)
```

**位置**：`src/notification.py` 第 2862-2873 行

### 3. 错误处理不完善
**问题**：Discord 文件发送失败时没有详细的错误日志。

**修复**：
- 添加了文件存在性检查
- 添加了文件大小记录
- 添加了详细的 HTTP 响应状态码和错误信息
- 添加了超时和连接错误的专门处理

**位置**：`src/notification_sender/discord_sender.py` 第 292-400 行

### 4. 回退逻辑问题
**问题**：文件推送失败后会回退到文本模式，导致用户困惑。

**修复**：
- 文件推送失败时不再自动回退到文本模式
- 直接记录错误并返回
- 提供明确的错误提示信息

**位置**：`src/core/pipeline.py` 第 3220-3227 行

## 验证步骤

### 步骤 1：配置检查

确保在 GitHub Settings → Variables → Actions 中配置了：

```
NOTIFICATION_PUSH_MODE = file
NOTIFICATION_FILE_WITH_SUMMARY = true  # 可选，默认为 true
```

### 步骤 2：运行测试

触发 GitHub Actions 工作流（可以手动运行），观察日志输出。

### 步骤 3：检查日志

成功的日志应该包含以下关键信息：

```
当前推送模式配置：NOTIFICATION_PUSH_MODE=file
当前文件摘要配置：NOTIFICATION_FILE_WITH_SUMMARY=true
使用文件推送模式...
报告已保存到文件：/home/runner/work/daily_stock_analysis/daily_stock_analysis/src/reports/report_20260706.md
生成文件推送摘要：📊 2026-07-06 股票分析报告...
开始调用 send_file() 发送文件...
Discord 配置检查通过
文件读取成功：/path/to/report_20260706.md, 大小：15234 bytes
使用 Discord Webhook 发送文件...
Discord Webhook URL: https://discord.com/api/webhooks/...（已隐藏）
文件大小：15234 bytes
摘要内容：📊 2026-07-06 股票分析报告...
准备发送文件：report.md, MIME type: text/markdown
Discord Webhook 响应状态码：200
Discord Webhook 文件发送成功：report.md
决策仪表盘文件推送成功
```

### 步骤 4：检查 Discord 消息

在 Discord 频道中，你应该看到：

1. **简短的摘要消息**（如果 `NOTIFICATION_FILE_WITH_SUMMARY=true`）：
   ```
   📊 2026-07-06 股票分析报告
   
   共分析 X 只股票
   🟢 买入: X  🟡 观望: X  🔴卖出: X
   
   [附件] report_20260706.md
   ```

2. **真实的 Markdown 文件附件**：
   - 文件名：`report.md`
   - 文件大小：通常在 10-50 KB
   - 可以点击打开、下载、预览

### 步骤 5：验证文件内容

点击 Discord 中的文件附件，确认：

- ✅ 文件可以正常打开
- ✅ 文件内容是完整的 Markdown 格式报告
- ✅ 文件格式正确，可以在 Markdown 阅读器中查看

## 可能的错误及解决方案

### 错误 1：文件不存在

**日志**：
```
ERROR | 文件不存在：/home/runner/work/daily_stock_analysis/daily_stock_analysis/src/reports/report_20260706.md
```

**原因**：文件保存失败或路径错误。

**解决方案**：
- 检查 `save_report_to_file()` 方法是否正确执行
- 确认 `reports/` 目录是否有写权限
- 检查磁盘空间是否充足

### 错误 2：Discord 配置不完整

**日志**：
```
ERROR | Discord 配置不完整，跳过文件发送。请检查 DISCORD_WEBHOOK_URL 是否已配置。
```

**原因**：`DISCORD_WEBHOOK_URL` 环境变量未配置。

**解决方案**：
- 在 GitHub Secrets 中配置 `DISCORD_WEBHOOK_URL`
- 确认 webhook URL 格式正确（应该是 `https://discord.com/api/webhooks/...`）

### 错误 3：Discord Webhook 返回错误

**日志**：
```
ERROR | Discord Webhook 文件发送失败：HTTP 400
ERROR | 响应内容：{"content": ["Must be 2000 or fewer in length."]}
```

**原因**：摘要内容太长，超过了 Discord 的消息长度限制（2000 字符）。

**解决方案**：
- 缩短摘要内容
- 或者设置 `NOTIFICATION_FILE_WITH_SUMMARY=false`，不发送摘要

### 错误 4：网络连接问题

**日志**：
```
ERROR | Discord Webhook 连接错误：...
```

**原因**：GitHub Actions 环境无法访问 Discord API。

**解决方案**：
- 检查 GitHub Actions 的网络限制
- 确认 Discord API 是否可访问（`https://discord.com`）
- 考虑使用代理（如果必要）

### 错误 5：未知的通知渠道

**日志**：
```
WARNING | NOTIFICATION_REPORT_CHANNELS 包含未知通知渠道，将忽略：xxx
```

**原因**：配置文件中指定了不存在的渠道名称。

**解决方案**：
- 检查 `NOTIFICATION_REPORT_CHANNELS` 环境变量的值
- 确认渠道名称拼写正确（支持的渠道：wechat, dingtalk, feishu, telegram, email, pushover, ntfy, gotify, pushplus, serverchan3, custom, discord, slack, astrbot）

## 支持的渠道

以下渠道完全支持文件推送：

- ✅ Telegram（使用 `sendDocument` API）
- ✅ Discord（使用 Webhook 或 Bot API）
- ✅ Email（使用 MIME 附件）
- ✅ Slack（使用 Files API）

以下渠道不支持文件推送：

- ❌ 企业微信（WeChat Work）- 平台限制
- ❌ 飞书（Lark）- 平台限制
- ❌ PushPlus - 平台限制
- ❌ Server酱 - 平台限制
- ❌ 其他推送平台 - 平台限制

## 回滚方案

如果文件推送模式出现问题，可以快速回退到文本模式：

1. 在 GitHub Settings → Variables → Actions 中修改：
   ```
   NOTIFICATION_PUSH_MODE = text
   ```

2. 或者删除 `NOTIFICATION_PUSH_MODE` 变量（会使用默认值 `text`）

3. 重新运行工作流

## 性能影响

文件推送对性能的影响：

- **文件大小**：通常 10-50 KB，对网络传输影响很小
- **发送时间**：增加约 1-2 秒（文件读取 + 上传）
- **内存使用**：增加约 50-100 KB（文件内容缓存）

总体来说，性能影响可以忽略不计。

## 安全性

文件推送的安全性考虑：

- **文件内容**：只包含股票分析报告，不包含敏感信息
- **传输加密**：使用 HTTPS 传输（Discord Webhook API）
- **文件权限**：GitHub Actions 运行环境是隔离的，文件不会被其他用户访问
- **Discord 权限**：确保 webhook 只有发送消息的权限，没有其他权限

## 监控和维护

建议定期检查：

1. **Discord 消息**：确认文件是否正常发送
2. **GitHub Actions 日志**：查看是否有错误
3. **文件大小**：如果文件过大（>10 MB），可能需要优化报告内容
4. **用户反馈**：收集用户对文件推送的体验反馈

## 常见问题解答

### Q: 为什么我配置了 `NOTIFICATION_PUSH_MODE=file`，但还是收到文本消息？

A: 可能的原因：
1. 配置没有保存成功 - 检查 GitHub Variables/Secrets
2. 配置是在工作流运行之后添加的 - 需要重新触发工作流
3. Discord 文件发送失败 - 查看日志中的错误信息
4. 使用了不支持文件推送的渠道 - 检查渠道配置

### Q: 文件推送和文本推送可以同时使用吗？

A: 不可以。`NOTIFICATION_PUSH_MODE` 只能是 `text` 或 `file` 之一。但你可以配置多个通知渠道，让它们都接收文件或文本。

### Q: 文件大小有限制吗？

A: Discord 的文件大小限制是 25 MB（免费用户），股票分析报告通常只有 10-50 KB，远低于限制。

### Q: 文件会保存多久？

A: 
- **本地保存**：文件会保存在 `reports/` 目录下，直到被手动删除或 GitHub Actions 清理
- **Discord 保存**：Discord 会永久保存文件，除非手动删除

### Q: 可以自定义文件名吗？

A: 可以。修改 `save_report_to_file()` 方法中的 `filename` 参数，或者设置环境变量自定义文件名格式。

### Q: 文件推送会影响其他通知渠道吗？

A: 不会。每个渠道独立处理文件推送。如果某个渠道不支持文件推送，会记录错误并跳过，不影响其他渠道。
