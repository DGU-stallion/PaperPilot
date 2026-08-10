"""清理面板数据：删除全空列，导出 .dta 格式"""
from pathlib import Path
import pandas as pd

_SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _SCRIPT_DIR.parent.parent
CLEAN_DIR = PROJECT_ROOT / "data" / "clean"

df = pd.read_csv(CLEAN_DIR / "china_provincial_panel_2011_2023.csv")

print(f"原始数据: {df.shape[0]} 行 × {df.shape[1]} 列")

# 识别并删除全空列
null_cols = df.columns[df.isnull().all()].tolist()
print(f"全空列 ({len(null_cols)}): {null_cols}")

df_clean = df.drop(columns=null_cols)

# 确认无其他缺失
remaining_null = df_clean.isnull().sum()
remaining_null = remaining_null[remaining_null > 0]
if len(remaining_null) > 0:
    print(f"警告：以下列存在部分缺失值:\n{remaining_null}")
else:
    print("确认：无任何缺失值")

# 排序（按省份、年份）
df_clean = df_clean.sort_values(["province_en", "year"]).reset_index(drop=True)

print(f"清洗后: {df_clean.shape[0]} 行 × {df_clean.shape[1]} 列")
print(f"变量列表: {df_clean.columns.tolist()}")
print(f"省份数: {df_clean['province_en'].nunique()}, 年份范围: {df_clean['year'].min()}-{df_clean['year'].max()}")

# 导出 .dta（便携格式，pandas/polars 均可读取）
df_clean.to_stata(
    CLEAN_DIR / "china_provincial_panel.dta",
    write_index=False,
    version=118
)

print("\n.dta 已导出: data/clean/china_provincial_panel.dta")
