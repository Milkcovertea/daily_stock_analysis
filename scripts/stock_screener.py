#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票筛选器 - 每日自动筛选符合条件的股票

筛选策略（可通过环境变量配置）：
1. 沪深主板（剔除创业板 300xxx、科创板 688xxx）
2. 剔除 ST 股票
3. 前一天收盘价 < 50 元（可配置）
4. 按成交额降序排列
5. 取前 5 只股票（可配置）

支持基础股票池：
- 通过 BASE_STOCK_LIST 环境变量配置基础股票池（逗号分隔）
- 筛选结果会与基础池合并（去重）
- 筛选失败时 fallback 到基础池

使用方法：
    python3 scripts/stock_screener.py [--output config/stocks.json] [--dry-run]

环境变量：
    SCREENER_MAX_PRICE: 最大收盘价（默认 50）
    SCREENER_TOP_N: 返回股票数量（默认 5）
    BASE_STOCK_LIST: 基础股票池（逗号分隔，如 600519,000001）
    SCREENER_VERBOSE: 详细输出模式（默认 true）

输出格式：
    JSON 文件，包含筛选后的股票列表和筛选详情
    同时输出纯股票代码文本文件（逗号分隔）
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 导入数据源
from data_provider.akshare_fetcher import AkshareFetcher
from data_provider.base import is_st_stock, is_kc_cy_stock, normalize_stock_code


class StockScreener:
    """股票筛选器实现"""

    def __init__(
        self,
        max_price: float = 50.0,
        top_n: int = 5,
        base_stock_list: Optional[List[str]] = None,
        verbose: bool = True
    ):
        """
        初始化筛选器

        Args:
            max_price: 最大收盘价（元），默认 50 元
            top_n: 返回前 N 只股票，默认 5 只
            base_stock_list: 基础股票池列表，默认 None
            verbose: 是否输出详细信息，默认 True
        """
        self.max_price = max_price
        self.top_n = top_n
        self.base_stock_list = base_stock_list or []
        self.verbose = verbose
        self.fetcher = AkshareFetcher()

        if self.verbose:
            logger.info(f"股票筛选器初始化完成 - 最高价：{max_price}元，返回数量：{top_n}只")
            if self.base_stock_list:
                logger.info(f"基础股票池：{len(self.base_stock_list)}只股票 - {','.join(self.base_stock_list)}")

    def get_all_a_shares(self, max_retries: int = 3, retry_delay: int = 5) -> Optional[pd.DataFrame]:
        """
        获取全部 A 股列表（带重试机制）

        Args:
            max_retries: 最大重试次数，默认3次
            retry_delay: 重试间隔秒数，默认5秒

        Returns:
            包含所有 A 股基本信息的 DataFrame，失败返回 None
        """
        logger.info(f"正在获取全部 A 股列表...（最多重试{max_retries}次）")

        for attempt in range(1, max_retries + 1):
            try:
                # 使用 akshare 获取 A 股列表
                import akshare as ak

                # 获取 A 股实时行情数据（包含基本面信息）
                logger.info(f"第{attempt}次尝试获取数据...")
                df = ak.stock_zh_a_spot_em()

                if df is None or len(df) == 0:
                    logger.error(f"第{attempt}次尝试失败：返回数据为空")
                    if attempt < max_retries:
                        logger.info(f"等待{retry_delay}秒后重试...")
                        import time
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error("所有尝试均失败：返回数据为空")
                        return None

                logger.info(f"成功获取 {len(df)} 只 A 股实时行情数据（第{attempt}次尝试）")
                return df

            except Exception as e:
                logger.warning(f"第{attempt}次尝试失败：{type(e).__name__} - {e}")
                if attempt < max_retries:
                    logger.info(f"等待{retry_delay}秒后重试...")
                    import time
                    time.sleep(retry_delay)
                else:
                    logger.error(f"所有{max_retries}次尝试均失败：{type(e).__name__} - {e}")
                    logger.error("股票筛选失败，将触发Fallback机制")
                    return None

        return None

            # 标准化列名（akshare 返回的列名可能变化）
            # 确保有我们需要的字段：代码、名称、收盘价、成交额
            required_columns = {
                '代码': 'code',
                '名称': 'name',
                '最新价': 'close',
                '成交额': 'amount',
                '涨跌幅': 'pct_chg',
                '涨速': 'change_rate',
                '换手': 'turnover',
                '量比': 'volume_ratio',
                '振幅': 'amplitude',
                '总市值': 'market_cap',
                '市盈率-动态': 'pe_ratio'
            }

            # 重命名列
            for cn_name, en_name in required_columns.items():
                if cn_name in df.columns:
                    df[en_name] = df[cn_name]

            # 确保代码是字符串格式
            df['code'] = df['code'].astype(str).str.zfill(6)

            return df

        except Exception as e:
            logger.error(f"获取 A 股列表失败：{e}", exc_info=True)
            return None

    def filter_stocks(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """
        应用筛选条件

        Args:
            df: 包含 A 股实时行情的 DataFrame

        Returns:
            (筛选后的 DataFrame, 筛选统计信息)
        """
        stats = {
            'total': len(df),
            'after_main_board': 0,
            'after_no_st': 0,
            'after_price': 0,
            'final': 0
        }

        # 1. 筛选沪深主板（剔除创业板和科创板）
        logger.info(f"筛选前：{len(df)} 只股票")

        # 创业板代码：300xxx，科创板代码：688xxx
        def is_main_board(row):
            code = str(row.get('code', ''))
            # 剔除创业板和科创板
            if code.startswith('300') or code.startswith('688'):
                return False
            return True

        df_filtered = df[df.apply(is_main_board, axis=1)].copy()
        stats['after_main_board'] = len(df_filtered)
        logger.info(f"剔除创业板/科创板后：{len(df_filtered)} 只股票")

        # 2. 剔除 ST 股票
        def no_st(row):
            name = str(row.get('名称', row.get('name', '')))
            return not is_st_stock(name)

        df_filtered = df_filtered[df_filtered.apply(no_st, axis=1)].copy()
        stats['after_no_st'] = len(df_filtered)
        logger.info(f"剔除 ST 股票后：{len(df_filtered)} 只股票")

        # 3. 筛选收盘价 < 50 元的股票
        # 确保收盘价是数值类型
        df_filtered['close'] = pd.to_numeric(df_filtered.get('close', df_filtered.get('最新价')), errors='coerce')
        df_filtered = df_filtered[df_filtered['close'] < self.max_price].copy()
        stats['after_price'] = len(df_filtered)
        logger.info(f"筛选收盘价 < {self.max_price}元后：{len(df_filtered)} 只股票")

        # 4. 按成交额降序排列
        # 确保成交额是数值类型
        df_filtered['amount'] = pd.to_numeric(df_filtered.get('amount', df_filtered.get('成交额')), errors='coerce')
        df_filtered = df_filtered.sort_values('amount', ascending=False)

        # 5. 取前 N 只
        df_final = df_filtered.head(self.top_n)
        stats['final'] = len(df_final)
        logger.info(f"最终筛选结果：{len(df_final)} 只股票")

        return df_final, stats

    def run(self, dry_run: bool = False) -> Tuple[Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]]]:
        """
        执行筛选流程

        Args:
            dry_run: 是否仅测试运行（不输出结果）

        Returns:
            (股票列表，筛选报告) 或 (None, None) 如果失败
        """
        logger.info("=" * 70)
        logger.info("开始执行股票筛选...")
        logger.info(f"筛选条件：主板 + 非 ST + 收盘价<{self.max_price}元 + 成交额前{self.top_n}名")
        if self.base_stock_list:
            logger.info(f"基础股票池：{len(self.base_stock_list)}只 - {','.join(self.base_stock_list)}")
        logger.info("=" * 70)

        # 1. 获取全部 A 股数据
        df_all = self.get_all_a_shares()
        if df_all is None or len(df_all) == 0:
            logger.error("无法获取 A 股数据，筛选失败")
            # Fallback: 如果筛选失败但有基础池，返回基础池
            if self.base_stock_list:
                logger.warning("筛选失败，FALLBACK 到基础股票池")
                return self._build_base_stock_fallback(), self._build_fallback_report()
            return None, None

        # 2. 应用筛选条件
        df_filtered, stats = self.filter_stocks(df_all)

        if df_filtered is None or len(df_filtered) == 0:
            logger.warning("没有股票符合筛选条件")
            # Fallback: 如果筛选结果为空但有基础池，返回基础池
            if self.base_stock_list:
                logger.warning("筛选结果为空，FALLBACK 到基础股票池")
                return self._build_base_stock_fallback(), self._build_fallback_report()
            return [], {
                'screen_date': datetime.now().strftime('%Y-%m-%d'),
                'screen_time': datetime.now().strftime('%H:%M:%S'),
                'timezone': 'Asia/Shanghai',
                'fallback_reason': 'no_stocks_matched_criteria',
                'stats': stats,
                'stocks': [],
                'stock_codes': []
            }

        # 3. 构建输出结果（自动筛选的股票）
        auto_stocks = []
        for _, row in df_filtered.iterrows():
            stock_info = {
                'code': str(row.get('code', '')).zfill(6),
                'name': str(row.get('名称', row.get('name', ''))),
                'close': float(row.get('close', row.get('最新价', 0))),
                'amount': float(row.get('amount', row.get('成交额', 0))) if pd.notna(row.get('amount', row.get('成交额'))) else 0,
                'pct_chg': float(row.get('pct_chg', row.get('涨跌幅', 0))) if pd.notna(row.get('pct_chg', row.get('涨跌幅'))) else 0,
                'source': 'auto_screened'  # 标记来源
            }
            auto_stocks.append(stock_info)

        # 4. 合并基础股票池（去重）
        final_stocks = self._merge_with_base_pool(auto_stocks)

        # 5. 构建筛选报告
        report = {
            'screen_date': datetime.now().strftime('%Y-%m-%d'),
            'screen_time': datetime.now().strftime('%H:%M:%S'),
            'timezone': 'Asia/Shanghai',
            'strategy': {
                'description': '沪深主板 + 非 ST + 收盘价<50 元 + 成交额前 5 名',
                'max_price': self.max_price,
                'top_n': self.top_n,
                'exclude_growth_enterprise': True,  # 创业板
                'exclude_star_market': True,       # 科创板
                'exclude_st': True                 # ST 股票
            },
            'stats': stats,
            'auto_screened': auto_stocks,
            'base_pool': [
                {'code': code, 'source': 'base_pool'}
                for code in self.base_stock_list
            ],
            'stocks': final_stocks,
            'stock_codes': [s['code'] for s in final_stocks],  # 方便直接读取
            'merged_count': len(final_stocks),
            'auto_count': len(auto_stocks),
            'base_count': len(self.base_stock_list)
        }

        # 6. 输出结果
        if not dry_run:
            self._print_results(report)

        return final_stocks, report

    def _merge_with_base_pool(self, auto_stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合并自动筛选结果和基础股票池（去重）

        Args:
            auto_stocks: 自动筛选的股票列表

        Returns:
            合并后的股票列表
        """
        if not self.base_stock_list:
            return auto_stocks

        # 使用 OrderedDict 保持顺序并去重
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
                    'name': f'BASE-{code}',  # 基础池股票暂时用代码作为名称
                    'close': 0.0,
                    'amount': 0.0,
                    'pct_chg': 0.0,
                    'source': 'base_pool'
                })
                seen_codes.add(code)

        return merged

    def _build_base_stock_fallback(self) -> List[Dict[str, Any]]:
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

    def _build_fallback_report(self) -> Dict[str, Any]:
        """构建 fallback 报告"""
        return {
            'screen_date': datetime.now().strftime('%Y-%m-%d'),
            'screen_time': datetime.now().strftime('%H:%M:%S'),
            'timezone': 'Asia/Shanghai',
            'fallback_reason': 'screening_failed',
            'strategy': {
                'description': 'Fallback to base pool',
                'max_price': self.max_price,
                'top_n': self.top_n,
            },
            'base_pool': [
                {'code': code, 'source': 'base_pool'}
                for code in self.base_stock_list
            ],
            'stocks': self._build_base_stock_fallback(),
            'stock_codes': self.base_stock_list,
            'merged_count': len(self.base_stock_list),
            'auto_count': 0,
            'base_count': len(self.base_stock_list)
        }

    def _print_results(self, report: Dict[str, Any]):
        """打印筛选结果（兼容ASCII输出）"""
        is_fallback = report.get('fallback_reason') is not None

        print("\n" + "=" * 70)
        if is_fallback:
            print("[FALLBACK] 模式 - 使用基础股票池")
            print("=" * 70)
            print(f"日期：{report['screen_date']} {report['screen_time']}")
            print(f"原因：{report['fallback_reason']}")
        else:
            print("股票筛选结果")
            print("=" * 70)
            print(f"筛选日期：{report['screen_date']} {report['screen_time']}")
            print(f"筛选策略：{report['strategy']['description']}")

        print("-" * 70)

        if not is_fallback:
            print("筛选过程统计：")
            stats = report['stats']
            print(f"  - 初始股票数量：{stats['total']}只")
            print(f"  - 剔除创业板/科创板后：{stats['after_main_board']}只")
            print(f"  - 剔除ST股票后：{stats['after_no_st']}只")
            print(f"  - 收盘价<{self.max_price}元后：{stats['after_price']}只")
            print(f"  - 最终自动筛选（成交额前{self.top_n}名）：{stats['final']}只")
            print("-" * 70)

        print("合并统计：")
        print(f"  - 自动筛选：{report['auto_count']}只")
        print(f"  - 基础股票池：{report['base_count']}只")
        print(f"  - 合并后总计：{report['merged_count']}只")
        print("-" * 70)

        # 显示自动筛选的股票详情
        auto_stocks = report.get('auto_screened', [])
        if auto_stocks:
            print("自动筛选股票详情：")
            for i, stock in enumerate(auto_stocks, 1):
                print(f"\n  {i}. {stock['name']} ({stock['code']})")
                print(f"     收盘价：{stock['close']:.2f}元")
                print(f"     成交额：{stock['amount']/1e8:.2f}亿")
                if stock.get('pct_chg', 0) != 0:
                    sign = "+" if stock['pct_chg'] > 0 else ""
                    print(f"     涨跌幅：{sign}{stock['pct_chg']:.2f}%")
            print("-" * 70)

        # 显示基础池股票
        if report['base_count'] > 0:
            base_stocks = [s for s in report['stocks'] if s.get('source') == 'base_pool']
            if base_stocks:
                print("基础股票池（未重复）：")
                for i, stock in enumerate(base_stocks, 1):
                    print(f"  {i}. {stock['code']}")
                print("-" * 70)

        print(f"最终股票列表（逗号分隔）：{','.join(report['stock_codes'])}")
        print("=" * 70)


def save_to_json(data: Dict[str, Any], output_path: str) -> bool:
    """
    保存筛选结果到 JSON 文件

    Args:
        data: 要保存的数据字典
        output_path: 输出文件路径

    Returns:
        是否保存成功
    """
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"筛选结果已保存到：{output_file}")
        return True

    except Exception as e:
        logger.error(f"保存 JSON 文件失败：{e}", exc_info=True)
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='股票筛选器 - 每日自动筛选符合条件的股票')
    parser.add_argument(
        '--output',
        type=str,
        default='config/stocks.json',
        help='输出 JSON 文件路径（默认：config/stocks.json）'
    )
    parser.add_argument(
        '--max-price',
        type=float,
        default=None,
        help='最大收盘价（元，默认从环境变量 SCREENER_MAX_PRICE 或 50）'
    )
    parser.add_argument(
        '--top-n',
        type=int,
        default=None,
        help='返回前 N 只股票（默认从环境变量 SCREENER_TOP_N 或 5）'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅测试运行，不保存结果'
    )
    parser.add_argument(
        '--no-verbose',
        action='store_true',
        help='关闭详细输出模式'
    )

    args = parser.parse_args()

    # 从环境变量读取配置（优先级：命令行 > 环境变量 > 默认值）
    max_price = args.max_price if args.max_price is not None else float(os.getenv('SCREENER_MAX_PRICE', '50.0'))
    top_n = args.top_n if args.top_n is not None else int(os.getenv('SCREENER_TOP_N', '5'))
    verbose = not args.no_verbose and os.getenv('SCREENER_VERBOSE', 'true').lower() != 'false'

    # 读取基础股票池
    base_stock_list_str = os.getenv('BASE_STOCK_LIST', '')
    base_stock_list = [
        code.strip().upper()
        for code in base_stock_list_str.split(',')
        if code.strip()
    ]

    # 创建筛选器
    screener = StockScreener(
        max_price=max_price,
        top_n=top_n,
        base_stock_list=base_stock_list,
        verbose=verbose
    )

    # 执行筛选
    stocks, report = screener.run(dry_run=args.dry_run)

    if stocks is None:
        logger.error("筛选失败，退出")
        return 1

    if not args.dry_run:
        # 保存结果到 JSON
        if report:
            success = save_to_json(report, args.output)
            if not success:
                return 1

            # 同时保存一个纯股票代码文件（方便 Actions 读取）
            stock_codes_file = Path(args.output).with_suffix('.txt')
            with open(stock_codes_file, 'w', encoding='utf-8') as f:
                f.write(','.join(report['stock_codes']))
            logger.info(f"股票代码列表已保存到：{stock_codes_file}")

            # 输出到 stdout（方便 GitHub Actions 捕获）
            if verbose:
                print(f"\nSTOCK_LIST_OUTPUT={','.join(report['stock_codes'])}")

    logger.info("筛选完成！")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[中断] 用户取消操作")
        sys.exit(1)
    except Exception as e:
        logger.error(f"未预期的异常：{e}", exc_info=True)
        sys.exit(1)
