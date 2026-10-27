"""Bloquea la publicación accidental de credenciales y archivos privados."""

from __future__ import annotations

import re
import subprocess
import sys


SECRET_PATTERNS = (
    re.compile(r"SCOPUS_API_KEY\s*=\s*[\"']?(?!tu_clave|pega_aqui)[A-Za-z0-9_-]{20,}", re.IGNORECASE),
    re.compile(r"(?:api[_-]?key|secret|token)\s*[:=]\s*[\"']?[A-Za-z0-9_-]{24,}", re.IGNORECASE),
)
FORBIDDEN_NAMES = {".env", ".env.local", ".env.production"}


def staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRT"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def staged_content(path: str) -> str:
    result = subprocess.run(
        ["git", "show", f":{path}"],
        check=True,
        capture_output=True,
        text=True,
        errors="replace",
    )
    return result.stdout


def main() -> int:
    files = staged_files()
    problems: list[str] = []
    for path in files:
        filename = path.replace("\\", "/").rsplit("/", 1)[-1].lower()
        if filename in FORBIDDEN_NAMES:
            problems.append(f"{path}: archivo de variables de entorno")
            continue
        content = staged_content(path)
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            problems.append(f"{path}: posible credencial o token")
    if problems:
        print("PUBLICACIÓN BLOQUEADA. Revisa estos archivos:")
        print("\n".join(f"- {problem}" for problem in problems))
        return 1
    print(f"OK: {len(files)} archivo(s) preparado(s) sin credenciales detectadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
