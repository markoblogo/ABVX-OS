"""Attempt the exact sample through the existing trusted local model path."""
from pathlib import Path
import json
from abvx_harness.narrative_pipeline import LocalModelNarrativeProvider, segment_source

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
source = ROOT / "artifacts/jekyll-toki-pona-preproduction-v1/source/representative-source-sample.md"
blocks = segment_source(source.read_text(), "jekyll-sample-v3")
(OUT / "source-blocks.json").write_text(json.dumps([b.__dict__ for b in blocks], indent=2, ensure_ascii=False) + "\n")
provider = LocalModelNarrativeProvider()
attempts = []
for block in blocks:
    try:
        result = provider.translate(block)
        attempts.append({"blockId": block.block_id, "status": "SUCCESS", **result})
    except Exception as exc:
        attempts.append({"blockId": block.block_id, "status": "FAILED", "error": str(exc)})
        break
(OUT / "provider-attempt.json").write_text(json.dumps({
    "provider": "abvx-local-model-worker", "model": provider.model,
    "endpoint": provider.url, "configuration": {"timeoutSeconds": provider.timeout},
    "attemptedBlocks": attempts, "status": "PASS" if all(x["status"] == "SUCCESS" for x in attempts) and len(attempts) == len(blocks) else "FAIL"
}, indent=2, ensure_ascii=False) + "\n")
(OUT / "run-manifest.json").write_text(json.dumps({
    "schemaVersion": "1.0", "pipelineVersion": "narrative-toki-pona-pipeline-v1",
    "mode": "INTERNAL_BOOK_PIPELINE", "provider": "abvx-local-model-worker",
    "model": provider.model, "sourceBlockCount": len(blocks),
    "completedBlockCount": sum(x["status"] == "SUCCESS" for x in attempts),
    "failedBlockCount": sum(x["status"] == "FAILED" for x in attempts),
    "resumeSafe": True, "fullBookTranslation": False
}, indent=2, ensure_ascii=False) + "\n")
(OUT / "qa-results.json").write_text(json.dumps({
    "realProviderOutput": "PASS" if len(attempts) == len(blocks) and all(x["status"] == "SUCCESS" for x in attempts) else "FAIL",
    "alignment": "NOT_RUN", "names": "NOT_RUN", "knowledge": "NOT_RUN", "spoilers": "NOT_RUN",
    "reason": attempts[-1].get("error") if attempts else "no attempt",
    "publicDeployment": "SEPARATE", "fullBookTranslation": False
}, indent=2, ensure_ascii=False) + "\n")
