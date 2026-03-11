#!/usr/bin/env python3

import json
import subprocess
import sys


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
    manifest = f"""\
apiVersion: kubeovn.io/v1
kind: VpcNatGateway
metadata:
  name: {tenant}-gw
spec:
  vpc: {tenant}-vpc
  subnet: attachnet-{tenant}
  lanIp: 172.30.0.254
  selector:
    - "kubernetes.io/os: linux"
  externalSubnets:
    - ovn-vpc-external-network
"""

    run(["kubectl", "apply", "-f", "-"], input_data=manifest)

    return {
        "tenant": tenant,
        "gateway_name": f"{tenant}-gw",
        "status": "created",
    }


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <tenant>", file=sys.stderr)
        sys.exit(1)

    tenant = sys.argv[1]

    try:
        result = create_gateway(tenant)
        print(json.dumps(result))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()