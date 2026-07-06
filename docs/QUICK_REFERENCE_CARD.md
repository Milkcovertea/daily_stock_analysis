# 📌 自动股票筛选 - 快速参考卡片

> 一页纸总结所有关键信息

---

## ⚡ 3步配置（5分钟）

### 1️⃣ 配置基础股票池（Secrets）

```
Settings → Secrets and variables → Actions → Repository secrets
New repository secret:
  Name:  BASE_STOCK_LIST
  Value: 600519,000001  # 你的实盘持仓
```

### 2️⃣ 启用自动筛选（Variables）

```
Repository variables:
  Name:  AUTO_SCREEN_ENABLED
  Value: true
```

### 3️⃣ 调整参数（可选）

```
SCREENER_MAX_PRICE: 50  # 最大收盘价（元）
SCREENER_TOP_N: 5       # 筛选数量（只）
```

---

## 🎯 筛选策略

| 条件 | 说明 |
|------|------|
| **市场** | 沪深主板（剔除创业板300xxx、科创板688xxx） |
| **风险** | 剔除所有ST股票 |
| **价格** | 收盘价 < 50元（可配置） |
| **排序** | 按成交额降序排列 |
| **数量** | 前5只（可配置） |
| **合并** | 与基础池智能合并（去重） |
| **Fallback** | 筛选失败 → 使用基础池 |

---

## 🔄 运行流程

```
每个交易日 18:00
    ↓
获取A股行情数据
    ↓
应用筛选策略
    ↓
合并基础股票池
    ↓
Fallback检查
    ↓
执行AI分析
    ↓
生成决策报告
    ↓
推送到通知渠道
```

---

## 📊 配置模式

| 模式 | BASE_STOCK_LIST | AUTO_SCREEN_ENABLED | 效果 |
|------|----------------|---------------------|------|
| **混合**（推荐） | `600519,000001` | `true` | 5只自动 + 基础池 |
| **完全自动** | 不配置 | `true` | 每天5只新股票 |
| **仅基础池** | `600519,000001` | `false` | 仅分析基础池 |
| **传统手动** | 不配置 | `false` | 使用STOCK_LIST |

---

## 🧪 测试验证

### 手动触发

```
Actions → 每日股票分析 → Run workflow
Mode: full
☑ Force run（强制运行）
→ Run workflow
```

### 查看日志

搜索关键词：`股票筛选`

**期望输出**：
```
📦 基础股票池已配置：600519,000001
🔍 自动筛选已启用...
🎯 股票筛选结果
...
✅ 股票筛选成功！
📊 筛选结果：xxxxx,xxxxx,...
```

### 验证结果

搜索：`最终使用的股票列表`

**应该看到**：自动筛选 + 基础池的合并结果

---

## ⚠️ 常见问题

### Q: 筛选器未执行？
**A**: 检查 `AUTO_SCREEN_ENABLED` 是否为 `true`

### Q: 筛选失败？
**A**: 网络问题，通常会自动fallback到基础池

### Q: 基础池股票未出现？
**A**: 与自动筛选重复（正常去重）

### Q: 筛选结果为空？
**A**: 放宽价格限制（提高 `SCREENER_MAX_PRICE`）

---

## 🔧 参数调整

### 价格范围

```yaml
# 更严格
SCREENER_MAX_PRICE: "30"

# 更宽松
SCREENER_MAX_PRICE: "80"
```

### 筛选数量

```yaml
# 更少
SCREENER_TOP_N: "3"

# 更多
SCREENER_TOP_N: "10"
```

### 基础池

```yaml
# 更新实盘持仓
BASE_STOCK_LIST: "600519,000001,300750"
```

---

## 📁 输出文件

### JSON报告（`config/stocks.json`）

```json
{
  "screen_date": "2026-07-06",
  "strategy": {
    "description": "沪深主板 + 非 ST + 收盘价<50元 + 成交额前5名"
  },
  "auto_screened": [...],
  "base_pool": [...],
  "stocks": [...],  // 合并后
  "stock_codes": ["600123", "..."]
}
```

### 纯文本列表（`config/stocks.txt`）

```
600123,000456,600789,000234,600567,600519,000001
```

---

## 📚 完整文档

- 📖 [5分钟配置清单](QUICK_START_AUTO_SCREEN.md)
- 📖 [详细使用指南](AUTO_SCREEN_GUIDE.md)
- 📖 [实现总结](IMPLEMENTATION_SUMMARY.md)
- 📖 [下一步计划](NEXT_STEPS_PLAN.md)

---

## 💬 获取帮助

- 📝 查看 [故障排查](NEXT_STEPS_PLAN.md#故障排查指南)
- 📝 提交 [Issue](https://github.com/ZhuLinsen/daily_stock_analysis/issues)
- 📧 邮箱：zhuls345@gmail.com

---

**最后更新**: 2026-07-06  
**状态**: ✅ 已部署，等待配置
