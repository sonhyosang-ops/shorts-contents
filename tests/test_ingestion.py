import tempfile
import unittest
from pathlib import Path

from edu_shorts.ingestion import normalize_sources


class IngestionTests(unittest.TestCase):
    def test_text_source_is_preserved_with_source_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "lesson.txt"
            source.write_text("증발한 물은 수증기가 된다.", encoding="utf-8")
            result = normalize_sources([source])
        self.assertIn("S001 | lesson.txt", result)
        self.assertIn("증발한 물은 수증기가 된다.", result)
        self.assertIn("자동 추출 과정에서는 원문에 없는 시각 해석을 추가하지 않음.", result)
