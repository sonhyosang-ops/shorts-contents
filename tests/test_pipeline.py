import json
import tempfile
import threading
import unittest
from pathlib import Path

from edu_shorts.pipeline import Pipeline
from edu_shorts.runner import FakeRunner


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def test_fake_pipeline_exports_package(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary)
            for name in (".codex", "schemas"):
                source = ROOT / name
                target = project_root / name
                self._copy_tree(source, target)
            input_dir = project_root / "projects/demo/input"
            input_dir.mkdir(parents=True)
            (input_dir / "brief.json").write_text(
                json.dumps(
                    {
                        "title": "샘플",
                        "audience": "초등학교 5학년",
                        "target_duration_seconds": 70,
                        "language": "ko",
                        "aspect_ratio": "9:16",
                        "visual_style": "3D",
                        "source_policy": "provided_material_only",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (input_dir / "content.md").write_text(
                "샘플 원자료의 핵심 문장", encoding="utf-8"
            )
            package = Pipeline(project_root, FakeRunner()).run("demo")
            self.assertEqual("passed", package["status"])
            self.assertTrue(
                (
                    project_root
                    / "projects/demo/output/runs/run-001/final-package.md"
                ).exists()
            )

    def test_second_run_preserves_first_run_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary)
            for name in (".codex", "schemas"):
                self._copy_tree(ROOT / name, project_root / name)
            input_dir = project_root / "projects/demo/input"
            input_dir.mkdir(parents=True)
            (input_dir / "brief.json").write_text(
                json.dumps(
                    {
                        "title": "샘플",
                        "audience": "초등학교 5학년",
                        "target_duration_seconds": 70,
                        "language": "ko",
                        "aspect_ratio": "9:16",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (input_dir / "content.md").write_text("샘플 원자료", encoding="utf-8")
            Pipeline(project_root, FakeRunner()).run("demo")
            first_output = (
                project_root / "projects/demo/output/runs/run-001/final-package.json"
            )
            first_contents = first_output.read_text(encoding="utf-8")
            Pipeline(project_root, FakeRunner()).run("demo")
            self.assertEqual(first_contents, first_output.read_text(encoding="utf-8"))
            self.assertTrue(
                (
                    project_root
                    / "projects/demo/output/runs/run-002/final-package.json"
                ).exists()
            )

    def test_review_restarts_only_targeted_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary)
            for name in (".codex", "schemas"):
                self._copy_tree(ROOT / name, project_root / name)
            input_dir = project_root / "projects/demo/input"
            input_dir.mkdir(parents=True)
            (input_dir / "brief.json").write_text(
                json.dumps(
                    {
                        "title": "샘플",
                        "audience": "초등학교 5학년",
                        "target_duration_seconds": 70,
                        "language": "ko",
                        "aspect_ratio": "9:16",
                        "visual_style": "3D",
                        "source_policy": "provided_material_only",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (input_dir / "content.md").write_text(
                "샘플 원자료의 핵심 문장", encoding="utf-8"
            )
            runner = OneFailureRunner()
            package = Pipeline(project_root, runner).run("demo")
            self.assertEqual("passed", package["status"])
            self.assertEqual(1, package["attempts"])
            self.assertEqual(1, runner.calls["content_analyst"])
            self.assertEqual(1, runner.calls["narrative_writer"])
            self.assertEqual(2, runner.calls["visual_director"])

    @staticmethod
    def _copy_tree(source: Path, target: Path) -> None:
        for path in source.rglob("*"):
            if path.is_file():
                destination = target / path.relative_to(source)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(path.read_bytes())

class OneFailureRunner(FakeRunner):
    def __init__(self) -> None:
        self.calls: dict[str, int] = {}
        self._lock = threading.Lock()

    def run(self, **kwargs):
        role = kwargs["role"]
        with self._lock:
            self.calls[role] = self.calls.get(role, 0) + 1
            call_number = self.calls[role]
        result = super().run(**kwargs)
        if role == "video_reviewer" and call_number == 1:
            result.update(
                {
                    "pass": False,
                    "score": 70,
                    "summary": "첫 검수에서 장면을 수정해야 합니다.",
                    "critical_issues": [
                        {
                            "code": "V001",
                            "severity": "major",
                            "target_stage": "storyboard",
                            "scene_ids": ["S1"],
                            "evidence": "한 장면에 행동이 많음",
                            "instruction": "첫 장면의 행동을 하나로 줄이세요.",
                        }
                    ],
                }
            )
            kwargs["output_path"].write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        return result


if __name__ == "__main__":
    unittest.main()
