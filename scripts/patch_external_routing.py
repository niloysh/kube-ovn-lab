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


def patch_workload_for_external(tenant: str) -> dict:
    patch = {
        "spec": {
            "template": {
                "spec": {
                    "initContainers": [
                        {
                            "name": "setup-routing",
                            "image": "nicolaka/netshoot",
                            "securityContext": {
                                "capabilities": {
                                    "add": ["NET_ADMIN"]
                                }
                            },
                            "command": [
                                "sh",
                                "-c",
                                "\n".join(
                                    [
                                        "set -eux",
                                        "ip -o -4 addr show dev net1",
                                        "ip -o -4 addr show dev net1 | grep -q '172.30.0.2/24'",
                                        "ip rule add from 172.30.0.2/32 table 100",
                                        "ip route add 172.30.0.0/24 dev net1 scope link table 100",
                                        "ip route add default via 172.30.0.254 dev net1 table 100",
                                        "ip rule show",
                                        "ip route show table 100",
                                    ]
                                ),
                            ],
                        }
                    ]
                }
            }
        }
    }

    run(
        [
            "kubectl",
            "patch",
            "deployment",
            "app-a",
            "-n",
            tenant,
            "--type",
            "merge",
            "-p",
            json.dumps(patch),
        ]
    )

    run(
        [
            "kubectl",
            "rollout",
            "status",
            "deployment/app-a",
            "-n",
            tenant,
            "--timeout=180s",
        ]
    )

    return {
        "tenant": tenant,
        "deployment": "app-a",
        "status": "patched",
    }


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <tenant>", file=sys.stderr)
        sys.exit(1)

    tenant = sys.argv[1]

    try:
        result = patch_workload_for_external(tenant)
        print(json.dumps(result))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()