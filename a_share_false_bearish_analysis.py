#!/usr/bin/env python3
"""统计A股日K线出现“假阴线”后下一交易日收盘上涨的概率。

假阴线定义（可按需要调整）：
1) 当日收盘价 < 当日开盘价（K线呈阴线）
2) 当日收盘价 > 前一交易日收盘价（相对前日仍上涨）

“后一天收盘时是上涨”定义：下一交易日收盘价 > 假阴线当日收盘价。
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from typing import Iterable

import pandas as pd

try:
    import akshare as ak
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "缺少依赖 akshare，请先安装：pip install akshare pandas"
    ) from exc


@dataclass
class SignalStat:
    symbol: str
    signal_count: int
    next_up_count: int

    @property
    def prob(self) -> float:
        if self.signal_count == 0:
            return 0.0
        return self.next_up_count / self.signal_count


def get_a_share_symbols(limit: int | None = None) -> list[str]:
    """获取A股股票代码列表。"""
    spot = ak.stock_zh_a_spot_em()
    symbols = spot["代码"].dropna().astype(str).tolist()
    if limit is not None:
        symbols = symbols[:limit]
    return symbols


def fetch_daily_k(symbol: str, start: str, end: str, adjust: str = "qfq") -> pd.DataFrame:
    """获取单只股票日线数据。"""
    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start,
        end_date=end,
        adjust=adjust,
    )
    if df.empty:
        return df

    keep_cols = ["日期", "开盘", "收盘"]
    df = df[keep_cols].copy()
    df["日期"] = pd.to_datetime(df["日期"])
    df = df.sort_values("日期").reset_index(drop=True)
    return df


def calc_false_bearish_next_up(df: pd.DataFrame) -> tuple[int, int]:
    """计算假阴线信号数量与下一日上涨数量。"""
    if len(df) < 3:
        return 0, 0

    prev_close = df["收盘"].shift(1)
    next_close = df["收盘"].shift(-1)

    false_bearish = (df["收盘"] < df["开盘"]) & (df["收盘"] > prev_close)
    valid = false_bearish & next_close.notna()
    next_up = valid & (next_close > df["收盘"])

    return int(valid.sum()), int(next_up.sum())


def analyze(
    symbols: Iterable[str],
    start: str,
    end: str,
    adjust: str,
    sleep_sec: float,
) -> list[SignalStat]:
    """遍历股票并统计信号结果。"""
    results: list[SignalStat] = []

    for idx, symbol in enumerate(symbols, start=1):
        try:
            df = fetch_daily_k(symbol=symbol, start=start, end=end, adjust=adjust)
            signal_count, next_up_count = calc_false_bearish_next_up(df)
            results.append(SignalStat(symbol, signal_count, next_up_count))
        except Exception as exc:
            print(f"[WARN] {symbol} 处理失败: {exc}")

        if idx % 100 == 0:
            print(f"已处理 {idx} 只股票...")
        if sleep_sec > 0:
            time.sleep(sleep_sec)

    return results


def print_report(results: list[SignalStat], top_n: int = 10) -> None:
    """输出汇总报告。"""
    total_signal = sum(x.signal_count for x in results)
    total_next_up = sum(x.next_up_count for x in results)
    total_prob = (total_next_up / total_signal) if total_signal else 0.0

    print("\n=== 全市场汇总 ===")
    print(f"假阴线样本数: {total_signal}")
    print(f"次日上涨样本数: {total_next_up}")
    print(f"次日上涨概率: {total_prob:.2%}")

    detail = [x for x in results if x.signal_count > 0]
    detail.sort(key=lambda x: x.prob, reverse=True)

    print(f"\n=== 个股概率Top {top_n}（至少1个信号）===")
    for item in detail[:top_n]:
        print(
            f"{item.symbol}: 假阴线={item.signal_count}, 次日上涨={item.next_up_count}, 概率={item.prob:.2%}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="A股假阴线后次日上涨概率统计")
    parser.add_argument("--start", default="20200101", help="开始日期，格式YYYYMMDD")
    parser.add_argument("--end", default="20251231", help="结束日期，格式YYYYMMDD")
    parser.add_argument(
        "--adjust",
        default="qfq",
        choices=["", "qfq", "hfq"],
        help="复权方式：''不复权, qfq前复权, hfq后复权",
    )
    parser.add_argument("--limit", type=int, default=None, help="仅分析前N只股票（调试用）")
    parser.add_argument("--sleep", type=float, default=0.0, help="每只股票请求间隔秒数")
    parser.add_argument("--top", type=int, default=10, help="输出个股TopN")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    symbols = get_a_share_symbols(limit=args.limit)
    print(f"待分析股票数量: {len(symbols)}")

    results = analyze(
        symbols=symbols,
        start=args.start,
        end=args.end,
        adjust=args.adjust,
        sleep_sec=args.sleep,
    )
    print_report(results, top_n=args.top)


if __name__ == "__main__":
    main()
