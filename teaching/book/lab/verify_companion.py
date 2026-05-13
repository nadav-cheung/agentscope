#!/usr/bin/env python3
"""Verify that all source-code pointers in companion files are valid.

Scans `# → src/agentscope/xxx.py:123` comments in all .py files,
then verifies each referenced file exists and line number is in range.

Usage:
    python verify_companion.py
"""
import re
import sys
from pathlib import Path

COMPANION_ROOT = Path(__file__).resolve().parent
# COMPANION_ROOT = teaching/book/lab/
# REPO_ROOT     = agentscope/ (3 levels up)
REPO_ROOT = COMPANION_ROOT.parent.parent.parent

# Matches: # → src/agentscope/agent/_react_agent.py:408
POINTER_RE = re.compile(r"#\s*→\s*(src/agentscope/\S+?\.py):(\d+)")


def find_agentscope_src():
    """Auto-detect AgentScope source. The lab is inside the repo, so it's always findable."""
    candidate = REPO_ROOT / "src" / "agentscope"
    if candidate.is_dir():
        return candidate
    # Fallback for standalone deployments
    for c in [
        COMPANION_ROOT.parent / "agentscope" / "src" / "agentscope",
        Path.home() / "agentscope" / "src" / "agentscope",
    ]:
        if c.is_dir():
            return c
    return None


def check_pointer(pointer_path, line_num, src_root):
    """Verify a single source pointer. Returns (ok, message)."""
    # pointer_path is relative to repo root: src/agentscope/xxx.py
    full_path = REPO_ROOT / pointer_path
    if not full_path.exists():
        full_path = src_root / Path(pointer_path).relative_to("src/agentscope")

    if not full_path.exists():
        return False, f"FILE NOT FOUND: {pointer_path}"

    lines = full_path.read_text().split("\n")
    if line_num > len(lines):
        return False, f"LINE {line_num} > {len(lines)} in {pointer_path}"

    return True, f"OK: {pointer_path}:{line_num}"


def main():
    src_root = find_agentscope_src()
    if not src_root:
        print("ERROR: Cannot find AgentScope source.")
        print("Run from within the agentscope repository.")
        sys.exit(1)
    print(f"AgentScope source: {src_root}\n")

    total, ok, fail = 0, 0, 0
    for py_file in sorted(COMPANION_ROOT.glob("ch*.py")):
        for match in POINTER_RE.finditer(py_file.read_text()):
            total += 1
            pointer_path = match.group(1)
            line_num = int(match.group(2))
            status, msg = check_pointer(pointer_path, line_num, src_root)
            if status:
                ok += 1
            else:
                fail += 1
                print(f"  FAIL [{py_file.name}] {msg}")

    print(f"\n{'='*50}")
    print(f"  Total pointers: {total}")
    print(f"  OK:             {ok}")
    print(f"  FAIL:           {fail}")

    if fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
