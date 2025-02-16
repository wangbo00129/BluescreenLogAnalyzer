import csv
import win32evtlog
import win32evtlogutil
import win32con


def export_logs_to_csv(output_file):
    # Open the System event log
    server = "localhost"
    logtype = "System"
    hand = win32evtlog.OpenEventLog(server, logtype)
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    total = win32evtlog.GetNumberOfEventLogRecords(hand)

    all_fields = [
        "RecordNumber",
        "EventID",
        "TimeGenerated",
        "SourceName",
        "EventType",
        "EventCategory",
        "Description",  
        "StringInserts",
        "ComputerName",
    ]

    event_types = {
        win32con.EVENTLOG_AUDIT_FAILURE: "审核失败",
        win32con.EVENTLOG_AUDIT_SUCCESS: "审核成功",
        win32con.EVENTLOG_INFORMATION_TYPE: "信息",
        win32con.EVENTLOG_WARNING_TYPE: "警告",
        win32con.EVENTLOG_ERROR_TYPE: "错误"
    }

    # Open the CSV file for writing
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=all_fields)
        writer.writeheader()

        # Read and write each event log record
        events = win32evtlog.ReadEventLog(hand, flags, 0)
        while events:
            for event in events:
                # 获取格式化的事件描述
                try:
                    description = win32evtlogutil.SafeFormatMessage(event, logtype)
                except Exception as e:
                    description = f"无法获取描述: {str(e)}"

                event_data = {
                    "RecordNumber": event.RecordNumber,
                    "EventID": event.EventID & 0xFFFF,  
                    "TimeGenerated": event.TimeGenerated,
                    "SourceName": event.SourceName,
                    "EventType": event_types.get(event.EventType, "未知"),
                    "EventCategory": event.EventCategory,
                    "Description": description,
                    "StringInserts": event.StringInserts if event.StringInserts else [],
                    "ComputerName": event.ComputerName,
                }
                
                writer.writerow(event_data)
            events = win32evtlog.ReadEventLog(hand, flags, 0)

    # Close the event log
    win32evtlog.CloseEventLog(hand)


if __name__ == "__main__":
    export_logs_to_csv("windows_logs.csv")
