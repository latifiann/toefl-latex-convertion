# Answering Policy

## Purpose
Aturan untuk pengisian jawaban, confidence, dan evidence.

## Answer status model
- `AI-proposed`: jawaban hasil draft AI.
- `validated`: jawaban sudah diverifikasi sumber lain.

## Confidence labels
- `high`, `medium`, `low`.
- Gunakan `low` bila evidence lemah.

## Validation model
- `needs-manual-review` untuk item yang belum dicek.
- `validated` hanya jika ada referensi atau sumber nyata.

## Structure rules
- Jawaban harus rule-based (grammar, agreement, clause structure).
- Jelaskan alasan singkat dan jelas.

## Reading rules
- Jawaban harus evidence-based.
- Pakai line reference bila `line_map` tersedia.

## Listening rules
- Reconstruction bukan transcript resmi.
- Jika source tidak lengkap, jangan menebak.

## Ambiguity handling
- Jika ada ambiguitas kuat, tulis catatan dan tandai `needs-manual-review`.

## Explanation style
- Bilingual: Indonesia default, English jika lebih tepat.
- Hindari klaim certainty tanpa evidence.

## Examples
Good:
- "Jawaban (B) karena subject-verb agreement; noun tunggal membutuhkan verb tunggal."
- "(C) sesuai line 12-13, penulis menyebut ..."

Bad:
- "Sepertinya (A) benar." tanpa alasan.
- "Pasti (D)" tanpa evidence.

## References
- [Data model](data-model.md)
- [Anomalies policy](anomalies-policy.md)
- [Editorial style](editorial-style.md)
