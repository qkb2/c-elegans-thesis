import subprocess
import threading
import time
import psutil
import pandas as pd
import argparse

from pynvml import (
    nvmlInit,
    nvmlDeviceGetHandleByIndex,
    nvmlDeviceGetComputeRunningProcesses,
)


class MemoryProfiler:
    def __init__(
        self,
        root_pid,
        interval=10,
        output_file=None,
        gpu_index=0,
    ):
        self.root_pid = root_pid
        self.interval = interval
        self.output_file = output_file

        self.root = psutil.Process(root_pid)

        self.running = False
        self.records = []

        self.start_time = None
        self.end_time = None

        # GPU init
        nvmlInit()
        self.gpu = nvmlDeviceGetHandleByIndex(gpu_index)

    def _get_process_tree(self):
        try:
            return [self.root] + self.root.children(recursive=True)
        except psutil.NoSuchProcess:
            return []

    def _get_gpu_mem_mb(self, pids):
        total = 0.0

        try:
            gpu_procs = nvmlDeviceGetComputeRunningProcesses(self.gpu)
            pid_set = set(pids)

            for p in gpu_procs:
                if p.pid in pid_set:
                    total += p.usedGpuMemory / 1024 / 1024
        except Exception:
            pass

        return total

    def _sample(self):
        while self.running:
            ts = time.time()

            procs = self._get_process_tree()

            ram_mb = 0.0
            pids = []

            for p in procs:
                try:
                    ram_mb += p.memory_info().rss / 1024 / 1024
                    pids.append(p.pid)
                except Exception:
                    continue

            gpu_mb = self._get_gpu_mem_mb(pids)

            self.records.append(
                {
                    "timestamp": ts,
                    "ram_mb": ram_mb,
                    "gpu_mb": gpu_mb,
                }
            )

            time.sleep(self.interval)

    def start(self):
        self.start_time = time.time()
        self.running = True

        self.thread = threading.Thread(target=self._sample)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.end_time = time.time()

        if self.thread:
            self.thread.join()

        df = pd.DataFrame(self.records)

        if self.output_file:
            df.to_csv(self.output_file, index=False)

        runtime_sec = self.end_time - self.start_time

        summary = {
            "runtime_sec": runtime_sec,
            "avg_ram_mb": df["ram_mb"].mean(),
            "max_ram_mb": df["ram_mb"].max(),
            "avg_gpu_mb": df["gpu_mb"].mean(),
            "max_gpu_mb": df["gpu_mb"].max(),
        }

        print("\n=== Memory Profiling Summary ===\n")
        print(f"Root PID: {self.root_pid}")
        print(f"Runtime: {runtime_sec:.2f} sec ({runtime_sec / 60:.2f} min)")
        print(f"Avg RAM: {summary['avg_ram_mb']:.2f} MB")
        print(f"Max RAM: {summary['max_ram_mb']:.2f} MB")
        print(f"Avg GPU: {summary['avg_gpu_mb']:.2f} MB")
        print(f"Max GPU: {summary['max_gpu_mb']:.2f} MB")

        return df, summary


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--interval",
        type=float,
        default=10,
        help="Sampling interval in seconds",
    )

    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Output CSV file",
    )

    parser.add_argument(
        "--max-minutes",
        type=float,
        default=None,
        help="Stop profiling after N minutes",
    )

    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to run",
    )

    args = parser.parse_args()

    if not args.command:
        raise ValueError("No command provided")

    print("Running:", " ".join(args.command))

    proc = subprocess.Popen(args.command)

    profiler = MemoryProfiler(
        root_pid=proc.pid,
        interval=args.interval,
        output_file=args.csv,
    )

    profiler.start()

    try:
        if args.max_minutes is None:
            proc.wait()
        else:
            try:
                proc.wait(timeout=args.max_minutes * 60)
            except subprocess.TimeoutExpired:
                print(f"\nProfiling limit reached ({args.max_minutes} min)")

    finally:
        profiler.stop()
        proc.kill()


if __name__ == "__main__":
    main()
