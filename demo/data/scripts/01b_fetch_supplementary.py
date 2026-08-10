#!/usr/bin/env python3
"""
01b_fetch_supplementary.py — 补充数据获取脚本
尝试从多个开放数据源获取 Figshare 数据集缺失的变量。

缺失变量:
  1. 城镇单位就业人员数 (urban_unit_employment)
  2. 城镇登记失业率 (registered_unemployment_rate)
  3. 电信业务总量 (telecom_business_volume)
  4. 信息传输、软件和信息技术服务业从业人员 (it_employment)
  5. 地区生产总值 GDP 总量 (gdp_total)
  6. 实际使用外资/FDI (fdi)
  7. R&D经费 (rd_expenditure)

数据来源尝试顺序:
  A. Wikipedia 表格 (GDP 总量, 人均GDP)
  B. World Bank API (国家层面参考)
  C. CNKI 数据平台
  D. 各省统计年鉴在线版本
  E. 学术论文复现数据
"""

import os
import sys
import re
import json
import warnings
from pathlib import Path

import pandas as pd
import numpy as np
import requests

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path("D:/Project/PaperPilot")
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEAN_DIR = PROJECT_ROOT / "data" / "clean"


# ============================================================
# A. Wikipedia: 中国各省GDP数据 (2011-2023)
# ============================================================
def scrape_wikipedia_gdp():
    """
    从 Wikipedia 获取中国各省GDP数据。
    英文页面包含历年数据表。
    """
    print("\n[A] Wikipedia: 尝试获取各省GDP数据...")

    try:
        url = "https://en.wikipedia.org/wiki/List_of_Chinese_administrative_divisions_by_GDP"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=30)
        r.encoding = 'utf-8'

        tables = pd.read_html(r.text)

        # Wikipedia 页面通常包含多个GDP表格
        # Table 2-5 可能是不同年份的GDP数据
        results = {}
        for i, table in enumerate(tables):
            if table.shape[0] > 30:  # 省份数据表通常有30+行
                print(f"  Table {i}: {table.shape[0]} rows x {table.shape[1]} cols")
                print(f"  Columns: {list(table.columns)[:8]}")
                results[i] = table

        if not results:
            print("  -> 未找到合适的GDP数据表")
            return None

        # 尝试从数据表中提取省份GDP
        # Wikipedia页面结构可能变化, 保存表格供人工检查
        for idx, tbl in results.items():
            tbl.to_csv(RAW_DIR / f"wikipedia_gdp_table_{idx}.csv",
                       index=False, encoding="utf-8-sig")
            print(f"  -> 已保存 Table {idx}")

        return results

    except Exception as e:
        print(f"  -> Wikipedia 抓取失败: {e}")
        return None


# ============================================================
# B. CEIC / World Bank Proxy Approach
# ============================================================
def fetch_world_bank_provincial_proxy():
    """
    使用 World Bank 的中国省级数据 (如果有)。
    World Bank Data API 查询省级数据。
    注意: 标准 WB API 没有中国省级数据。
    这里提供国家层面参考数据, 并说明如何推算省级数据。
    """
    print("\n[B] World Bank: 国家层面参考数据...")

    indicators = {
        "NY.GDP.MKTP.CD": "gdp_total_national",
        "NY.GDP.PCAP.CD": "gdp_percapita_national",
        "SL.UEM.TOTL.ZS": "unemployment_rate_national",
        "IT.NET.USER.ZS": "internet_users_pct_national",
        "IT.CEL.SETS.P2": "mobile_subscriptions_national",
        "BX.KLT.DINV.WD.GD.ZS": "fdi_inflow_pct_gdp_national",
        "GB.XPD.RSDV.GD.ZS": "rd_expenditure_pct_gdp_national",
    }

    all_data = {}
    for code, name in indicators.items():
        try:
            url = f"http://api.worldbank.org/v2/country/CN/indicator/{code}?format=json&per_page=50"
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                data = r.json()
                if len(data) > 1 and data[1]:
                    for item in data[1]:
                        if item["value"]:
                            year = int(item["date"])
                            if 2011 <= year <= 2023:
                                all_data.setdefault(year, {})[name] = float(item["value"])
        except Exception as e:
            print(f"  -> {name}: {e}")

    if all_data:
        df = pd.DataFrame.from_dict(all_data, orient="index")
        df.index.name = "year"
        print(f"  -> 获取了 {len(df)} 年 x {len(df.columns)} 个全国指标")
        df.to_csv(RAW_DIR / "world_bank_national_reference.csv", encoding="utf-8-sig")
        return df
    return None


# ============================================================
# C. 人工补充数据模板
# ============================================================
def create_manual_template():
    """
    创建手动填充缺失数据的模板文件。
    用户可以从《中国统计年鉴》等来源手动填入缺失变量。
    """
    print("\n[C] 创建手动数据填充模板...")

    # 读取现有的面板数据
    panel_path = CLEAN_DIR / "china_provincial_panel_2011_2023.csv"
    if panel_path.exists():
        panel = pd.read_csv(panel_path)
    else:
        # 创建省份年份网格
        provinces = [
            "北京市", "天津市", "河北省", "山西省", "内蒙古自治区",
            "辽宁省", "吉林省", "黑龙江省", "上海市", "江苏省",
            "浙江省", "安徽省", "福建省", "江西省", "山东省",
            "河南省", "湖北省", "湖南省", "广东省", "广西壮族自治区",
            "海南省", "重庆市", "四川省", "贵州省", "云南省",
            "西藏自治区", "陕西省", "甘肃省", "青海省", "宁夏回族自治区",
            "新疆维吾尔自治区"
        ]
        grid = [(p, y) for p in provinces for y in range(2011, 2024)]
        panel = pd.DataFrame(grid, columns=["province", "year"])

    # 添加缺失变量的空列
    template_cols = {
        "urban_unit_employment_10k": "城镇单位就业人员数 (万人)",
        "registered_unemployment_rate_pct": "城镇登记失业率 (%)",
        "telecom_business_volume_100m": "电信业务总量 (亿元)",
        "it_employment_10k": "信息传输/软件/IT服务业从业人员 (万人)",
        "gdp_total_100m": "地区生产总值 (亿元)",
        "fdi_100m_usd": "实际使用外资 (亿美元)",
        "rd_expenditure_100m": "R&D经费 (亿元)",
    }

    template = panel.copy()
    for col, desc in template_cols.items():
        template[col] = np.nan

    template_path = CLEAN_DIR / "manual_data_template.csv"
    template.to_csv(template_path, index=False, encoding="utf-8-sig")
    print(f"  -> 模板已创建: {template_path}")
    print(f"  -> 包含 {len(template_cols)} 个需要填充的变量")
    print(f"  -> 模板格式: {template.shape[0]} 行 x {template.shape[1]} 列")

    # 同时创建简易说明文档
    doc = """# 手动数据填充说明

## 数据来源推荐

| 变量 | 推荐数据来源 | 具体位置 |
|------|-------------|---------|
| 城镇单位就业人员数 | 《中国劳动统计年鉴》或《中国统计年鉴》 | 表 4-1 或 表 2-11 |
| 城镇登记失业率 | 《中国人口和就业统计年鉴》 | 表 2-5 |
| 电信业务总量 | 《中国统计年鉴》或工信部公报 | 表 15-30 或 通信业统计公报 |
| IT从业人员 | 《中国第三产业统计年鉴》 | 按行业分城镇单位就业人员 |
| GDP总量 | 《中国统计年鉴》 | 表 3-1 地区生产总值 |
| 实际使用外资 | 商务部数据中心 | data.mofcom.gov.cn |
| R&D经费 | 《中国科技统计年鉴》 | 表 1-2 |

## 推荐在线数据平台
1. 国家统计局: https://data.stats.gov.cn/easyquery.htm?cn=E0103
2. 马克数据网: https://www.macrodatas.cn/ (部分免费)
3. CNKI统计数据: https://data.cnki.net/
4. 众鲤数据网: https://zldatas.com/ (部分免费)
5. GitHub学术数据共享仓库

## 填充说明
- 在 manual_data_template.csv 中填入对应数据
- 然后运行: python 01c_merge_data.py
"""
    doc_path = CLEAN_DIR / "manual_data_fill_guide.md"
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"  -> 填充指南已创建: {doc_path}")

    return template


# ============================================================
# D. 从学术论文复现数据提取 (备用)
# ============================================================
def search_additional_replication_data():
    """
    搜索 Figshare/Zenodo 上更多中国省级数据。
    很多论文会公开复现数据。
    """
    print("\n[D] 搜索更多学术复现数据...")

    # 已知的 Figshare 数据集
    datasets = [
        {"id": "30656798", "desc": "Digital Inclusive Finance & Urban-Rural Integration (已获取)"},
    ]

    # 搜索更多
    try:
        r = requests.get(
            "https://api.figshare.com/v2/articles/search",
            params={"search": "China provincial panel data digital economy", "page_size": 10},
            timeout=30,
        )
        if r.status_code == 200:
            data = r.json()
            print(f"  -> 找到 {len(data)} 个相关数据集")
            for item in data:
                print(f"     [{item.get('id')}] {item.get('title', 'N/A')[:80]}")
                datasets.append({"id": item["id"], "desc": item.get("title", "")})
    except Exception as e:
        print(f"  -> Figshare 搜索失败: {e}")

    return datasets


# ============================================================
# E. 合并所有获取的数据
# ============================================================
def merge_all_data():
    """
    将所有获取的数据合并为最终的面板数据集。
    """
    print("\n[E] 合并所有数据源...")

    # 加载 Figshare 主数据集的编译版本
    panel_path = CLEAN_DIR / "china_provincial_panel_2011_2023.csv"
    if not panel_path.exists():
        print("  -> 错误: 未找到主面板数据, 请先运行 01_fetch_data.py")
        return None

    panel = pd.read_csv(panel_path)
    print(f"  -> 加载主面板数据: {panel.shape}")

    # 加载补充数据 (如果有)
    # 目前没有自动获取的补充数据, 需要手动填充

    print(f"  -> 最终面板数据: {panel.shape[0]} 行 x {panel.shape[1]} 列")
    return panel


# ============================================================
# 主流程
# ============================================================
def main():
    print("=" * 70)
    print("补充数据采集流程")
    print("=" * 70)

    # A. Wikipedia GDP
    wiki_data = scrape_wikipedia_gdp()

    # B. World Bank reference
    wb_data = fetch_world_bank_provincial_proxy()

    # C. Manual template
    template = create_manual_template()

    # D. Additional datasets
    more_data = search_additional_replication_data()

    # E. Merge
    panel = merge_all_data()

    # 总结
    print("\n" + "=" * 70)
    print("补充数据采集总结")
    print("=" * 70)

    # 已成功自动获取的变量
    auto_success = [
        "tertiary_employment_share (第三产业就业占比)",
        "internet_penetration (互联网普及率)",
        "mobile_phone_penetration (移动电话普及率)",
        "gdp_percapita (人均GDP)",
        "urbanization_rate (城镇化率)",
        "fixed_capital_investment (固定资产投资)",
        "export_share (出口占比)",
        "government_expenditure (财政支出)",
        "education_expenditure (教育支出)",
        "digital_finance_index (数字普惠金融指数)",
        "digital_economy_index (数字经济综合指数)",
    ]
    print(f"\n自动获取成功 ({len(auto_success)}):")
    for v in auto_success:
        print(f"  [OK] {v}")

    # 需要手动补充的变量
    manual_needed = [
        "urban_unit_employment (城镇单位就业人员数)",
        "registered_unemployment_rate (城镇登记失业率)",
        "telecom_business_volume (电信业务总量)",
        "it_employment (信息传输/软件/IT服务业从业人员)",
        "gdp_total (GDP总量)",
        "fdi (实际使用外资)",
        "rd_expenditure (R&D经费)",
    ]
    print(f"\n需要手动补充 ({len(manual_needed)}):")
    for v in manual_needed:
        print(f"  [MANUAL] {v}")

    print(f"\n手动填充模板: {CLEAN_DIR / 'manual_data_template.csv'}")
    print(f"填充指南: {CLEAN_DIR / 'manual_data_fill_guide.md'}")
    print(f"填充后运行: python data/scripts/01c_merge_manual_data.py")

    return panel


if __name__ == "__main__":
    panel = main()
