from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs/reference/official-artifact-sources.yaml"


class OfficialArtifactAuditTests(unittest.TestCase):
    def test_manifest_records_scoped_public_source_status(self) -> None:
        data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))

        self.assertEqual(data["audit"]["id"], "phase31-official-artifact-availability")
        self.assertEqual(data["audit"]["audited_on_utc"], "2026-05-17")
        self.assertEqual(
            data["audit"]["status"],
            "official_project_and_video_found_implementation_code_coming_soon_as_of_2026-05-17",
        )
        self.assertIn("not proof of private author-code absence", data["audit"]["scope_boundary"])
        self.assertIn("official_implementation_code_marked_coming_soon", data["audit"]["blockers"])
        self.assertNotIn("official_project_page_url_missing", data["audit"]["blockers"])
        self.assertNotIn("official_supplementary_video_url_missing", data["audit"]["blockers"])
        self.assertEqual(data["paper"]["arxiv_id"], "2603.08079")
        self.assertEqual(data["paper"]["arxiv_version"], "v2")

    def test_manifest_covers_official_pages_and_repository_search(self) -> None:
        data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
        sources = {source["source_id"]: source for source in data["audited_sources"]}

        for source_id in (
            "arxiv_abs_2603_08079",
            "siggraph_2026_schedule_papers_116",
            "minghao_guo_author_page",
            "zhiyong_he_author_content",
            "first_author_project_page",
            "first_author_github_mabd_repo",
            "yin_yang_author_page",
            "paper_tex_source_tree",
            "github_repository_exact_search",
        ):
            self.assertIn(source_id, sources)

        self.assertTrue(sources["arxiv_abs_2603_08079"]["official"])
        self.assertTrue(sources["siggraph_2026_schedule_papers_116"]["official"])
        self.assertTrue(sources["minghao_guo_author_page"]["official"])
        self.assertTrue(sources["zhiyong_he_author_content"]["official"])
        self.assertTrue(sources["first_author_project_page"]["official"])
        self.assertTrue(sources["first_author_github_mabd_repo"]["official"])
        self.assertTrue(sources["yin_yang_author_page"]["official"])
        self.assertFalse(sources["github_repository_exact_search"]["official"])
        self.assertEqual(sources["github_repository_exact_search"]["observed_total_count"], 0)

        for source in sources.values():
            self.assertIn("url", source)
            self.assertIn("observation", source)
            self.assertIs(source["has_official_implementation_code_link"], False)
        self.assertIs(sources["github_repository_exact_search"]["incomplete_results"], False)
        self.assertIs(sources["zhiyong_he_author_content"]["has_official_project_page_link"], True)
        self.assertIs(sources["first_author_project_page"]["has_official_project_page_link"], True)
        self.assertIs(sources["first_author_project_page"]["has_supplementary_video_url"], True)
        self.assertEqual(
            sources["first_author_project_page"]["implementation_code_status"],
            "coming_soon",
        )
        self.assertEqual(sources["first_author_github_mabd_repo"]["repository_language"], "HTML")
        self.assertEqual(
            sources["first_author_github_mabd_repo"]["root_contents"],
            ["index.html", "static"],
        )
        self.assertFalse(sources["first_author_github_mabd_repo"]["has_supplementary_video_url"])

    def test_manifest_keeps_supplementary_video_gap_separate_from_code_gap(self) -> None:
        data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
        sources = {source["source_id"]: source for source in data["audited_sources"]}
        tex_source = sources["paper_tex_source_tree"]
        project_page = sources["first_author_project_page"]

        self.assertTrue(tex_source["mentions_supplementary_video"])
        self.assertFalse(tex_source["has_supplementary_video_url"])
        self.assertIn("supplementary video", tex_source["observation"])
        self.assertTrue(project_page["has_supplementary_video_url"])
        self.assertEqual(
            project_page["supplementary_video_url"],
            "https://www.youtube-nocookie.com/embed/xnLCdUfq52w?rel=0",
        )
        self.assertNotIn("official_supplementary_video_url_missing", data["audit"]["blockers"])

    def test_manifest_uses_non_absolute_absence_language(self) -> None:
        text = MANIFEST_PATH.read_text(encoding="utf-8")

        self.assertIn("implementation_code_coming_soon_as_of_2026-05-17", text)
        self.assertNotIn("official code does not exist", text.lower())
        self.assertNotIn("no private author code exists", text.lower())
        self.assertNotIn("full reproduction complete", text.lower())
        self.assertNotIn("official_project_page_url_missing", text)
        self.assertNotIn("official_supplementary_video_url_missing", text)

    def test_validator_enforces_phase31_manifest_and_forbidden_claim_fields(self) -> None:
        validator = (ROOT / "scripts/validate_docs.py").read_text(encoding="utf-8")

        for snippet in (
            "first-author project page must mark implementation code coming soon",
            "first-author project page must record the supplementary video URL",
            "first-author mabd repository must be HTML project-page source",
            "GitHub repository exact search must report incomplete_results false",
            "Phase 31 project-page/video availability",
            "Phase 31 artifact manifest contains stale docs commit placeholder",
            "claim-boundaries.md contains stale Phase 31 placeholder",
        ):
            self.assertIn(snippet, validator)


if __name__ == "__main__":
    unittest.main()
