# 📎 Markdown文件推送功能

> 将分析报告以文件形式推送，而不是长文本消息

---

## 🎯 功能说明

传统推送方式是将完整的Markdown报告作为文本消息发送到通知渠道，但这有几个问题：

1. **消息过长**：Telegram/Discord等平台有消息长度限制
2. **阅读体验差**：长消息在手机上很难阅读
3. **无法保存**：消息容易被淹没，不方便后续查阅
4. **格式丢失**：某些平台会破坏Markdown格式

**文件推送**解决了这些问题：
- ✅ 推送一个`.md`文件，保持完整格式
- ✅ 用户可以下载、保存、分享
- ✅ 不受消息长度限制
- ✅ 更好的阅读体验（可以在专门的Markdown阅读器中打开）

---

## ⚙️ 配置方式

### 环境变量

在`.env`文件或GitHub Secrets/Variables中添加：

```bash
# 推送模式：text（文本）或 file（文件）
# 默认：text（保持向后兼容）
NOTIFICATION_PUSH_MODE=file

# 文件推送时是否同时发送简短摘要（可选）
# 默认：true（发送"今日报告已生成" + 文件）
NOTIFICATION_FILE_WITH_SUMMARY=true

# 自定义摘要消息（可选，支持Jinja2模板）
NOTIFICATION_FILE_SUMMARY_TEMPLATE="📊 {{date}} 股票分析报告已生成\n\n共分析 {{stock_count}} 只股票\n🟢买入: {{buy_count}} 🟡观望: {{hold_count}} 🔴卖出: {{sell_count}}"
```

### GitHub Actions配置

在`.github/workflows/00-daily-analysis.yml`中添加：

```yaml
env:
  NOTIFICATION_PUSH_MODE: ${{ vars.NOTIFICATION_PUSH_MODE || 'file' }}
  NOTIFICATION_FILE_WITH_SUMMARY: ${{ vars.NOTIFICATION_FILE_WITH_SUMMARY || 'true' }}
```

---

## 📊 推送效果对比

### 传统文本推送

```
🎯 2026-07-06 决策仪表盘
共分析7只股票 | 🟢买入:2 🟡观望:4 🔴卖出:1

📊 分析结果摘要
⚪ 紫金矿业(601899): 观望 | 评分 68 | 看多
⚪ 金山办公(600396): 买入 | 评分 78 | 看多
...

📢 最新动态: 【最新消息】...
🚨 风险警报: 风险点1：...
✨ 利好催化: 利好1：...

---（几百行内容）---

生成时间: 18:00
```

**问题**：
- ❌ 消息太长，被截断
- ❌ 在手机上难以阅读
- ❌ 无法方便保存

---

### 文件推送（新模式）

**推送消息**：
```
📊 2026-07-06 股票分析报告

共分析 7 只股票
🟢 买入: 2  🟡 观望: 4  🔴 卖出: 1

[附件] report_20260706.md (15.2 KB)
```

**附件文件内容**（完整Markdown报告）：
```markdown
# 🎯 2026-07-06 决策仪表盘

共分析7只股票 | 🟢买入:2 🟡观望:4 🔴卖出:1

## 📊 分析结果摘要

| 股票 | 代码 | 操作 | 评分 | 趋势 |
|------|------|------|------|------|
| 紫金矿业 | 601899 | 观望 | 68 | 看多 |
| 金山办公 | 600396 | 买入 | 78 | 看多 |
...

## 📈 个股详细分析

### 紫金矿业 (601899)

#### 📰 重要信息速览
...

#### 🚨 风险警报
...

#### ✨ 利好催化
...

#### 📢 最新动态
...

---

生成时间：2026-07-06 18:00
```

**优势**：
- ✅ 消息简短清晰
- ✅ 文件可下载保存
- ✅ 完整格式保留
- ✅ 方便分享和归档

---

## 🚀 实现细节

### 1. 文件生成

每次分析完成后，系统会自动生成Markdown文件：

```python
# 文件名格式：report_YYYYMMDD.md
filepath = notifier.save_report_to_file(
    content=full_report,
    filename=f"report_{date_str}.md"
)
```

### 2. 文件推送

根据配置选择推送模式：

```python
if config.notification_push_mode == "file":
    # 文件推送模式
    success = notifier.send_file(
        filepath=filepath,
        caption=summary_message,  # 可选的简短摘要
        route_type="report"
    )
else:
    # 传统文本推送
    success = notifier.send(
        content=full_report,
        route_type="report"
    )
```

### 3. 各渠道支持

| 渠道 | 文件推送支持 | 说明 |
|------|------------|------|
| **Telegram** | ✅ | 原生支持文件上传 |
| **Discord** | ✅ | 原生支持文件上传 |
| **Email** | ✅ | 作为附件发送 |
| **Slack** | ✅ | 原生支持文件上传 |
| **企业微信** | ⚠️ | 需要转换为图片（待实现） |
| **飞书** | ⚠️ | 需要转换为云文档（待实现） |
| **PushPlus** | ❌ | 仅支持文本 |
| **Server酱** | ❌ | 仅支持文本 |

---

## 💡 使用建议

### 推荐配置

**Telegram/Discord用户**：
```bash
NOTIFICATION_PUSH_MODE=file
NOTIFICATION_FILE_WITH_SUMMARY=true
```

**Email用户**：
```bash
NOTIFICATION_PUSH_MODE=file  # 作为附件发送
```

**企业微信/飞书用户**：
```bash
NOTIFICATION_PUSH_MODE=text  # 暂时保持文本模式
# 或等待后续的图片/云文档转换功能
```

**多渠道用户**：
```bash
# 系统会自动为每个渠道选择最佳方式
# Telegram/Discord → 文件
# Email → 附件
# 企业微信 → 文本（fallback）
NOTIFICATION_PUSH_MODE=file
```

---

## 🔧 高级用法

### 自定义摘要模板

使用Jinja2模板自定义摘要消息：

```bash
NOTIFICATION_FILE_SUMMARY_TEMPLATE="""
📊 {{date}} 股票分析报告

📈 市场概况
- 分析股票：{{stock_count}}只
- 买入信号：{{buy_count}}只
- 观望信号：{{hold_count}}只
- 卖出信号：{{sell_count}}只

🏆 评分最高：{{top_stock_name}}({{top_stock_code}}) - {{top_score}}分

📎 完整报告请查看附件
"""
```

### 条件推送

根据报告内容决定是否推送文件：

```python
# 只在有买入信号时推送
if any(r.operation_advice == "买入" for r in results):
    notifier.send_file(filepath, caption="🚨 发现买入机会！")
```

---

## 📁 文件管理

### 本地存储

文件默认保存在`reports/`目录：

```
daily_stock_analysis/
├── reports/
│   ├── report_20260706.md
│   ├── report_20260707.md
│   └── ...
```

### 自动清理

可以配置自动清理旧文件（防止磁盘占用）：

```bash
# 保留最近30天的报告
REPORT_RETENTION_DAYS=30
```

### 云端同步

可以将`reports/`目录同步到云端：

- **GitHub Actions**: 自动上传为Artifacts
- **Docker**: 挂载到云存储
- **本地**: 使用rsync/syncthing同步

---

## ⚠️ 注意事项

### 文件大小

- Telegram: 最大50MB（通常报告<100KB，完全没问题）
- Discord: 最大25MB（免费用户8MB）
- Email: 取决于服务商（通常10-25MB）

### 文件格式

- 当前仅支持Markdown（`.md`）
- 未来可能支持PDF、HTML等格式

### 兼容性

- 旧版本客户端可能不支持文件下载
- 某些渠道（如PushPlus）不支持文件推送

---

## 🎯 未来扩展

### 计划功能

1. **PDF导出**：将Markdown转换为PDF推送
2. **图片推送**：将报告转为长图（适合企业微信/飞书）
3. **云文档集成**：直接创建飞书云文档/腾讯文档
4. **多文件推送**：分别推送摘要和详细报告
5. **定时打包**：每周/月打包所有报告为一个文件

### 实验性功能

```bash
# 启用PDF导出（需要安装wkhtmltopdf）
REPORT_PDF_ENABLED=true

# 启用图片转换（需要安装markdown-to-file）
MARKDOWN_TO_IMAGE_CHANNELS=telegram,wechat
```

---

## 💬 反馈与建议

遇到问题或有改进建议？

- 📝 提交 [Issue](https://github.com/ZhuLinsen/daily_stock_analysis/issues)
- 💬 参与 [讨论](https://github.com/ZhuLinsen/daily_stock_analysis/discussions)

---

**最后更新**: 2026-07-06  
**状态**: 🚧 开发中
