#!/usr/bin/env python3
"""
01_fetch_data.py — 中国省级面板数据自动采集脚本 (2011-2023)
Digital Economy's Impact on Employment

采集策略：
  1. 主数据源：Figshare 论文复现数据 (PONE-D-25-41664) — 已下载
  2. 补充数据源：尝试 NBS API、Macrodatas.cn、World Bank API 等
  3. 最终输出：合并后的省级面板数据到 data/clean/

作者: Agent
日期: 2026-05-12
"""

import os
import sys
import json
import warnings
from pathlib import Path

import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

# ============================================================
# 路径配置（自动适配项目结构）
# ============================================================
_SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _SCRIPT_DIR.parent.parent  # papers/demo-paper/
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEAN_DIR = PROJECT_ROOT / "data" / "clean"
SCRIPTS_DIR = PROJECT_ROOT / "data" / "scripts"
OUTPUT_DIR = PROJECT_ROOT / "analysis" / "output"

for d in [RAW_DIR, CLEAN_DIR, SCRIPTS_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ============================================================
# 数据获取状态追踪
# ============================================================
class DataStatus:
    """追踪每个变量的获取状态"""
    def __init__(self):
        self.variables = {}

    def add(self, name, cn_name, status, source, note=""):
        self.variables[name] = {
            "cn_name": cn_name,
            "status": status,  # "ok", "partial", "missing"
            "source": source,
            "note": note
        }

    def report(self):
        """生成数据获取报告"""
        ok = [k for k, v in self.variables.items() if v["status"] == "ok"]
        partial = [k for k, v in self.variables.items() if v["status"] == "partial"]
        missing = [k for k, v in self.variables.items() if v["status"] == "missing"]

        print("\n" + "=" * 70)
        print("数据获取报告 (Data Acquisition Report)")
        print("=" * 70)
        print(f"\n目标: 31省份 x 13年 (2011-2023) = 403 观测值")
        print(f"\n--- 成功获取 ({len(ok)} variables) ---")
        for v in ok:
            info = self.variables[v]
            print(f"  [OK] {v:30s} | {info['cn_name']:20s} | {info['source']}")

        print(f"\n--- 部分获取 ({len(partial)} variables) ---")
        for v in partial:
            info = self.variables[v]
            print(f"  [PARTIAL] {v:30s} | {info['cn_name']:20s} | {info['note']}")

        print(f"\n--- 缺失 ({len(missing)} variables) ---")
        for v in missing:
            info = self.variables[v]
            print(f"  [MISSING] {v:30s} | {info['cn_name']:20s} | {info['note']}")

        print("\n" + "=" * 70)
        return self.variables

status = DataStatus()


# ============================================================
# 1. 加载 Figshare 主数据集
# ============================================================
def load_figshare_data():
    """
    加载从 Figshare 下载的论文复现数据。
    论文: "Unveiling nonlinear effects of Digital Inclusive Finance on urban-rural integration"
    链接: https://figshare.com/articles/dataset/data_for_PONE-D-25-41664/30656798
    """
    figshare_path = RAW_DIR / "figshare_PONE_D_25_41664.xlsx"
    if not figshare_path.exists():
        print("[WARN] Figshare 数据文件未找到，尝试下载...")
        try:
            import requests
            url = "https://ndownloader.figshare.com/files/59694182"
            r = requests.get(url, timeout=60)
            with open(figshare_path, "wb") as f:
                f.write(r.content)
            print(f"  -> 下载成功 ({len(r.content)} bytes)")
        except Exception as e:
            print(f"  -> 下载失败: {e}")
            return None

    df = pd.read_excel(figshare_path, sheet_name="Sheet1")
    print(f"\n[Figshare 主数据集]")
    print(f"  维度: {df.shape[0]} rows x {df.shape[1]} cols")
    print(f"  省份数: {df['province'].nunique()}")
    print(f"  年份范围: {df['year'].min()} - {df['year'].max()}")
    print(f"  变量列表: {', '.join(df.columns)}")

    return df


# ============================================================
# 2. 尝试从 NBS API 获取数据
# ============================================================
def fetch_from_nbs_api():
    """
    尝试从国家统计局 (data.stats.gov.cn) 的 easyquery API 获取数据。
    注意: NBS 有 WAF 防护，非中国大陆 IP 可能被拦截。
    本函数提供备用方案提示。
    """
    print("\n[NBS API] 尝试连接国家统计局 API...")

    try:
        import requests
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://data.stats.gov.cn/easyquery.htm?cn=A0G",
            "X-Requested-With": "XMLHttpRequest",
        })

        # 尝试获取树形目录
        params = {"id": "zb", "dbcode": "A0G", "wdcode": "zb", "m": "getTree"}
        r = session.post("https://data.stats.gov.cn/easyquery.htm", params=params, timeout=30)

        if r.status_code == 200:
            data = r.json()
            print(f"  -> 成功连接，获取 {len(data)} 个顶级节点")
            return data
        else:
            print(f"  -> NBS API 返回 {r.status_code} (WAF 拦截), 无法直接获取")
            print(f"  -> 备选方案: 使用 World Bank API 或手动从统计年鉴整理")
            return None
    except Exception as e:
        print(f"  -> NBS API 错误: {e}")
        return None


# ============================================================
# 3. 尝试从 World Bank API 获取中国数据 (备用)
# ============================================================
def fetch_from_world_bank():
    """
    使用 World Bank API 获取中国的省级宏观数据。
    注意: World Bank 只有国家层面数据，没有中国省级数据。
    这里主要获取中国全国层面的参考数据。
    """
    print("\n[World Bank API] 尝试获取中国宏观数据...")
    results = {}

    # World Bank indicators for China (national level)
    indicators = {
        "NY.GDP.MKTP.CD": "GDP (current US$)",
        "NY.GDP.PCAP.CD": "GDP per capita (current US$)",
        "SL.UEM.TOTL.ZS": "Unemployment (% of total labor force)",
        "IT.NET.USER.ZS": "Internet users (% of population)",
        "IT.CEL.SETS.P2": "Mobile cellular subscriptions (per 100 people)",
        "NE.GDI.FTOT.ZS": "Gross fixed capital formation (% of GDP)",
        "BX.KLT.DINV.WD.GD.ZS": "FDI net inflows (% of GDP)",
        "GB.XPD.RSDV.GD.ZS": "R&D expenditure (% of GDP)",
        "SE.PRM.ENRR": "School enrollment, primary (% gross)",
    }

    try:
        import requests
        for code, name in indicators.items():
            url = f"http://api.worldbank.org/v2/country/CN/indicator/{code}?format=json&per_page=50"
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                data = r.json()
                if len(data) > 1 and data[1]:
                    records = []
                    for item in data[1]:
                        if item["value"] and 2011 <= int(item["date"]) <= 2023:
                            records.append({"year": int(item["date"]), code: float(item["value"])})
                    if records:
                        results[code] = pd.DataFrame(records)
                        print(f"  -> {name}: {len(records)} 年数据")
            else:
                print(f"  -> {name}: 获取失败 ({r.status_code})")
    except Exception as e:
        print(f"  -> World Bank API 错误: {e}")

    if results:
        # 合并所有 WB 指标
        wb_df = None
        for code, df in results.items():
            if wb_df is None:
                wb_df = df.set_index("year")
            else:
                wb_df = wb_df.join(df.set_index("year"), how="outer")

        print(f"  共获取 {len(wb_df)} 年 x {len(wb_df.columns)} 个指标")
        return wb_df
    else:
        print("  -> 未能获取任何 World Bank 数据")
        return None


# ============================================================
# 4. 尝试从 Macrodatas.cn 获取数据
# ============================================================
def fetch_from_macrodatas():
    """
    尝试从马克数据网 (macrodatas.cn) 获取免费数据。
    注意: 部分数据需要登录/会员。
    """
    print("\n[Macrodatas.cn] 尝试获取省级数据...")
    print("  -> 马克数据网需要会员登录，无法直接下载")
    print("  -> 免费共享的中国统计年鉴需通过百度网盘手动下载")
    print("  -> 推荐手动下载页面: https://www.macrodatas.cn/article/1147472487")
    return None


# ============================================================
# 5. 编译综合面板数据
# ============================================================
def compile_panel_data(figshare_df):
    """
    将 Figshare 主数据集转换为所需的研究变量。
    构建统一的省级面板数据。
    """
    print("\n" + "=" * 70)
    print("编译省级面板数据...")
    print("=" * 70)

    df = figshare_df.copy()

    # ---- 省份编码 ----
    # 中文省份名映射
    province_cn = {
        "Beijing": "北京市", "Tianjin": "天津市", "Hebei": "河北省",
        "Shanxi": "山西省", "Inner Mongolia": "内蒙古自治区",
        "Liaoning": "辽宁省", "Jilin": "吉林省", "Heilongjiang": "黑龙江省",
        "Shanghai": "上海市", "Jiangsu": "江苏省", "Zhejiang": "浙江省",
        "Anhui": "安徽省", "Fujian": "福建省", "Jiangxi": "江西省",
        "Shandong": "山东省", "Henan": "河南省", "Hubei": "湖北省",
        "Hunan": "湖南省", "Guangdong": "广东省", "Guangxi": "广西壮族自治区",
        "Hainan": "海南省", "Chongqing": "重庆市", "Sichuan": "四川省",
        "Guizhou": "贵州省", "Yunnan": "云南省", "Tibet": "西藏自治区",
        "Shaanxi": "陕西省", "Gansu": "甘肃省", "Qinghai": "青海省",
        "Ningxia": "宁夏回族自治区", "Xinjiang": "新疆维吾尔自治区",
        "Shangdong": "山东省",  # typo in original data?
    }
    df["province_cn"] = df["province"].map(province_cn)

    # ---- 变量映射与创建 ----
    panel = pd.DataFrame()
    panel["province_en"] = df["province"]
    panel["province"] = df["province_cn"]
    panel["year"] = df["year"].astype(int)
    panel["region"] = df["region"]

    # --- 被解释变量 (Y) ---
    # Y1: 第三产业就业占比 (已有)
    panel["tertiary_employment_share"] = df["Tertiary_share"]
    status.add(
        "tertiary_employment_share", "第三产业就业占比", "ok",
        "Figshare", "来源: 中国统计年鉴"
    )

    # Y2: 城镇单位就业人员数 — 需要从其他来源获取
    panel["urban_unit_employment"] = np.nan
    status.add(
        "urban_unit_employment", "城镇单位就业人员数", "missing",
        "N/A", "Figshare 数据不含此项，需从《中国劳动统计年鉴》获取"
    )

    # Y3: 城镇登记失业率 — 需要从其他来源获取
    panel["registered_unemployment_rate"] = np.nan
    status.add(
        "registered_unemployment_rate", "城镇登记失业率", "missing",
        "N/A", "Figshare 数据不含此项，需从《中国统计年鉴》获取"
    )

    # --- 核心解释变量 (D) - 数字经济指数 ---
    # D1: 互联网普及率 (已有)
    panel["internet_penetration"] = df["Internet_penetration"]
    status.add(
        "internet_penetration", "互联网普及率", "ok",
        "Figshare", "来源: 中国统计年鉴 / CNNIC"
    )

    # D2: 移动电话普及率 (已有)
    panel["mobile_phone_penetration"] = df["MPP"]
    status.add(
        "mobile_phone_penetration", "移动电话普及率", "ok",
        "Figshare", "来源: 中国统计年鉴"
    )

    # D3: 电信业务总量 — 需要从其他来源获取
    panel["telecom_business_volume"] = np.nan
    status.add(
        "telecom_business_volume", "电信业务总量", "missing",
        "N/A", "Figshare 数据不含此项，需从工信部或统计年鉴获取"
    )

    # D4: 信息传输、软件和信息技术服务业从业人员 — 需要从其他来源获取
    panel["it_employment"] = np.nan
    status.add(
        "it_employment", "信息传输/软件/IT服务业从业人员", "missing",
        "N/A", "可从 macrodatas.cn 获取 (需会员) 或从统计年鉴手动整理"
    )

    # --- 控制变量 (X) ---
    # X1: 地区生产总值 (从 Figshare 没有直接的总量 GDP)
    # 但有 GDP_percapita; 如果有常住人口数据可以换算
    panel["gdp_percapita"] = df["GDP_percapita"]
    status.add(
        "gdp_percapita", "人均GDP", "ok",
        "Figshare", "来源: 中国统计年鉴"
    )

    # X2: GDP总量 — 需要计算或从其他来源获取
    panel["gdp_total"] = np.nan
    status.add(
        "gdp_total", "地区生产总值(GDP)", "missing",
        "N/A", "Figshare 有人均GDP但无总量，需人口数据换算"
    )

    # X3: 城镇化率 (已有)
    panel["urbanization_rate"] = df["urban_rate"]
    status.add(
        "urbanization_rate", "城镇化率", "ok",
        "Figshare", "来源: 中国统计年鉴"
    )

    # X4: 固定资产投资 (已有 - FCI)
    panel["fixed_capital_investment"] = df["FCI"]
    status.add(
        "fixed_capital_investment", "固定资产投资", "ok",
        "Figshare", "变量名 FCI (Fixed Capital Investment)"
    )

    # X5: 实际使用外资/FDI (Figshare 有 exports 但无 FDI)
    panel["fdi"] = np.nan
    status.add(
        "fdi", "实际使用外资/FDI", "missing",
        "N/A", "Figshare 仅有 exports 和 export_share，无 FDI"
    )
    # 用 export_share 作为贸易开放度的替代
    panel["export_share"] = df["export_share"]
    status.add(
        "export_share", "出口占比(贸易开放度)", "ok",
        "Figshare", "可作为 FDI 的弱替代变量"
    )

    # X6: 财政支出 (已有)
    panel["government_expenditure"] = df["GOV"]
    status.add(
        "government_expenditure", "财政支出", "ok",
        "Figshare", "来源: 中国统计年鉴"
    )

    # X7: R&D经费 — 需要从其他来源获取
    panel["rd_expenditure"] = np.nan
    status.add(
        "rd_expenditure", "R&D经费", "missing",
        "N/A", "Figshare 数据不含此项"
    )

    # X8: 教育支出/人力资本 (已有)
    panel["education_expenditure"] = df["edu_total"]
    status.add(
        "education_expenditure", "教育支出", "ok",
        "Figshare", "来源: 中国统计年鉴"
    )
    # EDU 可能是教育支出占比
    panel["education_share"] = df["EDU"]

    # --- 数字经济综合指数 ---
    # DIF: 北京大学数字普惠金融指数 (已有)
    panel["digital_finance_index"] = df["DIF"]
    status.add(
        "digital_finance_index", "数字普惠金融指数(PKU)", "ok",
        "Figshare", "来源: 北京大学数字金融研究中心"
    )

    # DE: 数字经济综合指数 (已有)
    panel["digital_economy_index"] = df["DE"]
    status.add(
        "digital_economy_index", "数字经济综合指数", "ok",
        "Figshare", "作者构建的 DE 指数"
    )

    return panel


# ============================================================
# 6. 保存与报告
# ============================================================
def save_panel_data(panel):
    """保存面板数据为 CSV 和 .dta 格式"""
    print("\n" + "=" * 70)
    print("保存面板数据...")
    print("=" * 70)

    # CSV 格式
    csv_path = CLEAN_DIR / "china_provincial_panel_2011_2023.csv"
    panel.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"  CSV: {csv_path} ({panel.shape[0]} rows x {panel.shape[1]} cols)")

    # Excel 格式 (方便查看)
    xlsx_path = CLEAN_DIR / "china_provincial_panel_2011_2023.xlsx"
    panel.to_excel(xlsx_path, index=False)
    print(f"  Excel: {xlsx_path}")

    # 变量说明表
    var_desc = pd.DataFrame({
        "variable": panel.columns,
        "description": [
            "省份 (英文)", "省份 (中文)", "年份", "区域代码",
            "第三产业就业占比", "城镇单位就业人员数 (万人, 缺失)",
            "城镇登记失业率 (%, 缺失)",
            "互联网普及率 (每百人)", "移动电话普及率 (每百人)",
            "电信业务总量 (缺失)", "信息传输/软件/IT服务业从业人员 (缺失)",
            "人均GDP (元)", "地区生产总值 (缺失)",
            "城镇化率", "固定资产投资",
            "实际使用外资 (缺失)", "出口占比",
            "财政支出", "R&D经费 (缺失)",
            "教育支出 (亿元)", "教育支出占比",
            "数字普惠金融指数 (PKU)", "数字经济综合指数",
        ]
    })
    var_desc_path = CLEAN_DIR / "variable_description.csv"
    var_desc.to_csv(var_desc_path, index=False, encoding="utf-8-sig")
    print(f"  变量说明: {var_desc_path}")

    return csv_path


def generate_report(panel, wb_data):
    """生成综合数据报告"""
    print("\n" + "=" * 70)
    print("数据质量报告")
    print("=" * 70)

    n_expected = 31 * 13  # 403
    n_actual = len(panel)
    print(f"\n预期观测值: {n_expected} (31 provinces x 13 years)")
    print(f"实际观测值: {n_actual}")

    # 检查每个变量的缺失情况
    print(f"\n--- 变量缺失率统计 ---")
    missing_cols = [
        "urban_unit_employment", "registered_unemployment_rate",
        "internet_penetration", "mobile_phone_penetration",
        "telecom_business_volume", "it_employment",
        "gdp_percapita", "gdp_total",
        "urbanization_rate", "fixed_capital_investment",
        "fdi", "export_share",
        "government_expenditure", "rd_expenditure",
        "education_expenditure", "digital_finance_index",
        "digital_economy_index", "tertiary_employment_share"
    ]

    for col in missing_cols:
        if col in panel.columns:
            n_missing = panel[col].isna().sum()
            missing_rate = n_missing / n_actual * 100
            if n_missing == n_actual:
                status_str = "[完全缺失]"
            elif n_missing > 0:
                status_str = f"[部分缺失: {n_missing}/{n_actual} ({missing_rate:.1f}%)]"
            else:
                status_str = "[完整]"
            print(f"  {col:35s} {status_str}")

    # 保存报告
    report = {
        "data_source": "Figshare PONE-D-25-41664",
        "provinces": 31,
        "years": "2011-2023",
        "expected_observations": n_expected,
        "actual_observations": n_actual,
        "variables": status.variables,
        "recommendations": [
            "1. 城镇单位就业人员数: 从《中国劳动统计年鉴》或《中国人口和就业统计年鉴》手动整理",
            "2. 城镇登记失业率: 从 zldatas.com 或国家统计局数据库下载",
            "3. 电信业务总量: 从工信部通信业统计公报或《中国统计年鉴》整理",
            "4. IT从业人员: 从 macrodatas.cn (需会员) 或《中国第三产业统计年鉴》整理",
            "5. GDP总量: 用人口数据 * 人均GDP 估算, 或从统计年鉴直接获取",
            "6. 实际使用外资: 从商务部数据中心 (data.mofcom.gov.cn) 获取",
            "7. R&D经费: 从《中国科技统计年鉴》或《中国统计年鉴》整理",
        ]
    }

    report_path = RAW_DIR / "data_acquisition_report.json"
    # Convert numpy types for JSON serialization
    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, (np.bool_,)):
                return bool(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super().default(obj)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, cls=NpEncoder)
    print(f"\n报告已保存: {report_path}")

    return report


# ============================================================
# 7. 数字经济指数构建 (基于已有变量)
# ============================================================
def construct_digital_economy_index(panel):
    """
    使用已有变量构建数字经济综合指数 (熵值法)。
    参考: 赵涛等 (2020), 管理世界

    维度:
    1. 数字基础设施: 互联网普及率, 移动电话普及率
    2. 数字产业化: 数字普惠金融指数 (DIF)
    3. 产业数字化: 已有 DE 指数
    """
    print("\n" + "=" * 70)
    print("数字经济指数构建")
    print("=" * 70)

    # 如果所有子指标都完整, 可以构建综合指数
    available = panel[["internet_penetration", "mobile_phone_penetration",
                        "digital_finance_index"]].dropna()
    print(f"  可用于构建指数的完整观测值: {len(available)}/{len(panel)}")

    if len(available) > 0:
        print("  已有 DE 指数可供使用 (来自 Figshare 论文作者构建)")
        print("  如需自行构建, 可以使用 entropy_weight.py 脚本")

    return panel


# ============================================================
# 8. 主流程
# ============================================================
def main():
    print("=" * 70)
    print("中国省级面板数据自动采集系统 (2011-2023)")
    print("Digital Economy's Impact on Employment")
    print("=" * 70)

    # Step 1: 加载 Figshare 主数据
    figshare_df = load_figshare_data()
    if figshare_df is None:
        print("[FATAL] 无法获取 Figshare 主数据, 终止")
        sys.exit(1)

    # Step 2: 尝试 NBS API (可选)
    nbs_data = fetch_from_nbs_api()

    # Step 3: 尝试 World Bank API (备选)
    wb_data = fetch_from_world_bank()

    # Step 4: 编译面板数据
    panel = compile_panel_data(figshare_df)

    # Step 5: 构建数字经济指数
    panel = construct_digital_economy_index(panel)

    # Step 6: 保存数据
    csv_path = save_panel_data(panel)

    # Step 7: 生成报告
    report = generate_report(panel, wb_data)

    # Step 8: 打印概要统计
    print(f"\n{'='*70}")
    print("最终面板数据概要")
    print(f"{'='*70}")
    print(f"\n{panel[['province', 'year']].head(10).to_string(index=False)}")
    print(f"  ...")
    print(f"\n数值变量统计:")
    numeric_cols = panel.select_dtypes(include=[np.number]).columns
    print(panel[numeric_cols].describe().to_string())

    print(f"\n{'='*70}")
    print("数据采集完成!")
    print(f"{'='*70}")
    print(f"\n输出文件:")
    print(f"  1. {csv_path}")
    print(f"  2. {CLEAN_DIR / 'china_provincial_panel_2011_2023.xlsx'}")
    print(f"  3. {RAW_DIR / 'data_acquisition_report.json'}")
    print(f"\n注意: 部分变量标记为 '缺失', 需要手动补充:")
    print(f"  缺失变量详见上方报告")

    return panel


if __name__ == "__main__":
    panel = main()
