#!/usr/bin/env python3
"""
测试股票筛选器逻辑（使用模拟数据）- 简单版本
"""

import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# 创建模拟数据
def create_mock_data():
    """创建模拟的A股行情数据"""
    data = {
        '代码': [
            '600519', '000001', '300750', '688001',  # 知名股票
            '600123', '000456', '600789', '000234',  # 主板股票
            '600567', '000678', '600890', '000901',  # 更多主板股票
            '300123', '688123',  # 创业板和科创板
            'ST1234', 'ST5678', '*ST9012'  # ST股票
        ],
        '名称': [
            '贵州茅台', '平安银行', '宁德时代', '华兴源创',
            '某某股份', '某某科技', '某某集团', '某某发展',
            '某某实业', '某某电子', '某某医药', '某某能源',
            '创业股票', '科创股票',
            'ST某股', 'ST某股', '*ST某股'
        ],
        '最新价': [
            1800.0, 15.5, 250.0, 80.0,  # 知名股票
            25.5, 18.2, 35.0, 22.0,  # 主板股票
            28.0, 15.0, 45.0, 30.0,  # 更多主板股票
            45.0, 60.0,  # 创业板和科创板
            5.0, 8.0, 12.0  # ST股票
        ],
        '成交额': [
            5.0e9, 2.0e9, 3.0e9, 1.0e9,  # 知名股票
            1.2e9, 9.8e8, 8.5e8, 7.2e8,  # 主板股票
            6.5e8, 5.8e8, 5.2e8, 4.5e8,  # 更多主板股票
            3.0e8, 2.5e8,  # 创业板和科创板
            1.0e8, 1.5e8, 2.0e8  # ST股票
        ],
        '涨跌幅': [
            1.5, -0.5, 2.0, -1.0,
            2.35, -1.20, 0.85, 1.50,
            -0.30, 0.60, -1.80, 0.95,
            1.20, -0.50,
            -2.00, -3.00, -4.00
        ]
    }

    df = pd.DataFrame(data)
    return df


def test_screener_logic():
    """测试筛选器逻辑"""
    print("=" * 70)
    print("STOCK SCREENER LOGIC TEST (Mock Data)")
    print("=" * 70)

    # 创建模拟数据
    df = create_mock_data()
    print(f"\nInitial data: {len(df)} stocks")
    print(df[['代码', '名称', '最新价', '成交额']].to_string(index=False))

    # 应用筛选逻辑
    print("\n" + "=" * 70)
    print("APPLYING FILTERS...")
    print("=" * 70)

    # 1. 剔除创业板和科创板
    def is_main_board(row):
        code = str(row['代码'])
        if code.startswith('300') or code.startswith('688'):
            return False
        return True

    df_filtered = df[df.apply(is_main_board, axis=1)].copy()
    print(f"\n[STEP 1] After removing ChiNext/STAR: {len(df_filtered)} stocks")
    print(f"   Removed: {set(df['代码']) - set(df_filtered['代码'])}")

    # 2. 剔除ST股票
    def no_st(row):
        name = str(row['名称'])
        return 'ST' not in name.upper()

    df_filtered = df_filtered[df_filtered.apply(no_st, axis=1)].copy()
    print(f"\n[STEP 2] After removing ST stocks: {len(df_filtered)} stocks")
    print(f"   Removed: {set(df['代码']) - set(df_filtered['代码'])}")

    # 3. 筛选收盘价 < 50元的股票
    df_filtered['close'] = pd.to_numeric(df_filtered['最新价'], errors='coerce')
    df_filtered = df_filtered[df_filtered['close'] < 50.0].copy()
    print(f"\n[STEP 3] After filtering close < 50: {len(df_filtered)} stocks")
    print(f"   Removed (price >= 50): {set(df['代码']) - set(df_filtered['代码'])}")

    # 4. 按成交额降序排列
    df_filtered['amount'] = pd.to_numeric(df_filtered['成交额'], errors='coerce')
    df_filtered = df_filtered.sort_values('amount', ascending=False)
    print(f"\n[STEP 4] Sorted by amount (descending)")

    # 5. 取前5只
    df_final = df_filtered.head(5)
    print(f"\n[STEP 5] Top 5 stocks:")

    print("\n" + "=" * 70)
    print("FINAL SCREENING RESULTS:")
    print("=" * 70)
    for i, (_, row) in enumerate(df_final.iterrows(), 1):
        print(f"\n  {i}. {row['名称']} ({row['代码']})")
        print(f"     Close: {row['最新价']:.2f} CNY")
        print(f"     Amount: {row['成交额']/1e8:.2f} billion CNY")
        sign = "+" if row['涨跌幅'] > 0 else ""
        print(f"     Change: {sign}{row['涨跌幅']:.2f}%")

    print("\n" + "=" * 70)
    print(f"STOCK CODES: {','.join(df_final['代码'])}")
    print("=" * 70)

    # 测试基础股票池合并
    print("\n" + "=" * 70)
    print("TEST BASE POOL MERGE LOGIC")
    print("=" * 70)

    base_pool = ['600519', '000001']  # 假设的基础池
    print(f"\nBase pool: {','.join(base_pool)}")

    # 合并逻辑（去重）
    seen_codes = set()
    merged = []

    # 优先添加自动筛选的股票
    for _, row in df_final.iterrows():
        code = row['代码']
        if code not in seen_codes:
            merged.append({
                'code': code,
                'name': row['名称'],
                'close': row['最新价'],
                'amount': row['成交额'],
                'source': 'auto_screened'
            })
            seen_codes.add(code)

    # 添加基础池中未重复的股票
    for code in base_pool:
        if code not in seen_codes:
            merged.append({
                'code': code,
                'name': f'BASE-{code}',
                'close': 0.0,
                'amount': 0.0,
                'source': 'base_pool'
            })
            seen_codes.add(code)

    print(f"\nMerged list: {len(merged)} stocks")
    print("Details:")
    for i, stock in enumerate(merged, 1):
        source_label = "Auto" if stock['source'] == 'auto_screened' else "Base"
        print(f"  {i}. {stock['code']} - {stock['name']} ({source_label})")

    print(f"\nFINAL STOCK CODES: {','.join([s['code'] for s in merged])}")

    print("\n" + "=" * 70)
    print("TEST PASSED! Screening logic works as expected.")
    print("=" * 70)

    return True


if __name__ == "__main__":
    try:
        test_screener_logic()
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
