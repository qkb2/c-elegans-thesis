import psutil
import subprocess
import time
import json
import argparse
import signal
from datetime import datetime

try:
    import GPUtil

    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False


def monitor_process(cmd, duration, interval, output):
    start_time = time.time()
    timestamps = []

    cpu_samples = []
    ram_samples = []
    gpu_samples = []

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ps_proc = psutil.Process(proc.pid)

    actual_runtime = 0.0
    exited_early = False

    try:
        while True:
            now = time.time()
            elapsed = now - start_time

            if elapsed >= duration:
                break

            if proc.poll() is not None:
                exited_early = True
                break

            try:
                cpu = ps_proc.cpu_percent(interval=None)
                ram = ps_proc.memory_info().rss / (1024**2)  # MB

                cpu_samples.append(cpu)
                ram_samples.append(ram)

                if GPU_AVAILABLE:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu_samples.append(gpus[0].load * 100)

                timestamps.append(elapsed)

            except psutil.NoSuchProcess:
                exited_early = True
                break

            time.sleep(interval)

    finally:
        actual_runtime = time.time() - start_time

        if proc.poll() is None:
            proc.send_signal(signal.SIGTERM)

    result = {
        "command": cmd,
        "start_time": datetime.fromtimestamp(start_time).isoformat(),
        "requested_duration_sec": duration,
        "actual_runtime_sec": round(actual_runtime, 3),
        "exited_early": exited_early,
        "sampling_interval_sec": interval,
        "cpu_percent": {
            "avg": sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0,
            "max": max(cpu_samples) if cpu_samples else 0,
        },
        "ram_mb": {
            "avg": sum(ram_samples) / len(ram_samples) if ram_samples else 0,
            "max": max(ram_samples) if ram_samples else 0,
        },
        "gpu_percent": None
        if not gpu_samples
        else {"avg": sum(gpu_samples) / len(gpu_samples), "max": max(gpu_samples)},
    }

    with open(output, "w") as f:
        json.dump(result, f, indent=4)

    print(f"Results written to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cmd", nargs="+", required=True, help="Executable + args")
    parser.add_argument(
        "--duration", type=int, required=True, help="Observation time in seconds"
    )
    parser.add_argument(
        "--interval", type=float, default=1.0, help="Sampling interval (seconds)"
    )
    parser.add_argument("--output", default="usage.json", help="Output JSON file")

    args = parser.parse_args()

    monitor_process(
        cmd=args.cmd, duration=args.duration, interval=args.interval, output=args.output
    )
