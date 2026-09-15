from pathlib import Path
import importlib.util


def test_biotools_corpus_reads_codex_and_claude_knowledge(tmp_path):
    script = Path("bio_population_genetics/skills/biotools/scripts/biotools_scan.py")
    spec = importlib.util.spec_from_file_location("biotools_scan", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    codex_kb = tmp_path / "codex"
    claude_kb = tmp_path / "claude"
    codex_kb.mkdir()
    claude_kb.mkdir()
    (codex_kb / "a.md").write_text("CodexOnlyMarker")
    (claude_kb / "b.md").write_text("ClaudeOnlyMarker")

    corpus = module.corpus_local((codex_kb, claude_kb))
    assert "codexonlymarker" in corpus
    assert "claudeonlymarker" in corpus
