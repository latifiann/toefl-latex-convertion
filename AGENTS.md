# TOEFL LaTeX Repository Guide

## Repository purpose
Generate TOEFL practice PDFs from DOCX sources with canonical/derived separation.

## Read this first
- [Build workflow](docs/build-workflow.md)
- [New practice conversion runbook](docs/new-practice-conversion-runbook.md)
- [Manual editing policy](docs/manual-editing-policy.md)
- [Editorial style](docs/editorial-style.md)
- [Answering policy](docs/answering-policy.md)
- [Data model](docs/data-model.md)
- [Anomalies policy](docs/anomalies-policy.md)

## Hard rules
- Source of truth: `source/original/*.docx` only.
- Authoritative PDFs: `build/pdf/*.pdf` only.
- `build/generated-tex/*.tex` is disposable.
- Do not guess missing source content.

## Allowed edit targets
- `content/**/canonical/`
- `content/**/derived/`
- `scripts/`
- `tex/preamble/`
- `docs/`
- `README.md`

## Forbidden edit targets
- `build/generated-tex/`
- `build/pdf/`

## Build rules
Run sequentially:
1. `python3 scripts/ingest_docx.py --practice-id P01 --source source/original/practice-01.docx`
2. `python3 scripts/validate_content.py --practice-id P01`
3. `python3 scripts/compile_pdf.py --practice-id P01 --mode both`

## Answering rules
- Reading: evidence-based, use line_map when available.
- Structure: rule-based grammar explanations.
- Listening: reconstruction is not an official transcript.

## Reading fidelity
- Preserve line breaks and the token `Line`.
- Render each line as a separate paragraph.

## Task-to-document routing
- Formatting/layout: [Editorial style](docs/editorial-style.md)
- Build/output: [Build workflow](docs/build-workflow.md)
- Manual edit choices: [Manual editing policy](docs/manual-editing-policy.md)
- Answering/explanations: [Answering policy](docs/answering-policy.md)
- Schemas/IDs: [Data model](docs/data-model.md)
- Missing/duplicate/noisy source: [Anomalies policy](docs/anomalies-policy.md)
