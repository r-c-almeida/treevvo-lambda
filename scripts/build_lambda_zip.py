#!/usr/bin/env python3
"""
Monta o artefato ZIP para AWS Lambda: dependências Linux (manylinux) + código da aplicação.

Uso (na raiz do repo):
    python scripts/build_lambda_zip.py

Com Lambda em ARM64:
    python scripts/build_lambda_zip.py --platform manylinux2014_aarch64

Com runtime Python 3.12 na AWS:
    python scripts/build_lambda_zip.py --python-version 312

Requisito: ``pip`` conseguir baixar wheels ``manylinux`` para a versão informada (rode em rede).
Docker não é obrigatório se este comando funcionar no seu Windows/macOS/Linux.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DEFAULT_PKG = DIST / "lambda_package"
REQ = ROOT / "requirements.txt"


def _copy_app_into(pkg: Path) -> None:
    for name in ("lambda_function.py", "application.py"):
        src = ROOT / name
        if not src.is_file():
            raise FileNotFoundError(f"Arquivo obrigatório ausente: {src}")
        shutil.copy2(src, pkg / name)

    for folder in ("source", "docs"):
        src = ROOT / folder
        if not src.is_dir():
            raise FileNotFoundError(f"Pasta obrigatória ausente: {src}")
        dest = pkg / folder
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def _clean_package(pkg: Path) -> None:
    for p in sorted(pkg.rglob("__pycache__"), key=lambda x: len(str(x)), reverse=True):
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
    for p in pkg.rglob("*.py[co]"):
        try:
            p.unlink()
        except OSError:
            pass
    for p in pkg.rglob("*.pyo"):
        try:
            p.unlink()
        except OSError:
            pass


def _zip_package_flat(pkg: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(pkg.rglob("*")):
            if path.is_file():
                arcname = path.relative_to(pkg).as_posix()
                zf.write(path, arcname)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Lambda deployment zip.")
    parser.add_argument(
        "--python-version",
        default="314",
        help="Tag cp do Lambda (ex.: 314 para Python 3.14, 312 para 3.12).",
    )
    parser.add_argument(
        "--platform",
        default="manylinux2014_x86_64",
        help="Plataforma dos wheels (x86_64 ou aarch64 conforme a função).",
    )
    parser.add_argument(
        "--package-dir",
        type=Path,
        default=DEFAULT_PKG,
        help="Pasta temporária com o conteúdo do ZIP.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DIST / "treevvo-lambda.zip",
        help="Arquivo ZIP final.",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Só empacota (assume dependências já instaladas em --package-dir).",
    )
    args = parser.parse_args()

    pkg: Path = args.package_dir
    if not args.skip_install:
        if DIST.exists():
            shutil.rmtree(DIST)
        pkg.mkdir(parents=True)

        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--isolated",
            "-r",
            str(REQ),
            "-t",
            str(pkg),
            "--platform",
            args.platform,
            "--implementation",
            "cp",
            "--python-version",
            args.python_version,
            "--only-binary=:all:",
            "--upgrade",
        ]
        print("Executando:", " ".join(cmd))
        subprocess.run(cmd, check=True)

    _copy_app_into(pkg)
    _clean_package(pkg)
    _zip_package_flat(pkg, args.output)

    size_mb = args.output.stat().st_size / (1024 * 1024)
    print(f"OK: {args.output} ({size_mb:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
