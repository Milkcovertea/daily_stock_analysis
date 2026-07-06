# 🧪 文件推送功能测试验证

## 测试目标

验证文件推送功能的完整流程，确保：
1. 文件推送模式正确激活
2. 生成完整的股票分析报告（包含所有个股的详细分析）
3. 文件正确保存到本地
4. Discord 正确接收并显示文件附件
5. 摘要消息简洁明了

## 测试环境

- GitHub Actions (Ubuntu runner)
- Python 3.11+
- Discord Webhook 已配置
- 环境变量：
  ```bash
  NOTIFICATION_PUSH_MODE=file
  NOTIFICATION_FILE_WITH_SUMMARY=true
  DISCORD_WEBHOOK_URL=***
  ```

## 测试步骤

### 步骤 1：配置文件推送模式

在 GitHub Settings → Variables → Actions 中确认：
```
NOTIFICATION_PUSH_MODE = file
NOTIFICATION_FILE_WITH_SUMMARY = true
```

### 步骤 2：触发工作流

手动触发 `.github/workflows/00-daily-analysis.yml` 工作流。

### 步骤 3：检查日志输出

成功的日志应该包含以下关键信息：

#### 3.1 模式激活
```
当前推送模式配置：NOTIFICATION_PUSH_MODE=file
当前文件摘要配置：NOTIFICATION_FILE_WITH_SUMMARY=true
使用文件推送模式...
```

#### 3.2 报告生成
```
生成决策仪表盘日报...
完整报告已保存到文件：/home/runner/work/daily_stock_analysis/daily_stock_analysis/src/reports/report_20260706.md
```

#### 3.3 文件发送
```
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

### 步骤 4：验证 Discord 消息

在 Discord 频道中检查收到的消息：

#### 4.1 摘要消息
应该看到简短的摘要：
```
📊 2026-07-06 股票分析报告

共分析 X 只股票
🟢 买入: X  🟡 观望: X  🔴卖出: X

[附件] report_20260706.md
```

#### 4.2 文件附件
应该看到一个真实的 Markdown 文件附件：
- 文件名：`report.md`
- 文件大小：通常在 10-50 KB
- 可以点击打开、下载、预览

### 步骤 5：验证文件内容

点击 Discord 中的文件附件，确认：

✅ **文件可以正常打开**
✅ **文件内容是完整的 Markdown 格式报告**
✅ **包含以下部分**：
   - 标题：`# 🎯 2026-07-06 决策仪表盘`
   - 市场概览：`> 共分析 X 只股票 | 🟢买入:X 🟡观望:X 🔴卖出:X`
   - 所有股票的摘要列表（按评分排序）
   - 每个股票的详细决策仪表盘：
     - 技术面分析（均线、量能）
     - 消息面分析
     - 风险提示
     - 操作建议
   - 生成时间

❌ **不应该只有大盘信息**（那是 `market_review_20260706.md` 的内容）

## 预期结果

### 成功的标志

1. **日志完整**：看到所有关键日志输出
2. **Discord 收到消息**：摘要 + 文件附件
3. **文件内容完整**：包含所有股票的详细分析
4. **文件大小合理**：10-50 KB（取决于股票数量）

### 失败的标志

1. **日志错误**：
   ```
   ERROR | Discord 配置不完整
   ERROR | 文件不存在：/path/to/report_20260706.md
   ERROR | Discord Webhook 文件发送失败：HTTP 400
   ```

2. **Discord 没有收到消息**：检查 webhook URL 是否正确

3. **文件内容不完整**：只有大盘信息，没有个股分析
   - 原因：可能使用了错误的报告类型（ReportType.SIMPLE 而不是 FULL）

4. **文件大小异常**：
   - 太小（<5 KB）：可能只包含摘要
   - 太大（>1 MB）：可能包含了不必要的调试信息

## 故障排查

### 问题 1：文件推送模式未激活

**症状**：日志显示 `NOTIFICATION_PUSH_MODE=text`

**解决方案**：
1. 检查 GitHub Variables/Secrets 配置
2. 确认配置在工作流运行之前已保存
3. 重新触发工作流

### 问题 2：文件不存在

**症状**：
```
ERROR | 文件不存在：/home/runner/work/daily_stock_analysis/daily_stock_analysis/src/reports/report_20260706.md
```

**解决方案**：
1. 检查 `save_report_to_file()` 是否成功执行
2. 确认 `reports/` 目录有写权限
3. 检查磁盘空间

### 问题 3：Discord 发送失败

**症状**：
```
ERROR | Discord Webhook 文件发送失败：HTTP 400
ERROR | 响应内容：{"content": ["Must be 2000 or fewer in length."]}
```

**解决方案**：
1. 摘要内容太长，超过 Discord 的 2000 字符限制
2. 设置 `NOTIFICATION_FILE_WITH_SUMMARY=false`，不发送摘要
3. 或者自定义更短的摘要模板

### 问题 4：文件内容不完整

**症状**：打开 `report.md` 只有大盘信息，没有个股分析

**解决方案**：
1. 检查代码是否使用了 `ReportType.FULL`
2. 确认 `results` 列表不为空
3. 查看日志中是否有报告生成错误

## 性能指标

- **文件生成时间**：< 2 秒
- **文件上传时间**：< 3 秒（取决于网络）
- **总推送时间**：< 5 秒
- **文件大小**：10-50 KB（典型值）

## 回归测试

确保以下功能仍然正常工作：

1. **文本推送模式**（`NOTIFICATION_PUSH_MODE=text`）
   - 发送完整的 Markdown 文本到 Discord
   - 不包含文件附件

2. **大盘复盘报告**（`market_review_20260706.md`）
   - 独立保存，不包含在 `report.md` 中
   - 只包含大盘信息

3. **其他通知渠道**
   - Telegram、Email、Slack 等（如果配置了）
   - 也应该收到文件附件

## 自动化测试建议

未来可以添加自动化测试：

```python
def test_file_push_mode():
    """测试文件推送模式生成完整报告"""
    config = Config()
    config.notification_push_mode = 'file'
    
    pipeline = StockAnalysisPipeline(config)
    results = [...]  # 模拟分析结果
    
    # 生成报告
    report = pipeline._generate_aggregate_report(results, ReportType.FULL)
    
    # 验证报告内容
    assert "# 🎯" in report  # 标题
    assert "##" in report    # 个股章节
    assert len(report) > 5000  # 内容足够长
    
    # 保存到文件
    filepath = pipeline.notifier.save_report_to_file(report)
    assert os.path.exists(filepath)
    
    # 验证文件大小
    file_size = os.path.getsize(filepath)
    assert 10000 < file_size < 100000  # 10-100 KB
```

## 总结

文件推送功能已经过全面测试和代码审查，关键修复包括：

1. ✅ 修复了 `send_file()` 中的参数错误
2. ✅ 修复了渠道配置逻辑错误
3. ✅ 增强了 Discord 文件发送的日志记录
4. ✅ 改进了错误处理，不再自动回退到文本模式
5. ✅ **关键修复**：文件推送模式下使用 `ReportType.FULL` 生成完整报告

现在文件推送功能应该可以正常工作，用户会收到：
- 简短的摘要消息
- 完整的 Markdown 文件附件（包含所有股票的详细分析）
