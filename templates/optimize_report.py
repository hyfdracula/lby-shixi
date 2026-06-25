"""Build the polished final report from CC 自写 Markdown and handoff figures.

====================================================================
STAGE 3 COMPATIBILITY ENTRY — READ BEFORE EDITING
====================================================================
This file is a thin wrapper. The actual Stage-3 work (format alignment:
fonts, cover page, figure slots, figure groups, body styling) is DONE by
`report_docx_builder.build_report_docx`. Nothing is implemented here.

What this file does:
    - Parses the historical CLI args (draft path, -o output).
    - Forwards to `build_report_docx(...)`.

What this file does NOT do (any more):
    - Compare against the reference/sample PDF.
    - Tweak font sizes / margins / spacing to match a样板.

Why it still exists:
    - `run_all` / `SKILL.md` may invoke `python optimize_report.py ...`.
    - Deleting it would break those callers. Keep the CLI shape stable.

If you genuinely need to tune the DOCX against a reference PDF, extend
`match_reference_pdf(doc, pdf_path)` (TODO — currently NOT implemented,
not imported, not called). Do not silently add logic here and pretend it
is still "just a wrapper".
====================================================================

Historical CLI shape:

    python optimize_report.py handoff/report_draft.docx [-o report_final.docx]

The draft DOCX argument is accepted for compatibility; the stable source of
truth for layout is paper_rewriting_output/report_draft.md plus handoff/.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from report_docx_builder import build_report_docx


def _project_root_from_draft(draft: Path) -> Path:
    resolved = draft.resolve()
    if resolved.parent.name in {"handoff", "paper_rewriting_output"}:
        return resolved.parent.parent
    return Path.cwd()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a stable final DOCX report.")
    parser.add_argument("draft", help="Compatibility argument; usually handoff/report_draft.docx")
    parser.add_argument("-o", "--output", default=None, help="Output DOCX path")
    args = parser.parse_args()

    draft = Path(args.draft)
    project_root = _project_root_from_draft(draft)
    output = Path(args.output) if args.output else draft.parent / "report_final.docx"
    if not output.is_absolute():
        output = project_root / output

    out = build_report_docx(project_root=project_root, output_path=output, include_appendix=True)
    print(f"最终版 -> {out}")


if __name__ == "__main__":
    main()
