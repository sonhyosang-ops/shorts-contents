import unittest
from pathlib import Path

from edu_shorts.runner import FakeRunner
from edu_shorts.validators import ContractError, validate_stage


ROOT = Path(__file__).resolve().parents[1]


class ValidatorTests(unittest.TestCase):
    def test_fake_storyboard_obeys_prompt_guards(self) -> None:
        result = FakeRunner().run(
            role="visual_director",
            prompt="",
            schema_path=ROOT / "schemas/storyboard.schema.json",
            output_path=ROOT / "tests/.tmp-storyboard.json",
        )
        validate_stage(
            "storyboard", result, ROOT / "schemas/storyboard.schema.json"
        )
        (ROOT / "tests/.tmp-storyboard.json").unlink()

    def test_unknown_evidence_id_is_rejected(self) -> None:
        narration = FakeRunner().run(
            role="narrative_writer",
            prompt="",
            schema_path=ROOT / "schemas/narration.schema.json",
            output_path=ROOT / "tests/.tmp-narration.json",
        )
        narration["lines"][0]["evidence_ids"] = ["UNKNOWN"]
        with self.assertRaises(ContractError):
            validate_stage(
                "narration",
                narration,
                ROOT / "schemas/narration.schema.json",
                analysis={"evidence": [{"evidence_id": "E1"}]},
            )
        (ROOT / "tests/.tmp-narration.json").unlink()

    def test_analysis_excerpt_must_come_from_source_material(self) -> None:
        analysis = FakeRunner().run(
            role="content_analyst",
            prompt="",
            schema_path=ROOT / "schemas/content-analysis.schema.json",
            output_path=ROOT / "tests/.tmp-analysis.json",
        )
        with self.assertRaises(ContractError):
            validate_stage(
                "analysis",
                analysis,
                ROOT / "schemas/content-analysis.schema.json",
                content="이 원자료에는 해당 인용문이 없습니다.",
            )
        (ROOT / "tests/.tmp-analysis.json").unlink()

    def test_narration_must_match_brief_duration(self) -> None:
        narration = FakeRunner().run(
            role="narrative_writer",
            prompt="",
            schema_path=ROOT / "schemas/narration.schema.json",
            output_path=ROOT / "tests/.tmp-narration.json",
        )
        with self.assertRaises(ContractError):
            validate_stage(
                "narration",
                narration,
                ROOT / "schemas/narration.schema.json",
                analysis={"evidence": [{"evidence_id": "E1"}]},
                brief={"target_duration_seconds": 65},
            )
        (ROOT / "tests/.tmp-narration.json").unlink()

    def test_narration_fields_must_match_timed_lines(self) -> None:
        narration = FakeRunner().run(
            role="narrative_writer",
            prompt="",
            schema_path=ROOT / "schemas/narration.schema.json",
            output_path=ROOT / "tests/.tmp-narration.json",
        )
        narration["full_text"] = "서로 다른 전문"
        with self.assertRaises(ContractError):
            validate_stage(
                "narration",
                narration,
                ROOT / "schemas/narration.schema.json",
                analysis={"evidence": [{"evidence_id": "E1"}]},
                brief={"target_duration_seconds": 70},
            )
        (ROOT / "tests/.tmp-narration.json").unlink()

    def test_storyboard_timing_must_be_contiguous(self) -> None:
        storyboard = FakeRunner().run(
            role="visual_director",
            prompt="",
            schema_path=ROOT / "schemas/storyboard.schema.json",
            output_path=ROOT / "tests/.tmp-storyboard.json",
        )
        storyboard["scenes"][1]["start"] += 1
        with self.assertRaises(ContractError):
            validate_stage(
                "storyboard",
                storyboard,
                ROOT / "schemas/storyboard.schema.json",
                narration={"duration_seconds": 70},
                brief={"target_duration_seconds": 70},
            )
        (ROOT / "tests/.tmp-storyboard.json").unlink()

    def test_storyboard_must_match_narration_and_define_one_action(self) -> None:
        runner = FakeRunner()
        narration = runner.run(
            role="narrative_writer",
            prompt="",
            schema_path=ROOT / "schemas/narration.schema.json",
            output_path=ROOT / "tests/.tmp-narration.json",
        )
        storyboard = runner.run(
            role="visual_director",
            prompt="",
            schema_path=ROOT / "schemas/storyboard.schema.json",
            output_path=ROOT / "tests/.tmp-storyboard.json",
        )
        storyboard["scenes"][0]["narration"] = "다른 내레이션"
        with self.assertRaises(ContractError):
            validate_stage(
                "storyboard",
                storyboard,
                ROOT / "schemas/storyboard.schema.json",
                narration=narration,
                brief={"target_duration_seconds": 70},
            )
        storyboard["scenes"][0]["narration"] = narration["lines"][0]["text"]
        del storyboard["scenes"][0]["core_action"]
        with self.assertRaises(ContractError):
            validate_stage(
                "storyboard",
                storyboard,
                ROOT / "schemas/storyboard.schema.json",
                narration=narration,
                brief={"target_duration_seconds": 70},
            )
        (ROOT / "tests/.tmp-narration.json").unlink()
        (ROOT / "tests/.tmp-storyboard.json").unlink()

    def test_review_must_match_assigned_reviewer(self) -> None:
        review = FakeRunner().run(
            role="education_reviewer",
            prompt="",
            schema_path=ROOT / "schemas/review.schema.json",
            output_path=ROOT / "tests/.tmp-review.json",
        )
        with self.assertRaises(ContractError):
            validate_stage(
                "review",
                review,
                ROOT / "schemas/review.schema.json",
                expected_reviewer="video",
            )
        (ROOT / "tests/.tmp-review.json").unlink()

    def test_passed_review_cannot_keep_issues(self) -> None:
        review = FakeRunner().run(
            role="education_reviewer",
            prompt="",
            schema_path=ROOT / "schemas/review.schema.json",
            output_path=ROOT / "tests/.tmp-review.json",
        )
        review["critical_issues"] = [
            {
                "code": "E001",
                "severity": "minor",
                "target_stage": "narration",
                "scene_ids": [],
                "evidence": "확인 필요",
                "instruction": "문장을 다듬으세요.",
            }
        ]
        with self.assertRaises(ContractError):
            validate_stage(
                "review",
                review,
                ROOT / "schemas/review.schema.json",
                expected_reviewer="education",
            )
        (ROOT / "tests/.tmp-review.json").unlink()


if __name__ == "__main__":
    unittest.main()
