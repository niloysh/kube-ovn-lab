#!/usr/bin/env python3

import json
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


def create_gateway(tenant: str) -> dict:
    out = run(["./scripts/create_gateway.py", tenant])
    return json.loads(out)


def wait_for_gateway_pod(tenant: str, timeout_seconds: int = 180) -> str:
    pod_name = f"vpc-nat-gw-{tenant}-gw-0"
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            phase = run(
                [
                    "kubectl",
                    "get",
                    "pod",
                    "-n",
                    "kube-system",
                    pod_name,
                    "-o",
                    "jsonpath={.status.phase}",
                ]
            ).strip()

            if phase == "Running":
                return pod_name
        except RuntimeError:
            pass

        time.sleep(2)

    raise RuntimeError(f"timed out waiting for gateway pod {pod_name}")


def create_eip_fip(tenant: str) -> dict:
    out = run(["./scripts/create_eip_fip.py", tenant])
    return json.loads(out)


def patch_workload(tenant: str) -> dict:
    out = run(["./scripts/patch_external_routing.py", tenant])
    return json.loads(out)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <tenant>", file=sys.stderr)
        sys.exit(1)

    tenant = sys.argv[1]

    try:
        print(f"[{tenant}] creating gateway...")
        create_gateway(tenant)

        print(f"[{tenant}] waiting for gateway pod...")
        gateway_pod = wait_for_gateway_pod(tenant)

        print(f"[{tenant}] creating EIP/FIP...")
        eip_data = create_eip_fip(tenant)

        print(f"[{tenant}] patching workload...")
        patch_workload(tenant)

        print(json.dumps({
            "tenant": tenant,
            "gateway_name": f"{tenant}-gw",
            "gateway_pod": gateway_pod,
            "gateway_ip": eip_data["gateway_ip"],
            "requested_eip": eip_data["requested_eip"],
            "actual_eip": eip_data["actual_eip"],
            "internal_ip": eip_data["internal_ip"],
            "status": "external-enabled"
        }, indent=2))

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()