#!/usr/bin/env python3
"""
财务因子库 (fin_factor) — 从 db-fin parquet (fin_indicator 年分区) 计算衍生财务因子。

独立于 factor_lib.py (行情技术因子): 不修改 factor_lib.py, 通过
    import sys; sys.path.insert(0, <engine-core>/scripts)
    from fin_factor import FIN_FACTORS, load_fin_frame, register_into
注册方式 (不覆盖既有注册表):
    from factor_lib import FACTORS
    register_into(FACTORS)   # 追加 (fid, label, group, fn) 四元组

输入 df: 按 (symbol, report_date) 升序的单票财务帧, 需含列:
  symbol, report_date, roe, roa, gross_margin, net_margin, debt_ratio,
  current_ratio, revenue_ttm, profit_ttm, eps, bps, ocf_ps
注意: revenue_ttm/profit_ttm 为报告期累计值, TTM 用滚动4期差分近似。
"""
from __future__ import annotations
import glob
import os
import pandas as pd
import numpy as np

FIN_FACTORS = []


def fin_factor(fid, label, group):
    def deco(fn):
        FIN_FACTORS.append((fid, label, group, fn))
        return fn
    return deco


def register_into(factor_list):
    """把财务因子追加进既有 factor_lib.FACTORS 列表 (id 前缀 fin_ 防冲突)。"""
    factor_list.extend(FIN_FACTORS)
    return len(FIN_FACTORS)


def load_fin_frame(db_dir):
    """读 data/fin_indicator/fin_indicator_*.parquet → 每票按报告期升序拼接。"""
    parts = []
    for f in sorted(glob.glob(os.path.join(db_dir, "fin_indicator_*.parquet"))):
        parts.append(pd.read_parquet(f))
    df = pd.concat(parts, ignore_index=True).drop_duplicates(
        subset=["symbol", "report_date"], keep="last")
    df["report_date"] = pd.to_datetime(df["report_date"])
    return df.sort_values(["symbol", "report_date"]).reset_index(drop=True)


def _ttm(df, col):
    """累计值 → TTM: 当期累计 + 上年年报 - 上年同期累计。"""
    s = df.groupby("symbol")[col]
    cur = s.transform(lambda x: x)
    prev_q = s.shift(1)
    prev_y = s.shift(4)
    prev_yq = s.shift(5)
    return cur + prev_y.fillna(0) - prev_yq.fillna(0) - (prev_q - prev_yq).fillna(0)


# ---- 12 个衍生因子 (fn(df)->Series, 单票帧) ----

@fin_factor("fin_roe_ttm_yoy", "ROE-TTM同比", "财务")
def f(df):
    roe_ttm = df.roe + df.roe.shift(4).fillna(0) - df.roe.shift(5).fillna(0)
    return (roe_ttm / roe_ttm.shift(4).replace(0, np.nan) - 1).clip(-10, 10)


@fin_factor("fin_gross_margin_trend", "毛利率趋势(3期斜率)", "财务")
def f(df):
    g = df.gross_margin
    return (g - g.shift(3)) / 3


@fin_factor("fin_gross_margin_zscore", "毛利率三年z分", "财务")
def f(df):
    g = df.gross_margin
    m = g.rolling(12, min_periods=4).mean()
    s = g.rolling(12, min_periods=4).std()
    return (g - m) / s.replace(0, np.nan)


@fin_factor("fin_debt_change", "负债率变化(4期)", "财务")
def f(df):
    return df.debt_ratio - df.debt_ratio.shift(4)


@fin_factor("fin_debt_trend", "负债率趋势(3期斜率)", "财务")
def f(df):
    d = df.debt_ratio
    return (d - d.shift(3)) / 3


@fin_factor("fin_ocf_profit_ratio", "经营现金流/净利润", "财务")
def f(df):
    ocf = df.ocf_ps * (df.revenue_ttm / df.eps.replace(0, np.nan))
    return (ocf / df.profit_ttm.replace(0, np.nan)).clip(-20, 20)


@fin_factor("fin_ocf_margin", "现金流利润率", "财务")
def f(df):
    ocf = df.ocf_ps * (df.revenue_ttm / df.eps.replace(0, np.nan))
    return ocf / df.revenue_ttm.replace(0, np.nan)


@fin_factor("fin_revenue_ttm_growth", "营收TTM同比", "财务")
def f(df):
    rev = _ttm(df.assign(_x=df.revenue_ttm), "_x")
    return rev.pct_change(4).clip(-10, 10)


@fin_factor("fin_profit_ttm_growth", "净利TTM同比", "财务")
def f(df):
    p = _ttm(df.assign(_x=df.profit_ttm), "_x")
    return p.pct_change(4).clip(-10, 10)


@fin_factor("fin_roa_trend", "ROA趋势(4期变化)", "财务")
def f(df):
    return df.roa - df.roa.shift(4)


@fin_factor("fin_net_margin_change", "净利率变化(4期)", "财务")
def f(df):
    return df.net_margin - df.net_margin.shift(4)


@fin_factor("fin_current_ratio_trend", "流动比率趋势", "财务")
def f(df):
    c = df.current_ratio
    return (c - c.shift(4)) / c.shift(4).replace(0, np.nan)


if __name__ == "__main__":
    import sys
    db = sys.argv[1] if len(sys.argv) > 1 else "data/fin_indicator"
    df = load_fin_frame(db)
    print("rows", len(df), "symbols", df.symbol.nunique())
    one = df[df.symbol == df.symbol.iloc[0]]
    for fid, label, group, fn in FIN_FACTORS:
        try:
            out = fn(one)
            print(f"{fid:28s} last={out.iloc[-1]:.4f}" if len(out) and pd.notna(out.iloc[-1])
                  else f"{fid:28s} nan")
        except Exception as e:
            print(f"{fid:28s} ERR {e}")
