#!/usr/bin/env python3

from pathlib import Path
import shutil
import sys


PLACEHOLDER = "__TENANT__"


def replace_in_file(path: Path, tenant: str) -> None:
    content = path.read_text()
    content = content.replace(PLACEHOLDER, tenant)
    path.write_text(content)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} <tenant>", file=sys.stderr)
        sys.exit(1)

    tenant = sys.argv[1].strip()
    if not tenant:
        print("ERROR: tenant name cannot be empty", file=sys.stderr)
        sys.exit(1)

    repo_root = Path(__file__).resolve().parent.parent
    template_dir = repo_root / "tenants" / "template"
    tenant_dir = repo_root / "tenants" / tenant

    if not template_dir.exists():
        print(f"ERROR: template directory not found: {template_dir}", file=sys.stderr)
        sys.exit(1)

    if tenant_dir.exists():
        print(f"ERROR: tenant directory already exists: {tenant_dir}", file=sys.stderr)
        sys.exit(1)

    shutil.copytree(template_dir, tenant_dir)

    for path in tenant_dir.rglob("*"):
        if path.is_file():
            replace_in_file(path, tenant)

    print(f"Created tenant directory: {tenant_dir}")


if __name__ == "__main__":
    main()