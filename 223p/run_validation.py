"""
run_validation.py — Execute ontology.py via ttl_tools.validate_project.

This script bootstraps the agent venv so that ttl_tools (and its dependencies)
are available, then calls validate_project.validate() with the paths required
by that function:

  samples_folder  → the 223p/ directory (must contain a ttl/ sub-folder)
  python_file     → ontology.py  (looked up under samples_folder/src/)

Expected layout assumed by validate_project:
  223p/
    src/
      ontology.py     ← symlink or copy placed here if needed
    ttl/              ← output .ttl files land here
"""

import os
import sys
import subprocess
from pathlib import Path

from rdf2html.rdf2html import to_html

# ── Bootstrap: add the agent .venv site-packages to sys.path ─────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_VENV_SITE = os.path.normpath(
    os.path.join(_HERE, "..", "agent", ".venv", "Lib", "site-packages")
)
if _VENV_SITE not in sys.path:
    sys.path.insert(0, _VENV_SITE)

_VENV_PYTHON = os.path.normpath(
    os.path.join(_HERE, "..", "agent", ".venv", "Scripts", "python.exe")
)
if not os.path.exists(_VENV_PYTHON):
    _VENV_PYTHON = sys.executable

# ── ttl_tools import ──────────────────────────────────────────────────────────
from ttl_tools.validate_project import validate  # noqa: E402

# ── Paths ─────────────────────────────────────────────────────────────────────
# validate_project.validate() resolves python_file as:
#   <samples_folder>/src/<python_file>
# So ontology.py must live (or be reachable) at 223p/src/ontology.py.
SAMPLES_FOLDER = _HERE          # 223p/
PYTHON_FILE    = "ontology.py"  # relative to SAMPLES_FOLDER/src/

# Create 223p/src/ and ensure ontology.py is visible there
SRC_DIR = os.path.join(SAMPLES_FOLDER, "src")
os.makedirs(SRC_DIR, exist_ok=True)

_src_ontology = os.path.join(SRC_DIR, PYTHON_FILE)
_real_ontology = os.path.join(SAMPLES_FOLDER, PYTHON_FILE)

if not os.path.exists(_src_ontology):
    # Create a thin proxy that simply executes the real ontology.py so that
    # validate_project can find and run it from src/.
    proxy_code = f"""\
import runpy, os, sys
sys.path.insert(0, {repr(SAMPLES_FOLDER)})
runpy.run_path({repr(_real_ontology)}, run_name="__main__")
"""
    with open(_src_ontology, "w") as fh:
        fh.write(proxy_code)
    print(f"[run_validation] Created proxy script: {_src_ontology}")

# Ensure 223p/ttl/ exists (validate_project walks for it)
os.makedirs(os.path.join(SAMPLES_FOLDER, "ttl"), exist_ok=True)

# ── Run the full validate pipeline ────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[run_validation] samples_folder : {SAMPLES_FOLDER}")
    print(f"[run_validation] python_file    : {PYTHON_FILE}")
    print()

    cwd = Path.cwd()
    samples_folder = (cwd / SAMPLES_FOLDER).resolve()
    python_file = (samples_folder / "src" / PYTHON_FILE).resolve()

    if not python_file.exists():
        print(f"[bold red]Error:[/] Python file {python_file} does not exist.")
        sys.exit(1)
    if not samples_folder.exists():
        print(f"[bold red]Error:[/] Samples folder {samples_folder} does not exist.")
        sys.exit(1)

    # Step 1: Run the specified Python file to create TTL files
    result = subprocess.run([_VENV_PYTHON, str(python_file)])
    if result.returncode != 0:
        print(f"[run_validation] ontology.py failed (exit {result.returncode})")
        sys.exit(result.returncode)

    # Step 2: Dynamically find and process all generated TTL files
    ttl_dir = Path(SAMPLES_FOLDER) / "ttl"
    ttl_files = sorted(ttl_dir.glob("*.ttl"))
    if not ttl_files:
        print(f"[run_validation] No .ttl file found in {ttl_dir}")
        sys.exit(1)

    print(f"[run_validation] Found {len(ttl_files)} TTL file(s).")
    for ttl in ttl_files:
        print(f"[run_validation] Processing: {ttl.name}")
        to_html(ttl_file=str(ttl.resolve()), show=False)


