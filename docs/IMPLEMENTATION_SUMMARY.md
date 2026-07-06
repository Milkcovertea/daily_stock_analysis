# 🎯 自动股票筛选功能实现总结

> 本文档总结了自动股票筛选功能的完整实现，包括设计思路、技术方案、配置方法和使用示例。

## 📋 需求回顾

用户需求：
1. ✅ **每个交易日自动筛选股票** - 不想每天手动更新股票列表
2. ✅ **筛选策略**：沪深主板、剔除创业板/科创板/ST、收盘价<50 元、成交额前 5 名
3. ✅ **测试阶段**：先确认首次筛选结果，成熟后自动执行
4. ✅ **基础股票池**：保留手动维护的实盘持仓股票
5. ✅ **Fallback 策略**：筛选失败时仅执行基础股票池

## 🏗️ 实现架构

### 整体流程

```
┌─────────────────────────────────────────────────────────────┐
│  GitHub Actions 定时触发（每个交易日 18:00）                 │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 1: 配置检查                                            │
│  - 读取 BASE_STOCK_LIST（基础股票池）                        │
│  - 读取 AUTO_SCREEN_ENABLED（是否启用自动筛选）              │
│  - 读取 SCREENER_MAX_PRICE / SCREENER_TOP_N（筛选参数）      │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 2: 执行股票筛选器（如果启用）                          │
│  - 获取全部 A 股行情数据                                     │
│  - 应用筛选策略：                                            │
│    * 剔除创业板（300xxx）和科创板（688xxx）                  │
│    * 剔除 ST 股票                                            │
│    * 筛选收盘价 < 50 元的股票                                │
│    * 按成交额降序排列，取前 N 只                             │
│  - 合并基础股票池（去重）                                    │
│  - 输出筛选结果                                              │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 3: Fallback 检查                                       │
│  - 如果筛选失败或结果为空：                                  │
│    * 有基础池 → 使用基础池                                   │
│    * 无基础池 → 使用默认值 600519                            │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 4: 执行股票分析                                        │
│  - 使用最终股票列表（自动筛选 + 基础池）                     │
│  - 生成决策报告                                              │
│  - 推送到通知渠道                                            │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 技术实现

### 1. 股票筛选器增强 (`scripts/stock_screener.py`)

#### 新增功能

- ✅ **环境变量配置支持**
  - `SCREENER_MAX_PRICE`：最大收盘价（默认 50）
  - `SCREENER_TOP_N`：返回数量（默认 5）
  - `BASE_STOCK_LIST`：基础股票池
  - `SCREENER_VERBOSE`：详细输出模式

- ✅ **基础股票池合并逻辑**
  - 优先添加自动筛选的股票
  - 补充基础池中未重复的股票
  - 去重并保持顺序

- ✅ **Fallback 机制**
  - 筛选失败 → 使用基础池
  - 结果为空 → 使用基础池
  - 无基础池 → 使用默认值

- ✅ **增强输出**
  - 详细统计信息
  - 分离显示自动筛选和基础池股票
  - 输出 `STOCK_LIST_OUTPUT` 供 Actions 捕获

#### 关键代码片段

```python
class StockScreener:
    def __init__(
        self,
        max_price: float = 50.0,
        top_n: int = 5,
        base_stock_list: Optional[List[str]] = None,
        verbose: bool = True
    ):
        """支持基础池和配置化的初始化"""
        self.max_price = max_price
        self.top_n = top_n
        self.base_stock_list = base_stock_list or []
        self.verbose = verbose

    def _merge_with_base_pool(self, auto_stocks: List[Dict]) -> List[Dict]:
        """合并自动筛选结果和基础池（去重）"""
        seen_codes = set()
        merged = []
        
        # 优先添加自动筛选的股票
        for stock in auto_stocks:
            code = stock['code']
            if code not in seen_codes:
                merged.append(stock)
                seen_codes.add(code)
        
        # 添加基础池中未重复的股票
        for code in self.base_stock_list:
            if code not in seen_codes:
                merged.append({
                    'code': code,
                    'name': f'BASE-{code}',
                    'close': 0.0,
                    'amount': 0.0,
                    'pct_chg': 0.0,
                    'source': 'base_pool'
                })
                seen_codes.add(code)
        
        return merged

    def _build_base_stock_fallback(self) -> List[Dict]:
        """构建基础股票池 fallback 结果"""
        if not self.base_stock_list:
            return []
        
        return [
            {
                'code': code,
                'name': f'BASE-{code}',
                'close': 0.0,
                'amount': 0.0,
                'pct_chg': 0.0,
                'source': 'base_pool_fallback'
            }
            for code in self.base_stock_list
        ]
```

### 2. GitHub Actions 工作流集成 (`.github/workflows/00-daily-analysis.yml`)

#### 新增配置变量

```yaml
# 自动筛选配置
BASE_STOCK_LIST: ${{ vars.BASE_STOCK_LIST || secrets.BASE_STOCK_LIST }}
SCREENER_MAX_PRICE: ${{ vars.SCREENER_MAX_PRICE || secrets.SCREENER_MAX_PRICE || '50' }}
SCREENER_TOP_N: ${{ vars.SCREENER_TOP_N || secrets.SCREENER_TOP_N || '5' }}
AUTO_SCREEN_ENABLED: ${{ vars.AUTO_SCREEN_ENABLED || secrets.AUTO_SCREEN_ENABLED || 'false' }}
```

#### 执行逻辑

```bash
# 判断是否启用自动筛选
if [ "${AUTO_SCREEN_ENABLED:-false}" = "true" ]; then
  # 运行筛选器
  SCREEN_OUTPUT=$(python3 scripts/stock_screener.py \
    --max-price "${SCREENER_MAX_PRICE:-50}" \
    --top-n "${SCREENER_TOP_N:-5}" \
    --dry-run 2>&1)
  
  # 捕获输出
  STOCK_LIST_OUTPUT=$(echo "$SCREEN_OUTPUT" | grep "STOCK_LIST_OUTPUT=" | cut -d'=' -f2)
  
  if [ -n "$STOCK_LIST_OUTPUT" ]; then
    # 更新 STOCK_LIST 为筛选结果
    export STOCK_LIST="$STOCK_LIST_OUTPUT"
  else
    # Fallback
    if [ -n "${BASE_STOCK_LIST:-}" ]; then
      export STOCK_LIST="$BASE_STOCK_LIST"
    else
      export STOCK_LIST="600519"
    fi
  fi
fi
```

### 3. 文档更新

#### 新增文档

- ✅ `docs/AUTO_SCREEN_GUIDE.md` - 快速入门指南
- ✅ `docs/IMPLEMENTATION_SUMMARY.md` - 实现总结（本文档）

#### 更新文档

- ✅ `docs/full-guide.md` - 在"其他配置"部分添加自动筛选配置说明
  - 新增环境变量说明
  - 详细配置示例
  - 运行逻辑图解
  - Fallback 策略说明
  - 测试验证方法

## 📊 配置示例

### 最小配置（快速开始）

```yaml
# GitHub Actions Secrets
BASE_STOCK_LIST: "600519,000001"  # 你的实盘持仓

# GitHub Actions Variables
AUTO_SCREEN_ENABLED: "true"
```

**效果**：每天自动筛选 5 只股票 + 2 只基础池股票 = 7 只股票

### 完整配置（推荐）

```yaml
# GitHub Actions Secrets
BASE_STOCK_LIST: "600519,000001,300750"  # 实盘持仓

# GitHub Actions Variables
AUTO_SCREEN_ENABLED: "true"
SCREENER_MAX_PRICE: "50"  # 最大收盘价
SCREENER_TOP_N: "5"       # 筛选数量
```

**效果**：5 只自动筛选 + 3 只基础池（去重）= 最多 8 只股票

### 保守配置（测试阶段）

```yaml
# GitHub Actions Secrets
BASE_STOCK_LIST: "600519,000001"

# GitHub Actions Variables
AUTO_SCREEN_ENABLED: "false"  # 先不启用
STOCK_LIST: "600519,000001"   # 使用手动配置
```

**效果**：仅分析基础池的 2 只股票，观察系统运行

### 激进配置（成熟阶段）

```yaml
# GitHub Actions Secrets
# 不配置基础池

# GitHub Actions Variables
AUTO_SCREEN_ENABLED: "true"
SCREENER_MAX_PRICE: "50"
SCREENER_TOP_N: "10"  # 多筛选一些
```

**效果**：完全依赖自动筛选，每天 10 只新股票

## 🧪 测试验证

### 本地测试命令

```bash
# 1. 基础测试（dry-run）
python3 scripts/stock_screener.py --dry-run

# 2. 带基础池测试
BASE_STOCK_LIST="600519,000001" python3 scripts/stock_screener.py --dry-run

# 3. 自定义参数测试
python3 scripts/stock_screener.py --max-price 30 --top-n 10 --dry-run

# 4. 查看详细输出
python3 scripts/stock_screener.py --dry-run 2>&1 | grep -A 50 "股票筛选结果"
```

### GitHub Actions 测试

1. **手动触发测试**
   - 进入 Actions → 每日股票分析 → Run workflow
   - 选择模式（full / stocks-only / market-only）
   - 勾选"强制运行"
   - 点击 Run workflow

2. **查看筛选日志**
   ```
   🔍 执行股票筛选...
   ========================================
   📦 基础股票池已配置：600519,000001
   🔍 自动筛选已启用，准备执行股票筛选...
   
   🎯 股票筛选结果
   ...
   
   ✅ 股票筛选成功！
   📊 筛选结果：600123,000456,...
   ```

3. **验证最终股票列表**
   ```
   🚀 开始执行股票分析...
   ==========================================
   📊 最终使用的股票列表：600123,000456,600789,000234,600567,600519,000001
   ```

## 📈 运行效果

### 典型输出

```
========================================
🔍 执行股票筛选...
========================================
📦 基础股票池已配置：600519,000001
🔍 自动筛选已启用，准备执行股票筛选...

========================================
🎯 股票筛选结果
========================================
📅 筛选日期：2026-07-06 18:00:00
📊 筛选策略：沪深主板 + 非 ST + 收盘价<50 元 + 成交额前 5 名
----------------------------------------
📈 筛选过程统计：
  - 初始股票数量：5000只
  - 剔除创业板/科创板后：3000只
  - 剔除 ST 股票后：2800只
  - 收盘价<50 元后：1500只
  - 最终自动筛选（成交额前 5 名）：5只
----------------------------------------
📊 合并统计：
  - 自动筛选：5只
  - 基础股票池：2只
  - 合并后总计：7只
----------------------------------------
🏆 自动筛选股票详情：
  1. 某某股份 (600123)
     收盘价：¥25.50
     成交额：¥12.5亿
     涨跌幅：+2.35%
  
  2. 某某科技 (000456)
     收盘价：¥18.20
     成交额：¥9.8亿
     涨跌幅：-1.20%
  
  ... (共 5 只)
----------------------------------------
📦 基础股票池（未重复）：
  1. 600519
  2. 000001
----------------------------------------
💾 最终股票列表（逗号分隔）：600123,000456,600789,000234,600567,600519,000001
========================================

✅ 股票筛选成功！
📊 筛选结果：600123,000456,600789,000234,600567,600519,000001
📤 已更新 STOCK_LIST 为筛选结果
```

### Fallback 场景

```
⚠️ 股票筛选失败或结果为空
🔄 FALLBACK 到基础股票池：600519,000001
```

## ⚠️ 注意事项

### 数据源依赖

- **AkShare**：获取 A 股实时行情
- **网络要求**：GitHub Actions runner 需要能访问 AkShare 数据源
- **交易时间**：使用收盘价数据，应在收盘后执行（默认 18:00）

### 性能影响

- **筛选耗时**：约 5-10 秒
- **整体影响**：对总分析时间影响很小（通常分析需要几分钟）

### 维护成本

- **基础池**：需要手动更新（通过 GitHub Secrets）
- **筛选参数**：可根据市场情况调整
- **策略优化**：如需修改筛选逻辑，需编辑 `stock_screener.py`

## 🚀 未来扩展

### 短期计划

- [ ] 支持更多筛选条件（市值、PE、PB 等）
- [ ] 支持行业分布控制
- [ ] 支持地域分布控制
- [ ] 支持技术指标筛选

### 长期愿景

- [ ] 多策略并行（价值、成长、趋势等）
- [ ] 机器学习辅助筛选
- [ ] 自动调参优化
- [ ] 回测验证筛选效果

## 📚 相关资源

### 代码文件

- [`scripts/stock_screener.py`](../scripts/stock_screener.py) - 筛选器实现
- [`.github/workflows/00-daily-analysis.yml`](../.github/workflows/00-daily-analysis.yml) - 工作流配置

### 文档

- [`docs/AUTO_SCREEN_GUIDE.md`](AUTO_SCREEN_GUIDE.md) - 快速入门
- [`docs/full-guide.md`](full-guide.md#自动股票筛选配置) - 完整配置指南
- [`README.md`](../README.md) - 项目总览

### 外部资源

- [AkShare 文档](https://akshare.akfamily.xyz/) - A 股数据源
- [GitHub Actions 文档](https://docs.github.com/en/actions) - 工作流配置

## 💬 反馈与支持

遇到问题或有改进建议？

- 📝 提交 [Issue](https://github.com/ZhuLinsen/daily_stock_analysis/issues)
- 💬 参与 [讨论](https://github.com/ZhuLinsen/daily_stock_analysis/discussions)
- 📧 联系合作邮箱：zhuls345@gmail.com

---

**实现完成时间**: 2026-07-06  
**版本**: v1.0.0  
**维护者**: ZhuLinsen
