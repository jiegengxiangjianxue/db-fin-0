# db-fin-0 — A股财务因子全史 (fin_indicator)

数据源: 东方财富 datacenter-web `RPT_F10_FINANCE_MAINFINADATA` (F10 主要财务指标, 按报告期)。
接口: `GET https://datacenter-web.eastmoney.com/api/data/v1/get?reportName=RPT_F10_FINANCE_MAINFINADATA&filter=(SECUCODE="600000.SH")&sortColumns=REPORT_DATE&sortTypes=-1&pageSize=500`
需 `User-Agent` + `Referer: https://emweb.securities.eastmoney.com/`。全史 1998 至今, 每股约 40–120 条。

## Schema (data/fin_indicator/fin_indicator_{year}.parquet, 年分区)

| 字段 | 源字段 | 说明 |
|---|---|---|
| symbol | — | sh600000 / sz000001 / bj920000 |
| report_date | REPORT_DATE | 报告期 |
| announce_date | NOTICE_DATE | 公告日 |
| roe | ROEJQ | 加权ROE % (累计) |
| roa | TOAZZL | 总资产净利率 % |
| gross_margin | XSMLL | 销售毛利率 % (银行等常为空) |
| net_margin | XSJLL | 销售净利率 % |
| debt_ratio | ZCFZL | 资产负债率 % |
| current_ratio | LD | 流动比率 (银行常为空) |
| revenue_ttm | TOTALOPERATEREVE | 营业总收入 (累计) |
| profit_ttm | PARENTNETPROFIT | 归母净利润 (累计) |
| eps | EPSJB | 基本每股收益 |
| bps | BPS | 每股净资产 |
| ocf_ps | MGJYXJJE | 每股经营现金流 |

注: revenue_ttm/profit_ttm 为累计值(TTM需按报告期差分, engine 层处理); 备用源 RPT_LICO_FN_CPD 可用但字段较少。

## Backfill
`.github/workflows/fin-backfill.yml`: 每60分钟按 `(unix_epoch_hour % n_shards)` 拉一批200只, 增量合并进年分区 parquet。`shard_worker.py` 内嵌于 workflow。

## Sample validation
20只样票(600000/600036/600519/300750/688981等)全史已入库: 1712行, 1998–2026, 38个年分区。
