#!/usr/bin/env python3

import subprocess
import sys
import time


def run(cmd, input_data=None):
    result = subprocess.run(
        cmd,
        input=input_data,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed: {' '.join(cmd)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result.stdout


def apply_file(path: str) -> None:
    run(["kubectl", "apply", "-f", path])


def wait_for_namespace(namespace: str, timeout_seconds: int = 60) -> None:
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            phase = run(
                [
                    "kubectl",
                    "get",
                    "ns",
                    namespace,
                    "-o",
                    "jsonpath={.status.phase}",
                ]
            ).strip()

            if phase == "Active":
                return
        except RuntimeError:
            pass

        time.sleep(2)

    raise RuntimeError(f"timed out waiting for namespace {namespace}")


def wait_for_rollout(namespace: str, deployment: str, timeout_seconds: int = 180) -> None:
    run(
        [
            "kubectl",
            "rollout",
            "status",
            f"deployment/{deployment}",
            "-n",
            namespace,
            f"--timeout={timeout_seconds}s",
        ]
    )


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <tenant>", file=sys.stderr)
        sys.exit(1)

    tenant = sys.argv[1]

    base_file = f"tenants/{tenant}/base.yaml"
    workloads_file = f"tenants/{tenant}/workloads.yaml"

    try:
        print(f"[{tenant}] applying base resources...")
        apply_file(base_file)

        print(f"[{tenant}] waiting for namespace...")
        wait_for_namespace(tenant)

        print(f"[{tenant}] applying workloads...")
        apply_file(workloads_file)

        print(f"[{tenant}] waiting for app-a rollout...")
        wait_for_rollout(tenant, "app-a")

        print(f"[{tenant}] waiting for app-b rollout...")
        wait_for_rollout(tenant, "app-b")

        print(f"[{tenant}] tenant created successfully")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()