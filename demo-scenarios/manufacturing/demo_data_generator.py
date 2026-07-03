"""
🎯 Feishu + AI 制造业演示场景
制造业 Demo 数据生成器 - 快速填充演示数据到 Bitable
"""

import json
import random
import datetime
from typing import Any

# =====================
# 1️⃣ 生产异常告警场景
# =====================

def generate_alert_scenario() -> dict[str, Any]:
    """生成设备异常告警演示数据"""
    equipment = [
        {"name": "注塑机-A3", "type": "注塑设备", "location": "A车间"},
        {"name": "冲压机-B1", "type": "冲压设备", "location": "B车间"},
        {"name": "焊接机器人-C2", "type": "焊接设备", "location": "C车间"},
        {"name": "CNC-D5", "type": "数控机床", "location": "D车间"},
        {"name": "空压机-E1", "type": "动力设备", "location": "动力站"},
    ]
    alert_types = [
        "温度异常", "振动超标", "压力异常", "电流过载",
        "润滑油位低", "刀具磨损", "精度偏差", "通讯中断"
    ]
    severity = ["严重", "中等", "轻微"]
    status = ["待处理", "处理中", "已闭环"]

    alerts = []
    for i in range(3):
        eq = random.choice(equipment)
        alerts.append({
            "id": f"ALT-{datetime.date.today().strftime('%Y%m%d')}-{i+1:03d}",
            "equipment": eq["name"],
            "type": eq["type"],
            "location": eq["location"],
            "alert_type": random.choice(alert_types),
            "severity": random.choice(severity),
            "time": (datetime.datetime.now() - datetime.timedelta(minutes=random.randint(5, 120))).strftime("%Y-%m-%d %H:%M"),
            "status": random.choice(status),
            "value": f"{random.uniform(80, 150):.1f}",
            "threshold": "100.0",
            "description": f"{eq['name']} {random.choice(alert_types)}，当前值超出阈值"
        })

    return {
        "scenario": "生产异常告警",
        "description": "设备传感器检测到异常，自动触发飞书告警并启动 Agent 分析流程",
        "data": alerts,
        "workflow": [
            "1️⃣ 传感器采集设备数据 → Bitable 实时记录",
            "2️⃣ 异常触发 → 飞书群聊自动告警",
            "3️⃣ Agent 查询历史数据和维修记录",
            "4️⃣ Agent 分析根因 → 生成处理建议",
            "5️⃣ 飞书文档自动创建维修工单",
            "6️⃣ 闭环跟踪 → 数据沉淀为知识库"
        ]
    }


# =====================
# 2️⃣ 设备巡检场景
# =====================

def generate_inspection_scenario() -> dict[str, Any]:
    """生成设备巡检演示数据"""
    checkpoints = [
        "设备运行温度", "润滑油状态", "皮带松紧度",
        "电气接线", "安全防护装置", "仪表读数",
        "异响检查", "振动检测", "滤网清洁", "接地检查"
    ]
    results = ["正常", "正常", "正常", "正常", "正常", "异常"]

    records = []
    for i in range(5):
        date = datetime.date.today() - datetime.timedelta(days=i)
        items = []
        abnormal_count = 0
        for cp in random.sample(checkpoints, 4):
            r = random.choice(results)
            if r == "异常":
                abnormal_count += 1
            items.append({"checkpoint": cp, "result": r})

        records.append({
            "date": date.strftime("%Y-%m-%d"),
            "inspector": random.choice(["张三", "李四", "王五", "赵六"]),
            "location": random.choice(["A车间", "B车间", "C车间", "D车间"]),
            "total_items": len(items),
            "abnormal": abnormal_count,
            "pass": "是" if abnormal_count == 0 else "否",
            "details": items
        })

    return {
        "scenario": "设备巡检管理",
        "description": "巡检员用飞书移动端完成设备巡检，数据自动录入多维表格",
        "data": records,
        "workflow": [
            "1️⃣ 巡检员扫描设备二维码 → 打开巡检表单",
            "2️⃣ 逐项检查并拍照上传（飞书文档）",
            "3️⃣ Agent 自动识别照片内容并结构化录入 Bitable",
            "4️⃣ 异常项自动创建整改任务",
            "5️⃣ 临近到期自动催办"
        ]
    }


# =====================
# 3️⃣ 质量管控场景
# =====================

def generate_quality_scenario() -> dict[str, Any]:
    """生成质量管控演示数据"""
    products = ["A型连接器", "B型底座", "C型外壳", "D型轴承", "E型密封圈"]
    defects = ["尺寸偏差", "表面划伤", "毛刺", "变形", "色差", "装配间隙过大"]

    records = []
    for i in range(10):
        product = random.choice(products)
        date = datetime.date.today() - datetime.timedelta(days=random.randint(0, 30))
        total = random.randint(500, 2000)
        defective = random.randint(0, 30)
        defect_type = random.choice(defects) if defective > 0 else "无"

        records.append({
            "date": date.strftime("%Y-%m-%d"),
            "product": product,
            "batch": f"BATCH-{date.strftime('%Y%m%d')}-{random.randint(1,5):02d}",
            "total_qty": total,
            "defective_qty": defective,
            "yield_rate": f"{(1 - defective/max(total,1))*100:.1f}%",
            "main_defect": defect_type,
            "inspector": random.choice(["质检A组", "质检B组", "质检C组"])
        })

    # 计算趋势
    yield_rates = [float(r["yield_rate"].rstrip("%")) for r in records]

    return {
        "scenario": "质量管控看板",
        "description": "生产质量数据实时汇总到 Bitable 仪表盘，AI 分析异常趋势",
        "data": records,
        "avg_yield_rate": f"{sum(yield_rates)/len(yield_rates):.1f}%",
        "trend": "上升" if yield_rates[-1] > yield_rates[0] else "下降",
        "workflow": [
            "1️⃣ 质检员录入检测数据 → Bitable 实时更新",
            "2️⃣ 仪表盘自动汇总良品率趋势",
            "3️⃣ Agent 发现良品率下降 → 自动分析根因",
            "4️⃣ Agent 关联设备巡检记录 → 定位问题工位",
            "5️⃣ 生成质量改进报告（飞书文档）",
            "6️⃣ 推送至质量改进群"
        ]
    }


# =====================
# 打印所有场景
# =====================

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 Feishu 制造业 AI Demo 场景数据")
    print("=" * 60)

    print("\n📊 场景 1: 生产异常告警")
    s1 = generate_alert_scenario()
    print(f"   描述: {s1['description']}")
    print(f"   数据条数: {len(s1['data'])}")
    print(f"   工作流:")
    for step in s1['workflow']:
        print(f"     {step}")

    print("\n📊 场景 2: 设备巡检管理")
    s2 = generate_inspection_scenario()
    print(f"   描述: {s2['description']}")
    print(f"   数据条数: {len(s2['data'])}")

    print("\n📊 场景 3: 质量管控看板")
    s3 = generate_quality_scenario()
    print(f"   描述: {s3['description']}")
    print(f"   平均良品率: {s3['avg_yield_rate']}")
    print(f"   趋势: {s3['trend']}")

    print("\n✅ Demo 数据已就绪，可直接导入 Bitable")

    # 输出 JSON 格式供导入 Bitable
    with open("demo_alert_data.json", "w") as f:
        json.dump(s1, f, ensure_ascii=False, indent=2)
    with open("demo_quality_data.json", "w") as f:
        json.dump(s3, f, ensure_ascii=False, indent=2)
    print("\n💾 数据已导出至 demo_alert_data.json / demo_quality_data.json")
