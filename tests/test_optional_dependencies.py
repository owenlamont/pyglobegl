from __future__ import annotations

from pathlib import Path
import shutil
import subprocess  # noqa: S404


def test_optional_dependencies_not_required(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = tmp_path / "import_check.py"
    script_path.write_text(
        "\n".join(
            [
                "# /// script",
                f'# dependencies = ["pyglobegl @ {repo_root.as_uri()}"]',
                "# ///",
                "from pyglobegl import GlobeConfig, GlobeWidget",
                "GlobeWidget(config=GlobeConfig())",
                'print("ok")',
            ]
        ),
        encoding="utf-8",
    )
    uv_path = shutil.which("uv")
    assert uv_path is not None, "uv must be installed to run optional dependency guard."
    result = subprocess.run(  # noqa: S603
        [uv_path, "run", "--script", str(script_path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
    )
    assert result.returncode == 0, result.stderr
