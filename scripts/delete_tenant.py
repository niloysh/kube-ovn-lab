#!/usr/bin/env python3

import subprocess
import sys


def run(cmd):
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        print(result.stderr.strip())
    else:
        print(result.stdout.strip())


def delete_external_resources(tenant):

    print(f"[{tenant}] deleting FIP rules")
    run(["kubectl", "delete", "iptables-fip-rule", f"{tenant}-fip-app-a", "--ignore-not-found"])

    print(f"[{tenant}] deleting EIP")
    run(["kubectl", "delete", "iptables-eip", f"{tenant}-eip", "--ignore-not-found"])

    print(f"[{tenant}] deleting NAT gateway")
    run(["kubectl", "delete", "vpc-nat-gateway", f"{tenant}-gw", "--ignore-not-found"])


def delete_workloads(tenant):

    print(f"[{tenant}] deleting workloads")
    run(["kubectl", "delete", "-f", f"tenants/{tenant}/workloads.yaml", "--ignore-not-found"])


def delete_base(tenant):

    print(f"[{tenant}] deleting base resources")
    run(["kubectl", "delete", "-f", f"tenants/{tenant}/base.yaml", "--ignore-not-found"])


def delete_namespace(tenant):

    print(f"[{tenant}] deleting namespace")
    run(["kubectl", "delete", "ns", tenant, "--ignore-not-found"])


def main():

    if len(sys.argv) != 2:
        print("Usage: delete_tenant.py <tenant>")
        sys.exit(1)

    tenant = sys.argv[1]

    delete_external_resources(tenant)

    delete_workloads(tenant)

    delete_base(tenant)

    delete_namespace(tenant)

    print(f"[{tenant}] tenant deleted")


if __name__ == "__main__":
    main()