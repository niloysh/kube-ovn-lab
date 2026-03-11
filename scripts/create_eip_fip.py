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


def allocate_ip(tenant: str) -> dict:
    out = run(["./scripts/allocate_eip.py", tenant])
    return json.loads(out)


def apply_yaml(yaml_text: str) -> None:
    run(["kubectl", "apply", "-f", "-"], input_data=yaml_text)


def get_actual_eip(name: str) -> str:
    return run(
        ["kubectl", "get", "iptables-eip", name, "-o", "jsonpath={.spec.v4ip}"]
    ).strip()


def wait_for_eip_object(name: str, timeout_seconds: int = 60) -> str:
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            ip = get_actual_eip(name)
            if ip:
                return ip
        except Exception:
            pass
        time.sleep(2)

    raise RuntimeError(f"timed out waiting for iptables-eip/{name} to appear")


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <tenant>", file=sys.stderr)
        sys.exit(1)

    tenant = sys.argv[1]

    try:
        alloc = allocate_ip(tenant)

        requested_eip = alloc["allocated_eip"]
        gateway_ip = alloc["gateway_ip"]

        gw = f"{tenant}-gw"
        eip_name = f"{tenant}-eip"
        fip_name = f"{tenant}-fip-app-a"
        internal_ip = "172.30.0.2"

        manifest = f"""\
apiVersion: kubeovn.io/v1
kind: IptablesEIP
metadata:
  name: {eip_name}
spec:
  natGwDp: {gw}
  externalSubnet: ovn-vpc-external-network
  v4ip: {requested_eip}
---
apiVersion: kubeovn.io/v1
kind: IptablesFIPRule
metadata:
  name: {fip_name}
spec:
  eip: {eip_name}
  internalIp: {internal_ip}
"""

        apply_yaml(manifest)

        actual_eip = wait_for_eip_object(eip_name)

        print(json.dumps({
            "tenant": tenant,
            "gateway_ip": gateway_ip,
            "requested_eip": requested_eip,
            "actual_eip": actual_eip,
            "internal_ip": internal_ip,
            "eip_name": eip_name,
            "fip_name": fip_name
        }))

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()