import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import pandas as pd
from export_logs import export_logs_to_csv
from correlation import analyze_logs
import json


class DatePickerApp:
    def __init__(self, root, logs_file):
        self.root = root
        self.logs_file = logs_file
        self.root.title("蓝屏日志分析器")

        # 创建标签页
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # 日期选择页面
        self.date_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.date_frame, text="选择日期")

        # 分析结果页面
        self.result_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.result_frame, text="分析结果")

        self.setup_date_selection()
        self.setup_result_view()

        # 存储选择的日期
        self.blue_screen_dates = []
        self.normal_dates = []

    def setup_date_selection(self):
        # 蓝屏日期选择
        blue_screen_frame = ttk.LabelFrame(self.date_frame, text="蓝屏日期", padding=10)
        blue_screen_frame.pack(fill="x", padx=10, pady=5)

        self.blue_screen_cal = DateEntry(
            blue_screen_frame,
            width=12,
            background="darkblue",
            foreground="white",
            borderwidth=2,
        )
        self.blue_screen_cal.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            blue_screen_frame,
            text="添加日期",
            command=lambda: self.add_date("blue_screen"),
        ).pack(side=tk.LEFT, padx=5)

        self.blue_screen_list = tk.Text(blue_screen_frame, height=3, width=30)
        self.blue_screen_list.pack(fill="x", padx=5, pady=5)

        # 正常日期选择
        normal_frame = ttk.LabelFrame(self.date_frame, text="正常运行日期", padding=10)
        normal_frame.pack(fill="x", padx=10, pady=5)

        self.normal_cal = DateEntry(
            normal_frame,
            width=12,
            background="darkblue",
            foreground="white",
            borderwidth=2,
        )
        self.normal_cal.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            normal_frame, text="添加日期", command=lambda: self.add_date("normal")
        ).pack(side=tk.LEFT, padx=5)

        self.normal_list = tk.Text(normal_frame, height=3, width=30)
        self.normal_list.pack(fill="x", padx=5, pady=5)

        # 控制按钮
        control_frame = ttk.Frame(self.date_frame)
        control_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(control_frame, text="清除所有日期", command=self.clear_dates).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(control_frame, text="开始分析", command=self.on_submit).pack(
            side=tk.LEFT, padx=5
        )

    def setup_result_view(self):
        # 创建结果显示的文本框，使用带滚动条的文本框
        self.result_text = tk.Text(self.result_frame, wrap=tk.WORD, height=30)
        scrollbar = ttk.Scrollbar(
            self.result_frame, orient="vertical", command=self.result_text.yview
        )
        self.result_text.configure(yscrollcommand=scrollbar.set)

        # 使用grid布局来确保滚动条紧贴文本框
        self.result_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # 配置grid权重使文本框能够扩展
        self.result_frame.grid_columnconfigure(0, weight=1)
        self.result_frame.grid_rowconfigure(0, weight=1)

    def add_date(self, date_type):
        if date_type == "blue_screen":
            cal = self.blue_screen_cal
            date_list = self.blue_screen_dates
            text_widget = self.blue_screen_list
        else:
            cal = self.normal_cal
            date_list = self.normal_dates
            text_widget = self.normal_list

        selected_date = cal.get_date()
        if selected_date not in date_list:
            date_list.append(selected_date)
            text_widget.delete(1.0, tk.END)
            text_widget.insert(
                tk.END, ", ".join(d.strftime("%Y-%m-%d") for d in date_list)
            )

    def clear_dates(self):
        self.blue_screen_dates = []
        self.normal_dates = []
        self.blue_screen_list.delete(1.0, tk.END)
        self.normal_list.delete(1.0, tk.END)

    def format_event_info(self, event):
        """格式化单个事件信息"""
        info = []
        info.append(f"事件描述: {event['description']}")
        if "source" in event:
            info.append(f"事件来源: {event['source']}")
            info.append(f"事件ID: {event['event_id']}")
            info.append(f"事件类型: {event['event_type']}")
        if "count" in event:
            info.append(f"出现次数: {event['count']}")
        if "probability_ratio" in event:
            info.append(f"概率提升倍数: {event['probability_ratio']:.2f}")
        if "bluescreen_count" in event:
            info.append(f"蓝屏日期出现次数: {event['bluescreen_count']}")
            info.append(f"正常日期出现次数: {event['normal_count']}")
        return "\n".join(info)

    def display_results(self, results):
        """在结果页面显示分析结果"""
        self.result_text.delete(1.0, tk.END)

        # 显示最具指示性的事件
        self.result_text.insert(tk.END, "=== 最可能导致蓝屏的事件 ===\n\n")
        for event in results["indicative_events"]:
            self.result_text.insert(tk.END, self.format_event_info(event) + "\n\n")

        # 显示蓝屏日期最常见的事件
        self.result_text.insert(tk.END, "\n=== 蓝屏日期最常见的事件 ===\n\n")
        for event in results["top_bluescreen_events"]:
            self.result_text.insert(tk.END, self.format_event_info(event) + "\n\n")

        # 显示事件类型分布
        self.result_text.insert(tk.END, "\n=== 事件类型分布 ===\n")
        for label, type_dist in results["event_type_distribution"].items():
            self.result_text.insert(tk.END, f"\n{label}:\n")
            for event_type, count in type_dist.items():
                self.result_text.insert(tk.END, f"  {event_type}: {count}\n")

        # 显示每个日期的统计信息
        self.result_text.insert(tk.END, "\n=== 每日事件统计 ===\n")
        for date, count in results["date_statistics"]["event_counts"].items():
            self.result_text.insert(tk.END, f"\n{date} 的事件统计:\n")
            self.result_text.insert(tk.END, f"总事件数: {count}\n")

            # 显示事件类型分布
            self.result_text.insert(tk.END, "事件类型分布:\n")
            for event_type, type_count in results["date_statistics"]["event_types"][
                date
            ].items():
                self.result_text.insert(tk.END, f"  {event_type}: {type_count}\n")

        # 切换到结果标签页
        self.notebook.select(self.result_frame)

    def on_submit(self):
        if not self.blue_screen_dates or not self.normal_dates:
            messagebox.showwarning("警告", "请至少选择一个蓝屏日期和一个正常运行日期")
            return

        try:
            # 运行分析
            results = analyze_logs(
                self.logs_file, self.blue_screen_dates, self.normal_dates
            )
            # 显示结果
            self.display_results(results)
        except Exception as e:
            messagebox.showerror("错误", f"分析过程中发生错误：{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    export_logs_to_csv("windows_logs.csv")
    app = DatePickerApp(root, "windows_logs.csv")
    root.mainloop()
