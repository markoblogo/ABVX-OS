import json
import tempfile
import unittest
from pathlib import Path

from abvx_harness.book_radar import DEFAULT_MODEL, assess_portfolio_similarity, empty_state, export_state, import_bundle, import_catalog, load_state, register_scoring_model, report, save_state, score_values
from abvx_harness.harness import ValidationError


ROOT = Path(__file__).resolve().parents[1]


class BookRadarTests(unittest.TestCase):
    def test_score_is_reproducible(self):
        values = {key: 4 for key in DEFAULT_MODEL["weights"]}
        self.assertEqual(score_values(values, {}, DEFAULT_MODEL), 80.0)

    def test_scoring_version_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            register_scoring_model(root, DEFAULT_MODEL)
            changed = {**DEFAULT_MODEL, "formula": "changed"}
            with self.assertRaises(ValidationError):
                register_scoring_model(root, changed)

    def test_import_is_idempotent_and_links_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = ROOT / "book-radar" / "imports" / "asset-radar-v1-minimum.json"
            first = import_bundle(root, source)
            second = import_bundle(root, source)
            self.assertEqual(first["added"]["opportunities"], 3)
            self.assertEqual(second["added"]["opportunities"], 0)
            self.assertEqual(len(load_state(root)["decisions"]), 3)

    def test_round_trip_preserves_actual_snapshots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = empty_state()
            state["radar_runs"] = [{"id": "run-1"}]
            state["opportunities"] = [{"id": "opp-1", "radar_run_id": "run-1"}]
            state["products"] = [{"id": "product-1", "opportunity_id": "opp-1", "status": "LIVE"}]
            state["actuals"] = [{"id": "actual-1-D7", "product_id": "product-1", "checkpoint": "D7", "units": 2}]
            save_state(root, state)
            destination = root / "export.json"
            export_state(root, destination)
            self.assertEqual(json.loads(destination.read_text()), state)
            self.assertEqual(report(root, "experiments")["experiments"][0]["actuals"][0]["checkpoint"], "D7")

    def test_invalid_stable_id_is_rejected(self):
        state = empty_state()
        state["radar_runs"] = [{"id": "bad id"}]
        with self.assertRaises(ValidationError):
            save_state(Path("unused"), state)

    def test_existing_product_match_blocks_same_thesis(self):
        fixture = json.loads((ROOT / "book-radar" / "fixtures" / "portfolio-similarity-human-backup-plan.json").read_text())
        self.assertEqual(assess_portfolio_similarity(fixture["facets"], fixture["weights"]), fixture["expected"])

    def test_similar_words_do_not_override_different_buyer_jobs(self):
        weights = {"buyer":15,"jtbd":25,"trigger":10,"promise":20,"format":5,"information_architecture":10,"search_intent":5,"audience":5,"differentiation":5}
        facets = {"buyer":10,"jtbd":10,"trigger":10,"promise":15,"format":80,"information_architecture":20,"search_intent":90,"audience":10,"differentiation":10}
        result = assess_portfolio_similarity(facets, weights)
        self.assertEqual(result["classification"], "NOVEL")
        self.assertTrue(result["production_eligible"])

    def test_adjacent_product_remains_eligible_with_warning(self):
        weights = {"buyer":15,"jtbd":25,"trigger":10,"promise":20,"format":5,"information_architecture":10,"search_intent":5,"audience":5,"differentiation":5}
        facets = {key: 45 for key in weights}
        result = assess_portfolio_similarity(facets, weights)
        self.assertEqual(result["classification"], "ADJACENT")
        self.assertEqual(result["route"], "PRODUCTION_ELIGIBLE_WITH_WARNING")

    def test_catalog_and_similarity_persist_without_changing_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            import_bundle(root, ROOT / "book-radar" / "imports" / "radar-native-2-opportunities.json")
            before = json.dumps({key: load_state(root)[key] for key in ("opportunities", "evidence")}, sort_keys=True)
            import_catalog(root, ROOT / "book-radar" / "catalog-imports" / "human-backup-plan.json")
            audit = json.loads((ROOT / "book-radar" / "imports" / "radar-native-2-existing-product-match-audit.json").read_text())
            state = load_state(root)
            state["similarity_results"] = audit["similarity_results"]
            save_state(root, state)
            after = json.dumps({key: load_state(root)[key] for key in ("opportunities", "evidence")}, sort_keys=True)
            self.assertEqual(before, after)
            self.assertEqual(load_state(root)["similarity_results"][0]["route"], "EXISTING_PRODUCT_AUDIT")


if __name__ == "__main__":
    unittest.main()
