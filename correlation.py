import pandas as pd
import numpy as np
from collections import Counter
import math


def calculate_event_probability(
    description, blue_screen_logs, normal_logs, combined_logs
):
    """
    使用贝叶斯方法计算事件的指示性概率
    P(蓝屏|事件) = P(事件|蓝屏) * P(蓝屏) / P(事件)
    """
    # 计算先验概率 P(蓝屏)
    p_bluescreen = len(blue_screen_logs) / len(combined_logs)

    # 计算条件概率 P(事件|蓝屏)
    event_in_bluescreen = (blue_screen_logs["Description"] == description).sum()
    p_event_given_bluescreen = event_in_bluescreen / len(blue_screen_logs)

    # 计算事件的总体概率 P(事件)
    event_total = (combined_logs["Description"] == description).sum()
    p_event = event_total / len(combined_logs)

    # 使用贝叶斯公式计算后验概率 P(蓝屏|事件)
    if p_event == 0:
        return 0

    p_bluescreen_given_event = (p_event_given_bluescreen * p_bluescreen) / p_event

    # 计算信息增益（相对于先验概率的提升）
    information_gain = (
        p_bluescreen_given_event / p_bluescreen if p_bluescreen > 0 else 0
    )

    return information_gain


def analyze_logs(logs_file, blue_screen_dates, normal_dates):
    """
    分析事件日志，支持多个蓝屏日期和正常日期的对比
    :param logs_file: 日志文件路径
    :param blue_screen_dates: 蓝屏日期列表
    :param normal_dates: 正常日期列表
    :return: 包含分析结果的字典
    """
    # Load the logs and select specific columns
    logs_df = pd.read_csv(
        logs_file,
        usecols=[
            "EventID",
            "SourceName",
            "Description",
            "StringInserts",
            "TimeGenerated",
            "EventType",
        ],
    )
    logs_df["TimeGenerated"] = pd.to_datetime(logs_df["TimeGenerated"]).dt.date

    # Filter logs for the selected dates
    blue_screen_mask = logs_df["TimeGenerated"].isin(blue_screen_dates)
    normal_mask = logs_df["TimeGenerated"].isin(normal_dates)

    blue_screen_logs = logs_df[blue_screen_mask].copy()
    normal_logs = logs_df[normal_mask].copy()

    # Label the data
    blue_screen_logs.loc[:, "label"] = 1  # 1 for blue screen
    normal_logs.loc[:, "label"] = 0  # 0 for normal

    # Combine the datasets
    combined_logs = pd.concat([blue_screen_logs, normal_logs])

    # Preprocess the log descriptions
    combined_logs["Description"] = combined_logs["Description"].fillna("")
    combined_logs["Description"] = combined_logs["Description"].astype(str)

    # 分析事件描述的分布
    print("\n=== 事件描述分析 ===")

    # 1. 分析蓝屏日期的事件
    print("\n蓝屏日期最常见的事件:")
    blue_screen_descriptions = Counter(blue_screen_logs["Description"])
    for desc, count in blue_screen_descriptions.most_common(10):
        print(f"\n出现 {count} 次:")
        print(f"事件描述: {desc}")
        # 显示相关的事件信息
        events = blue_screen_logs[blue_screen_logs["Description"] == desc]
        if not events.empty:
            print(f"事件来源: {events['SourceName'].iloc[0]}")
            print(f"事件ID: {events['EventID'].iloc[0]}")
            print(f"事件类型: {events['EventType'].iloc[0]}")

    # 2. 分析正常日期的事件
    print("\n正常日期最常见的事件:")
    normal_descriptions = Counter(normal_logs["Description"])
    for desc, count in normal_descriptions.most_common(10):
        print(f"\n出现 {count} 次:")
        print(f"事件描述: {desc}")
        # 显示相关的事件信息
        events = normal_logs[normal_logs["Description"] == desc]
        if not events.empty:
            print(f"事件来源: {events['SourceName'].iloc[0]}")
            print(f"事件ID: {events['EventID'].iloc[0]}")
            print(f"事件类型: {events['EventType'].iloc[0]}")

    # 3. 使用贝叶斯分析找出最具指示性的事件
    print("\n=== 贝叶斯分析：最具蓝屏指示性的事件 ===")
    event_probabilities = []

    # 分析所有在蓝屏日期出现的事件
    for desc in blue_screen_descriptions:
        if pd.isna(desc):  # 跳过 nan 值
            continue
        prob = calculate_event_probability(
            desc, blue_screen_logs, normal_logs, combined_logs
        )
        if prob > 1:  # 只关注比随机更有指示性的事件
            event_probabilities.append((desc, prob))

    # 按指示性概率排序
    event_probabilities.sort(key=lambda x: x[1], reverse=True)

    # 显示最具指示性的事件
    print("\n以下事件最可能与蓝屏相关（数字表示相对于随机的可能性提升倍数）：")
    for desc, prob in event_probabilities[:10]:
        print(f"\n提升 {prob:.2f} 倍:")
        print(f"事件描述: {desc}")
        # 显示相关的事件信息
        events = blue_screen_logs[blue_screen_logs["Description"] == desc]
        if not events.empty:
            print(f"事件来源: {events['SourceName'].iloc[0]}")
            print(f"事件ID: {events['EventID'].iloc[0]}")
            print(f"事件类型: {events['EventType'].iloc[0]}")
            print(f"在蓝屏日期出现次数: {blue_screen_descriptions[desc]}")
            print(f"在正常日期出现次数: {normal_descriptions.get(desc, 0)}")

    # 4. 分析事件类型分布
    print("\n=== 事件类型分布 ===")
    event_type_dist = (
        combined_logs.groupby(["label", "EventType"]).size().unstack(fill_value=0)
    )
    event_type_dist.index = ["正常日期", "蓝屏日期"]
    print(event_type_dist)

    # 5. 分析事件来源分布
    print("\n=== 事件来源分布 ===")
    source_dist = (
        combined_logs.groupby(["label", "SourceName"]).size().unstack(fill_value=0)
    )
    source_dist.index = ["正常日期", "蓝屏日期"]
    print(source_dist)

    # 6. 显示每个日期的事件统计
    print("\n=== 每个日期的事件统计 ===")
    date_stats = (
        combined_logs.groupby("TimeGenerated")
        .agg(
            {
                "EventID": "count",
                "EventType": lambda x: x.value_counts().to_dict(),
                "SourceName": lambda x: x.value_counts().to_dict(),
            }
        )
        .round(2)
    )

    print("\n每个日期的事件数量:")
    print(date_stats["EventID"])

    print("\n每个日期的事件类型分布:")
    for date, type_dist in date_stats["EventType"].items():
        print(f"\n{date}:")
        for event_type, count in type_dist.items():
            print(f"  {event_type}: {count}")

    print("\n每个日期的事件来源分布:")
    for date, source_dist in date_stats["SourceName"].items():
        print(f"\n{date}:")
        for source, count in source_dist.items():
            print(f"  {source}: {count}")

    # 收集分析结果
    results = {
        "top_bluescreen_events": [],
        "indicative_events": [],
        "event_type_distribution": (
            event_type_dist.to_dict("index")
            if hasattr(event_type_dist, "to_dict")
            else event_type_dist
        ),
        "source_distribution": (
            source_dist.to_dict("index")
            if hasattr(source_dist, "to_dict")
            else source_dist
        ),
        "date_statistics": {
            "event_counts": (
                date_stats["EventID"].to_dict()
                if hasattr(date_stats["EventID"], "to_dict")
                else date_stats["EventID"]
            ),
            "event_types": (
                date_stats["EventType"].to_dict()
                if hasattr(date_stats["EventType"], "to_dict")
                else date_stats["EventType"]
            ),
            "event_sources": (
                date_stats["SourceName"].to_dict()
                if hasattr(date_stats["SourceName"], "to_dict")
                else date_stats["SourceName"]
            )
        }
    }

    # 收集蓝屏日期最常见事件
    for desc, count in blue_screen_descriptions.most_common(10):
        event_info = {
            "description": desc,
            "count": count
        }
        events = blue_screen_logs[blue_screen_logs["Description"] == desc]
        if not events.empty:
            event_info.update({
                "source": events['SourceName'].iloc[0],
                "event_id": events['EventID'].iloc[0],
                "event_type": events['EventType'].iloc[0]
            })
        results["top_bluescreen_events"].append(event_info)

    # 收集最具指示性的事件
    for desc, prob in event_probabilities[:10]:
        event_info = {
            "description": desc,
            "probability_ratio": prob
        }
        events = blue_screen_logs[blue_screen_logs["Description"] == desc]
        if not events.empty:
            event_info.update({
                "source": events['SourceName'].iloc[0],
                "event_id": events['EventID'].iloc[0],
                "event_type": events['EventType'].iloc[0],
                "bluescreen_count": blue_screen_descriptions[desc],
                "normal_count": normal_descriptions.get(desc, 0)
            })
        results["indicative_events"].append(event_info)

    return results


if __name__ == "__main__":
    # Example usage with multiple dates
    blue_screen_dates = [
        # pd.to_datetime("2025-02-15").date(),
        pd.to_datetime("2025-02-11").date(),
    ]
    normal_dates = [
        pd.to_datetime("2025-02-13").date(),
        pd.to_datetime("2025-02-14").date(),
    ]
    results = analyze_logs("windows_logs.csv", blue_screen_dates, normal_dates)
    print(results)
