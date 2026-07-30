from __future__ import annotations

import os
import json
import shutil
import time
from pathlib import Path
from typing import Any

from .api_runner import OpenAIResponsesRunner
from .ingestion import normalize_sources
from .pipeline import Pipeline
from .web_api import supabase_admin


def run_worker() -> None:
    interval = float(os.getenv("WORKER_POLL_SECONDS", "3"))
    while True:
        try:
            _process_one()
        except Exception as exc:
            print(f"worker error: {exc}", flush=True)
        time.sleep(interval)


def _process_one() -> None:
    client = supabase_admin()
    response = client.rpc("claim_next_short_job").execute()
    if not response.data:
        return
    job: dict[str, Any] = response.data[0]
    project_root = Path(os.getenv("PROJECT_ROOT", Path.cwd()))
    project_dir = project_root / "projects" / job["slug"]
    try:
        source_dir = project_dir / "input" / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        paths = _download_sources(client, job["source_paths"], source_dir)
        _write_inputs(project_dir, job, normalize_sources(paths))
        pipeline = Pipeline(project_root, OpenAIResponsesRunner(os.getenv("OPENAI_MODEL", "")))
        package = pipeline.run(job["slug"])
        assert pipeline.output_dir is not None
        result = pipeline.output_dir / "final-package.md"
        storage_path = f"{job['user_id']}/{job['id']}/final-package.md"
        client.storage.from_("short-results").upload(storage_path, result.read_bytes(), {"content-type": "text/markdown", "upsert": "true"})
        client.table("short_jobs").update({"status": package["status"], "result_path": storage_path}).eq("id", job["id"]).execute()
    except Exception as exc:
        client.table("short_jobs").update({"status": "failed", "error": str(exc)[-1000:]}).eq("id", job["id"]).execute()
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)


def _download_sources(client: Any, source_paths: list[str], destination: Path) -> list[Path]:
    paths = []
    for index, storage_path in enumerate(source_paths, start=1):
        target = destination / f"S{index:03d}-{Path(storage_path).name}"
        target.write_bytes(client.storage.from_("short-sources").download(storage_path))
        paths.append(target)
    return paths


def _write_inputs(project_dir: Path, job: dict[str, Any], content: str) -> None:
    input_dir = project_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    brief = {
        "title": job["title"],
        "audience": job["audience"],
        "target_duration_seconds": job["duration_seconds"],
        "language": "ko",
        "aspect_ratio": "9:16",
        "visual_style": "cinematic 3D educational animation",
        "source_policy": "provided_material_only",
    }
    (input_dir / "brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
    (input_dir / "content.md").write_text(content, encoding="utf-8")


if __name__ == "__main__":
    run_worker()
