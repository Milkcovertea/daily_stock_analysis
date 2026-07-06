# 📎 文件推送功能故障排查指南

## 问题现象

收到推送消息，显示"[附件] report_20260706.md"，但这只是文本，不是真正的可下载附件。

## 根本原因

这个问题通常是因为**没有配置文件推送模式**，系统使用的是默认的文本推送模式。

## 解决方案

### 1. 确认是否配置了文件推送模式

在 GitHub Actions 中，需要配置环境变量`NOTIFICATION_PUSH_MODE=file`才能启用文件推送。

#### 检查步骤：

1. 进入 GitHub 仓库
2. 点击 **Settings** → **Variables** → **Actions**
3. 检查是否有 `NOTIFICATION_PUSH_MODE` 变量
4. 如果没有，或者值是`text`，请添加或修改为`file`

#### 配置方法：

**方式一：通过 GitHub Variables（推荐）**

1. Settings → Variables → Actions → New variable
2. Name: `NOTIFICATION_PUSH_MODE`
3. Value: `file`
4. 点击 "Add variable"

**方式二：通过 GitHub Secrets**

1. Settings → Secrets and variables → Actions → New secret
2. Name: `NOTIFICATION_PUSH_MODE`
3. Value: `file`
4. 点击 "Add secret"

### 2. 验证配置是否生效

配置完成后，下一次 GitHub Actions 运行时，日志中应该能看到：

```
当前推送模式配置：NOTIFICATION_PUSH_MODE=file
当前文件摘要配置：NOTIFICATION_FILE_WITH_SUMMARY=true
使用文件推送模式...
报告已保存到文件：/path/to/reports/report_20260706.md
开始调用 send_file() 发送文件...
```

如果看到的是`NOTIFICATION_PUSH_MODE=text`，说明配置没有生效。

### 3. 检查文件是否真的被创建

在 GitHub Actions 日志中，应该能看到类似这样的输出：

```
报告已保存到文件：/home/runner/work/daily_stock_analysis/daily_stock_analysis/reports/report_20260706.md
```

如果看不到这行日志，说明文件推送模式没有被激活。

### 4. 检查文件发送是否成功

文件推送成功后，日志中应该能看到：

```
Telegram文件推送成功：/path/to/report_20260706.md
或
Discord文件推送成功：/path/to/report_20260706.md
或
Email文件推送成功：/path/to/report_20260706.md
```

如果看到"文件推送失败"的错误，可能的原因有：

- **通知渠道未配置文件推送**：某些渠道可能不支持文件推送
- **文件路径不正确**：检查文件是否真的被保存到了预期路径
- **网络连接问题**：GitHub Actions 环境无法访问通知渠道的 API

### 5. 可选配置

#### 5.1 关闭摘要消息

如果只想发送文件，不发送摘要消息：

```bash
NOTIFICATION_FILE_WITH_SUMMARY=false
```

#### 5.2 自定义摘要模板

可以使用 Jinja2 模板自定义摘要消息：

```bash
NOTIFICATION_FILE_SUMMARY_TEMPLATE="📊 {{date}} 股票分析报告已生成\n\n共分析 {{stock_count}} 只股票\n🟢买入: {{buy_count}} 🟡观望: {{hold_count}} 🔴卖出: {{sell_count}}"
```

## 预期效果

配置正确后，推送的消息应该是这样的：

### Telegram/Discord
```
📊 2026-07-06 股票分析报告

共分析 7 只股票
🟢 买入: 2  🟡 观望: 4  🔴 卖出: 1

[文件附件] report_20260706.md (15.2 KB)
```

用户可以点击文件附件下载和查看。

### Email
```
主题：📊 2026-07-06 股票分析报告

正文：
📊 2026-07-06 股票分析报告

共分析 7 只股票
🟢 买入: 2  🟡 观望: 4  🔴 卖出: 1

[附件] report_20260706.md
```

用户可以点击下载附件。

## 常见问题

### Q1: 为什么我配置了`NOTIFICATION_PUSH_MODE=file`，但还是收到文本消息？

A: 可能的原因：
1. 配置没有保存成功，检查 GitHub Variables/Secrets 是否正确添加
2. 配置是在工作流运行之后添加的，需要重新触发工作流
3. 工作流文件中没有正确引用环境变量

### Q2: 文件推送失败后会回退到文本模式吗？

A: **不会**。文件推送失败时，系统会记录错误并停止，不会自动回退到文本模式。这是为了避免混淆。

### Q3: 哪些通知渠道支持文件推送？

A: 目前支持文件推送的渠道：
- ✅ Telegram（使用 sendDocument API）
- ✅ Discord（使用文件上传 API）
- ✅ Email（使用 MIME 附件）
- ✅ Slack（使用 Files API）

不支持文件推送的渠道：
- ❌ 企业微信（平台限制）
- ❌ 飞书（平台限制）
- ❌ PushPlus/Server酱（平台限制）

这些渠道在文件推送模式下会发送简短摘要。

## 技术细节

### 文件保存路径

文件会被保存到项目根目录下的`reports/`文件夹：

```
reports/
  report_20260706.md
  report_20260707.md
  ...
```

### 文件命名规则

默认命名格式：`report_YYYYMMDD.md`

例如：
- `report_20260706.md`
- `report_20260707.md`

### 文件大小

通常报告文件大小在 10-50 KB 之间，远低于各平台限制：
- Telegram: 2 GB
- Discord: 25 MB (免费用户)
- Email: 通常 25 MB

## 回滚方法

如果文件推送模式出现问题，可以临时回退到文本模式：

```bash
NOTIFICATION_PUSH_MODE=text
```

或者直接在 GitHub Variables/Secrets 中删除`NOTIFICATION_PUSH_MODE`变量，系统会使用默认的`text`模式。
