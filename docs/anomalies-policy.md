# Anomalies Policy

## Purpose
Menetapkan aturan penanganan source yang cacat, missing, duplicate, atau noisy.

## Definition of anomaly
Anomali adalah masalah di source DOCX yang membuat data tidak lengkap atau tidak konsisten.

## Logging rules
- Semua anomali dicatat di `content/practice-XX/anomalies.json`.
- Jangan silent-fix tanpa log.

## Placeholder rules
- Jika source hilang, buat placeholder di canonical.
- Jangan mengarang konten placeholder.

## Non-guessing principle
- Jangan menebak teks soal, jawaban, atau passage.
- Jika perlu, beri catatan dan tandai `needs-manual-review`.

## Allowed normalization
- Normalisasi whitespace dan karakter kontrol.
- Membuat line_map dan paragraph_ranges agar konsisten.

## Forbidden normalization
- Menghapus isi substansial tanpa alasan.
- Mengubah wording agar terlihat lebih baik.

## Known cases
- Missing Listening Part B Q33.
- Duplicate Reading Q44 di passage 05.

## Escalation
- Jika anomali mengubah makna, eskalasi ke review manual.

## References
- [Data model](data-model.md)
- [Build workflow](build-workflow.md)
