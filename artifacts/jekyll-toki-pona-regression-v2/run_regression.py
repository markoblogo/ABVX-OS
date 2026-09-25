from pathlib import Path
import json
from abvx_harness.narrative_pipeline import (
    NarrativeRunner, PipelineConfig, alignment_report, knowledge_spoiler_report,
    load_entity_registry, segment_source, sitelen_name_representation, validate_names,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "artifacts/jekyll-toki-pona-preproduction-v1/source/representative-source-sample.md"
LEDGER = ROOT / "JEKYLL_ENTITY_LEDGER_V1.json"
blocks = segment_source(SOURCE.read_text(), "jekyll-sample-v2")
registry = load_entity_registry(LEDGER)
(OUT / "source-blocks.json").write_text(json.dumps([b.__dict__ for b in blocks], indent=2, ensure_ascii=False) + "\n")

def provider(block, _context):
    # Adapter fixture: pipeline QA is real; literary output remains review-gated.
    text = block.source_text.lower()
    if "jekyll" in text and "hyde" in text:
        return "jan Jekil li toki. jan Hata li weka."
    if "poole" in text:
        return "jan Pulu li pilin ike. ona li toki."
    return "jan Utason li lukin e ijo."

runner = NarrativeRunner(OUT / "run", PipelineConfig(max_retries=0))
translated = runner.run(blocks, provider)
(OUT / "translated-blocks.json").write_text(json.dumps([b.__dict__ for b in translated], indent=2, ensure_ascii=False) + "\n")
(OUT / "entity-name-registry.json").write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n")
constraints = [{"blockId": b.block_id, "knowledgeType": b.knowledge_type, "spoilerConstraints": b.spoiler_constraints} for b in blocks]
(OUT / "knowledge-spoiler-constraints.json").write_text(json.dumps(constraints, indent=2, ensure_ascii=False) + "\n")
alignment = alignment_report(blocks, translated)
names = validate_names("\n".join(b.translation_text for b in translated), registry)
spoiler = knowledge_spoiler_report(blocks, translated)
sitelen = ["# " + b.block_id + "\n" + sitelen_name_representation(b.translation_text) for b in translated]
(OUT / "sitelen-input-output.txt").write_text("\n\n".join(sitelen) + "\n")
qa = {"pipelineVersion": "narrative-toki-pona-pipeline-v1", "sourceBlockCount": len(blocks),
      "translationBlockCount": len(translated), "alignment": alignment, "names": names,
      "knowledgeSpoiler": spoiler, "mechanicalStatus": "PASS" if alignment["status"] == "PASS" and names["status"] == "PASS" else "FAIL",
      "editorialStatus": "REVIEW", "providerAdapter": "fixture-backed-local-regression", "fullBookTranslation": False}
(OUT / "qa-results.json").write_text(json.dumps(qa, indent=2, ensure_ascii=False) + "\n")
