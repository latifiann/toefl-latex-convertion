# New Practice Conversion Runbook

## Tujuan
Dokumen ini menjadi runbook konversi `practice-XX.docx` agar menghasilkan konten JSON, LaTeX, dan PDF sesuai format yang disepakati.

## Input yang dibutuhkan
- File DOCX baru di `source/original/practice-XX.docx`.
- Practice ID, contoh: `P04`.

## Output wajib
- `content/practice-XX/` (canonical + derived + meta/anomalies).
- `build/pdf/PXX-tryout.pdf`.
- `build/pdf/PXX-review.pdf`.

## Shortcut intent
Jika user memberikan prompt singkat seperti: `rubah docx practice X ini`, artinya:
1. Ingest DOCX ke canonical JSON.
2. Validasi canonical.
3. Rapikan canonical sesuai rules (line_map, paragraph_ranges, error segments, dll).
4. Siapkan derived answers sesuai policy (Indonesia-first, English bila lebih tepat).
5. Jika ada transcript reconstruction, simpan di `derived/listening/part-*.reconstruction.json`.
6. Render + compile PDF `tryout` dan `review`.

## Urutan eksekusi wajib
1. Ingest
   ```bash
   python3 scripts/ingest_docx.py --practice-id PXX --source source/original/practice-XX.docx
   ```
2. Validate
   ```bash
   python3 scripts/validate_content.py --practice-id PXX
   ```
3. Review canonical
   - Reading: cek `line_map`, `paragraph_ranges`, `referenced_lines`.
   - Structure: cek `render_segments` untuk error-identification.
   - Listening: cek numbering dan missing-source placeholders.
4. Derived answers
   - Structure & Reading: isi `proposed_answer`, `rationale_id`, `confidence_label`.
   - Listening: jangan menebak jika audio tidak ada; gunakan kunci belajar jika tersedia.
5. Compile PDF
   ```bash
   python3 scripts/compile_pdf.py --practice-id PXX --mode both
   ```

## Aturan per section
### Listening
- Canonical hanya berisi choices dari DOCX.
- Transcript reconstruction disimpan di `derived/listening/part-*.reconstruction.json`.
- Harus ada label bahwa transcript itu AI-reconstructed dan bukan official.

### Structure
- `grammar_rule` bisa English jika lebih presisi.
- `rationale_id` Indonesia-first.

### Reading
- Evidence wajib berbasis `line_map`.
- `rationale_id` Indonesia-first.

## Anomalies
- Semua masalah source dicatat di `content/practice-XX/anomalies.json`.
- Jangan menebak konten yang hilang.

## Checklist selesai
- `validate_content.py` lulus.
- `PXX-tryout.pdf` dan `PXX-review.pdf` terbuat di `build/pdf/`.
- Tidak ada edit di `build/generated-tex/`.
- Semua perubahan ada di `content/` atau `scripts/`.

## Referensi
- [Build workflow](build-workflow.md)
- [Manual editing policy](manual-editing-policy.md)
- [Answering policy](answering-policy.md)
- [Editorial style](editorial-style.md)
