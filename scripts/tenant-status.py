#!/usr/bin/env python3

import subprocess
import sys


def run(cmd):
    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def print_cmd_output(cmd):
    rc, out, err = run(cmd)
    if rc == 0 and out:
        print(out)
    elif err:
        print(err)
    else:
        print("(none)")


def get_gateway_pod_name(tenant: str) -> str | None:
    rc, out, _ = run(["kubectl", "get", "pods", "-n", "kube-system", "-o", "name"])
    if rc != 0:
        return None

    for line in out.splitlines():
        name = line.split("/")[-1]
        if f"vpc-nat-gw-{tenant}-gw-" in name:
            return name

    return None


def get_gateway_ip(tenant: str) -> str | None:
    rc, out, _ = run(["./scripts/get_gateway_ip.py", tenant])
    if rc != 0:
        return None

    # simple parse without json dependency
    # expected output is JSON with "gateway_ip": "..."
    marker = '"gateway_ip":'
    if marker not in out:
        return None

    tail = out.split(marker, 1)[1].strip()
    if not tail.startswith('"'):
        return None

    return tail.split('"')[1]


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <tenant>", file=sys.stderr)
        sys.exit(1)

    tenant = sys.argv[1]

    print(f"Tenant: {tenant}")

    section("Namespace")
    print_cmd_output(["kubectl", "get", "ns", tenant])

    section("Workloads")
    print_cmd_output(["kubectl", "get", "deploy", "-n", tenant])

    section("Pods")
    print_cmd_output(["kubectl", "get", "pods", "-n", tenant, "-o", "wide"])

    section("Subnet / VPC")
    print_cmd_output(["kubectl", "get", "subnet", f"attachnet-{tenant}"])
    print_cmd_output(["kubectl", "get", "vpc", f"{tenant}-vpc"])

    section("Gateway")
    print_cmd_output(["kubectl", "get", "vpc-nat-gateway", f"{tenant}-gw"])

    gateway_pod = get_gateway_pod_name(tenant)
    if gateway_pod:
        print()
        print(f"Gateway pod: {gateway_pod}")
        print_cmd_output(["kubectl", "get", "pod", "-n", "kube-system", gateway_pod, "-o", "wide"])

        gateway_ip = get_gateway_ip(tenant)
        if gateway_ip:
            print(f"Gateway external IP: {gateway_ip}")

    section("External")
    print_cmd_output(["kubectl", "get", "iptables-eip", f"{tenant}-eip"])
    print_cmd_output(["kubectl", "get", "iptables-fip-rule", f"{tenant}-fip-app-a"])

    section("Quick checks")
    print_cmd_output(["kubectl", "rollout", "status", "deployment/app-a", "-n", tenant, "--timeout=5s"])
    print_cmd_output(["kubectl", "rollout", "status", "deployment/app-b", "-n", tenant, "--timeout=5s"])


if __name__ == "__main__":
    main()