#103.4.103.85 (Sign In Pvt. Ltd.)
#103.121.121.28 (Logon Broadband)
#122.129.66.199 (Brain Telecommunication)
#202.63.203.113 (Cube XS)

#!/usr/bin/env python3

import subprocess
import platform
import time
from datetime import datetime
from pathlib import Path

# ==========================================================
# Configuration
# ==========================================================

IP_ADDRESSES = [
    "103.4.103.85",
    "103.121.121.28",
    "122.129.66.199",
    "202.63.203.113",
]

INTERVAL_MINUTES = 20

# ==========================================================


def traceroute_command(ip):
    """
    Returns the traceroute command appropriate for the current OS.
    """

    system = platform.system().lower()

    if system == "windows":
        return ["tracert", "-d", ip]
    else:
        # Linux/macOS
        return ["traceroute", "-n", ip]


def run_traceroute(ip):
    """
    Executes traceroute and returns its output.
    """

    try:
        result = subprocess.run(
            traceroute_command(ip),
            capture_output=True,
            text=True,
            timeout=300
        )

        return result.stdout + result.stderr

    except subprocess.TimeoutExpired:
        return "Traceroute timed out.\n"

    except Exception as e:
        return f"Error running traceroute: {e}\n"


def append_result(ip, output):
    """
    Appends traceroute output to the IP-specific log file.
    """

    logfile = Path(f"{ip.replace('.', '_')}.log")

    with logfile.open("a", encoding="utf-8") as f:

        f.write("\n")
        f.write("=" * 80 + "\n")
        f.write(f"Traceroute Timestamp : {datetime.now()}\n")
        f.write(f"Target IP            : {ip}\n")
        f.write("=" * 80 + "\n\n")

        f.write(output)

        if not output.endswith("\n"):
            f.write("\n")


def main():

    print("Traceroute monitor started.")
    print(f"Running every {INTERVAL_MINUTES} minute(s).\n")

    while True:

        start = datetime.now()

        print(f"[{start}] Starting traceroutes...")

        for ip in IP_ADDRESSES:

            print(f"  Tracing {ip}...")

            output = run_traceroute(ip)

            append_result(ip, output)

        finish = datetime.now()

        print(f"[{finish}] Cycle complete.\n")

        time.sleep(INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main()