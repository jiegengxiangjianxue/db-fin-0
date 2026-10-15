# fin_factor.py — 财务衍生因子

从 db-fin-0 的 parquet (data/fin_indicator/fin_indicator_{year}.parquet, schema 见该仓 README)
计算 12 个财务衍生因子, 独立注册, 不修改 factor_lib.py。

## import 方式
```python
import sys; sys.path.insert(0, "<engine-core>/scripts")
from fin_factor import FIN_FACTORS, load_fin_frame, register_into
from factor_lib import FACTORS          # 既有技术因子注册表
register_into(FACTORS)                  # 追加 fin_ 前缀因子 (12 个)
```

因子列表: fin_roe_ttm_yoy / fin_gross_margin_trend / fin_gross_margin_zscore /
fin_debt_change / fin_debt_trend / fin_ocf_profit_ratio / fin_ocf_margin /
fin_revenue_ttm_growth / fin_profit_ttm_growth / fin_roa_trend /
fin_net_margin_change / fin_current_ratio_trend

注: revenue_ttm/profit_ttm 源字段为报告期累计值, TTM 近似 = 当期 + 上年年报 - 上年同期。
自检: `/tmp/senv/bin/python fin_factor.py <db_dir>` 在 20 票样例上 12 因子全部可算
(银行票 gross_margin/current_ratio 为 nan 属源数据为空)。
