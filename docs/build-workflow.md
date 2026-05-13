# Build Workflow

## Purpose
Menjelaskan alur build resmi, source of truth, dan lokasi output authoritative.

## Source of truth
- Satu-satunya source: `source/original/*.docx`.
- Semua konten canonical harus diturunkan dari DOCX.

## Data layers
- Canonical: `content/practice-XX/canonical/`
- Derived: `content/practice-XX/derived/`
- Generated TeX: `build/generated-tex/`
- Authoritative PDF: `build/pdf/`

## Normal editing workflow
1. Edit atau ganti DOCX di `source/original/`.
2. Jalankan ingest.
3. Validasi canonical.
4. Compile PDF authoritative.

## Build commands
```bash
python3 scripts/ingest_docx.py --practice-id P01 --source source/original/practice-01.docx
python3 scripts/validate_content.py --practice-id P01
python3 scripts/compile_pdf.py --practice-id P01 --mode both
```

## Authoritative output
- PDF yang dianggap final hanya di `build/pdf/`.
- Jangan simpan PDF di `build/generated-tex/`.

## Sequential build rule
- Ingest -> Validate -> Compile harus sequential.
- Jangan menjalankan render dan compile paralel untuk practice yang sama.

## VS Code workflow
- LaTeX Workshop diarahkan ke `build/pdf/` lewat `.vscode/settings.json`.
- Jika VS Code menghasilkan PDF di folder lain, itu bukan authoritative.

## Common mistakes
- Mengedit `build/generated-tex/*.tex` lalu menganggapnya permanen.
- Menganggap PDF di luar `build/pdf/` sebagai output final.
- Menjalankan build paralel sehingga output tidak sinkron.

## Recovery checklist
- Hapus PDF non-authoritative.
- Jalankan pipeline sequential.
- Pastikan `build/pdf/` memiliki output terbaru.

## References
- [Manual editing policy](manual-editing-policy.md)
- [Data model](data-model.md)
