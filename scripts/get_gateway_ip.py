#!/usr/bin/env python3

import subprocess
import sys
import re
import json


EXTERNAL_PREFIX = "10.10.10."


def run(cmd):
    return subprocess.check_output(cmd, text=True)


def get_gateway_pod(tenant):
    out = run(["kubectl", "get", "pods", "-n", "kube-system", "-o", "name"])

    for line in out.splitlines():
        if f"vpc-nat-gw-{tenant}-gw-" in line:
            return line.split("/")[-1]

    raise RuntimeError(f"No gateway pod found for tenant {tenant}")


def get_external_ip(pod):
    out = run([
        "kubectl",
        "exec",
        "-n",
        "kube-system",
        pod,
        "--",
        "ip",
        "-4",
        "addr"
    ])

    for line in out.splitlines():
        match = re.search(r"inet (10\.10\.10\.\d+)", line)
        if match:
            return match.group(1)

    raise RuntimeError("No external IP found")


def main():
    if len(sys.argv) != 2:
        print("Usage: get_gateway_ip.py <tenant>", file=sys.stderr)
        sys.exit(1)

    tenant = sys.argv[1]

    pod = get_gateway_pod(tenant)
    ip = get_external_ip(pod)

    result = {
        "tenant": tenant,
        "gateway_pod": pod,
        "gateway_ip": ip
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()