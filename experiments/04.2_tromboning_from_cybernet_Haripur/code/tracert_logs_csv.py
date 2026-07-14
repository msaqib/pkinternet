#!/usr/bin/env python3

import csv
import re
from pathlib import Path

# ==========================================================
# Configuration
# ==========================================================

LOG_FILE = "202_63_203_113.log"

# ==========================================================


timestamp_pattern = re.compile(
    r"Traceroute Timestamp\s*:\s*(.+)"
)

# Matches Windows tracert output with -d
hop_pattern = re.compile(
    r"^\s*(\d+)\s+"
    r"(<\d+|\d+)\s*ms\s+"
    r"(<\d+|\d+)\s*ms\s+"
    r"(<\d+|\d+)\s*ms\s+"
    r"([\d\.]+)"
)


def parse_log(filename):

    traces = []

    current_trace = None

    with open(filename, encoding="utf-8") as f:

        for line in f:

            m = timestamp_pattern.search(line)

            if m:
                if current_trace:
                    traces.append(current_trace)

                current_trace = {
                    "timestamp": m.group(1).strip(),
                    "hops": []
                }

                continue

            if current_trace is None:
                continue

            m = hop_pattern.match(line)

            if m:

                hop_no = int(m.group(1))

                lat1 = m.group(2)
                lat2 = m.group(3)
                lat3 = m.group(4)
                ip = m.group(5)

                current_trace["hops"].append(
                    (hop_no, ip, lat1, lat2, lat3)
                )

    if current_trace:
        traces.append(current_trace)

    return traces


def write_csv(traces, output_csv):

    max_hops = max(len(t["hops"]) for t in traces)

    header = ["Timestamp"]

    for hop in range(1, max_hops + 1):
        header.extend([
            f"Hop{hop}_IP",
            f"Hop{hop}_Lat1",
            f"Hop{hop}_Lat2",
            f"Hop{hop}_Lat3",
        ])

    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:

        writer = csv.writer(csvfile)

        writer.writerow(header)

        for trace in traces:

            row = [trace["timestamp"]]

            for _, ip, l1, l2, l3 in trace["hops"]:
                row.extend([ip, l1, l2, l3])

            while len(row) < len(header):
                row.append("")

            writer.writerow(row)


def main():

    traces = parse_log(LOG_FILE)

    output = Path(LOG_FILE).with_suffix(".csv")

    write_csv(traces, output)

    print(f"Parsed {len(traces)} traceroutes.")

    print(f"CSV written to {output}")


if __name__ == "__main__":
    main()