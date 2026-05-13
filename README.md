# TOEFL LaTeX Project

This project keeps `DOCX` as the only source of truth and separates cleaned study content from AI-derived material.

## Data Layers

1. `source/original/`
   Only original `.docx` files live here.
2. `content/practice-XX/canonical/`
   Normalized content extracted from the `.docx` source.
3. `content/practice-XX/derived/`
   AI-generated drafts such as listening reconstructions, proposed answers, and bilingual review notes.

## Derived Answer Layout

Answer drafts are split by section:

- `derived/structure.answers.ai.json`
- `derived/reading.answers.ai.json`
- `derived/listening.answers.ai.json`

This keeps the files smaller, makes review easier, and avoids mixing `Structure`, `Reading`, and `Listening` workflows.

## File Format Choice

Question data uses `.json` filenames and is read with the standard JSON parser.
This keeps the files readable while allowing the scripts in `scripts/` to use Python's standard `json` module without extra dependencies.

## Current Status

- `practice-01` has been ingested from `source/original/practice-01.docx`
- `practice-01` reading canonical files now include `line_map` data that follows the source line breaks from the DOCX extract
- `practice-01` listening content contains a missing source question `33`
- `practice-01` reading content contains a duplicate extracted `44` in passage 05, logged as an anomaly and excluded from canonical questions
- No official answer key exists yet, so all answers remain `AI-proposed` unless a later validation source is added
- Pilot AI answers are filled for `Structure 01-05` and `Reading Passage 01`
- Review PDF now supports both inline explanations and an appendix-style answer key
- `build/pdf/` is the single authoritative PDF output directory

## Commands

Extract and normalize a practice:

```bash
python3 scripts/ingest_docx.py --practice-id P01 --source source/original/practice-01.docx
```

Validate canonical content:

```bash
python3 scripts/validate_content.py --practice-id P01
```

Render a LaTeX draft:

```bash
python3 scripts/render_tex.py --practice-id P01 --mode tryout
python3 scripts/render_tex.py --practice-id P01 --mode review
```

Compile authoritative PDFs:

```bash
python3 scripts/compile_pdf.py --practice-id P01 --mode both
```

For VS Code users, workspace settings in `.vscode/settings.json` force LaTeX Workshop to compile generated `.tex` files into `build/pdf/` instead of creating sibling PDFs inside `build/generated-tex/`.

Current derived answer files are consumed automatically by `render_tex.py`, with this precedence:

1. `validated_answer`
2. `proposed_answer`

If a TeX engine is installed, use the compile script instead of calling `xelatex` or `pdflatex` directly. The script keeps `build/generated-tex/` for `.tex` files only and writes the authoritative PDFs to `build/pdf/`.

Authoritative PDF paths:

- `build/pdf/P01-tryout.pdf`
- `build/pdf/P01-review.pdf`

## Docs Map

- [AGENTS.md](AGENTS.md): ringkas aturan kerja agent dan routing dokumen.
- [docs/new-practice-conversion-runbook.md](docs/new-practice-conversion-runbook.md): runbook konversi docx practice baru sesuai format repo.
- [docs/build-workflow.md](docs/build-workflow.md): alur build resmi dan output authoritative.
- [docs/manual-editing-policy.md](docs/manual-editing-policy.md): aturan edit manual dan file yang aman.
- [docs/editorial-style.md](docs/editorial-style.md): gaya penulisan, format soal, dan layout.
- [docs/answering-policy.md](docs/answering-policy.md): aturan jawaban, confidence, dan evidence.
- [docs/data-model.md](docs/data-model.md): schema data, ID, dan struktur file.
- [docs/anomalies-policy.md](docs/anomalies-policy.md): aturan penanganan missing/duplicate/noisy source.

## Conventions

- Listening IDs: `P01-LA-01`, `P01-LB-31`, `P01-LC-39`
- Structure IDs: `P01-ST-01` to `P01-ST-40`
- Reading IDs: `P01-RC-01-Q01`
- Reading evidence should use source-backed `line_map` references whenever possible
- Missing source content is represented explicitly instead of guessed
- Listening transcript drafts use the term `reconstruction`, not `transcript`
- Bilingual explanations should default to Indonesian, and use English where the term is more natural or precise
- Review mode should show inline explanations and an answer-key appendix, while tryout mode stays answer-free
