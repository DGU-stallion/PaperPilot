#!/usr/bin/env python3
"""
01c_merge_manual_data.py — 合并手动补充数据与自动获取数据
将 manual_data_template.csv 中填好的数据合并到主面板数据中。

用法:
  1. 先在 manual_data_template.csv 中填入缺失的数据
  2. 运行: python data/scripts/01c_merge_manual_data.py
  3. 输出: data/clean/china_provincial_panel_complete.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path("D:/Project/PaperPilot")
CLEAN_DIR = PROJECT_ROOT / "data" / "clean"


def merge_manual_data():
    """合并手动填充的数据到主面板"""
    print("合并手动填充数据...")

    # 加载主面板数据
    panel_path = CLEAN_DIR / "china_provincial_panel_2011_2023.csv"
    if not panel_path.exists():
        print("[ERROR] 未找到主面板数据, 请先运行 01_fetch_data.py")
        return None

    panel = pd.read_csv(panel_path)
    print(f"主面板数据: {panel.shape}")

    # 加载手动填充数据
    manual_path = CLEAN_DIR / "manual_data_template.csv"
    if not manual_path.exists():
        print("[ERROR] 未找到手动填充模板, 请先运行 01b_fetch_supplementary.py")
        return None

    manual = pd.read_csv(manual_path)
    print(f"手动填充数据: {manual.shape}")

    # 检查是否有实际填充的数据 (非空列)
    filled_cols = [c for c in manual.columns if c not in ["province", "year"]
                   and not manual[c].isna().all()]

    if not filled_cols:
        print("[WARN] 手动填充模板中没有任何已填充的数据")
        print("请先在 manual_data_template.csv 中填入从《中国统计年鉴》等来源获取的数据")
        return panel

    print(f"已填充的变量: {filled_cols}")

    # 合并数据
    # 使用 province 和 year 作为键
    for col in filled_cols:
        # 从 manual 中提取非空值
        manual_subset = manual[["province", "year", col]].dropna(subset=[col])
        # 合并到 panel
        panel = panel.merge(manual_subset, on=["province", "year"], how="left", suffixes=("", "_manual"))

        # 如果 panel 已有该列, 用 manual 的值填充 NaN
        if col in panel.columns and f"{col}_manual" in panel.columns:
            panel[col] = panel[col].fillna(panel[f"{col}_manual"])
            panel.drop(columns=[f"{col}_manual"], inplace=True)

    # 保存完整数据
    output_path = CLEAN_DIR / "china_provincial_panel_complete.csv"
    panel.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n完整面板数据已保存: {output_path}")
    print(f"最终数据: {panel.shape[0]} 行 x {panel.shape[1]} 列")

    # 打印缺失率
    print("\n--- 最终缺失率 ---")
    for col in panel.columns:
        if col not in ["province", "year", "province_en", "region"]:
            missing = panel[col].isna().sum()
            if missing > 0:
                print(f"  {col}: {missing}/{len(panel)} 缺失 ({missing/len(panel)*100:.1f}%)")
            else:
                print(f"  {col}: 完整")

    return panel


if __name__ == "__main__":
    panel = merge_manual_data()
