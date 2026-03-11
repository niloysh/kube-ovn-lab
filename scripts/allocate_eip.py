#!/usr/bin/env python3

import subprocess
import sys
import re
import json


POOL_START = 81
POOL_END = 99
PREFIX = "10.10.10."


def run(cmd):
    return subprocess.check_output(cmd, text=True)


def get_gateway_ip(tenant):
    out = run(["./scripts/get_gateway_ip.py", tenant])
    data = json.loads(out)
    return data["gateway_ip"]


def get_existing_eips():
    try:
        out = run(["kubectl", "get", "iptables-eip", "-A", "--no-headers"])
    except subprocess.CalledProcessError:
        return []

    ips = []

    for line in out.splitlines():
        match = re.search(r"(10\.10\.10\.\d+)", line)
        if match:
            ips.append(match.group(1))

    return ips


def pick_ip(used):
    for i in range(POOL_START, POOL_END + 1):
        ip = f"{PREFIX}{i}"
        if ip not in used:
            return ip

    raise RuntimeError("No free IP in pool")


def main():

    if len(sys.argv) != 2:
        print("Usage: allocate_eip.py <tenant>", file=sys.stderr)
        sys.exit(1)

    tenant = sys.argv[1]

    gateway_ip = get_gateway_ip(tenant)
    existing_eips = get_existing_eips()

    used = set(existing_eips)
    used.add(gateway_ip)

    ip = pick_ip(used)

    result = {
        "tenant": tenant,
        "gateway_ip": gateway_ip,
        "existing_eips": existing_eips,
        "allocated_eip": ip
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()