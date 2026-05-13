# Editorial Style Guide

## Purpose and scope
Dokumen ini menetapkan aturan gaya penulisan, format soal, dan konsistensi layout.
Gunakan sebagai acuan utama untuk teks yang dirender ke PDF.

## Language policy
- Default: Bahasa Indonesia.
- Gunakan English bila istilah lebih tepat atau standard (mis. evidence, line_map).
- Jangan mengubah istilah teknis repo (path, field name, ID).

## Typography and spacing
- Konsisten dengan spacing antar soal dan antar blok contoh.
- Jangan menambah font baru tanpa alasan kuat.
- Hindari variasi spacing yang tidak perlu; gunakan pola yang sama di seluruh section.

## Heading order
Gunakan urutan tetap:
1. Directions
2. Examples (jika ada)
3. Questions
4. Answer key (review mode)

## Question formatting rules
### Structure: Sentence Completion
- Format: judul contoh, stem, pilihan (A)-(D), lalu penjelasan.
- Pilihan harus berupa enumerate yang konsisten.

### Reading
- Passage harus menjaga line fidelity dan mempertahankan token "Line".
- Render setiap line sebagai paragraf terpisah.
- Pertanyaan mengikuti passage; contoh memakai format yang sama seperti Structure.

### Error Identification
- Tanda error harus di-underline.
- Spasi dan indent sejajar dengan soal lain.

## Example formatting template
Gunakan struktur berikut untuk contoh (canonical/derived):

```json
{
  "title": "EXAMPLE I",
  "stem": "...",
  "choices": {
    "A": "...",
    "B": "...",
    "C": "...",
    "D": "..."
  },
  "explanation_lines": [
    "..."
  ]
}
```

## Explanation rules
- Jelaskan alasan jawab dengan ringkas.
- Hindari klaim certainty jika tidak ada evidence kuat.
- Reading: selalu refer ke isi passage (line-based bila tersedia).

## Non-negotiable rules
- Jangan menebak konten sumber yang hilang.
- Jangan mengedit output generate sebagai perubahan permanen.
- Jaga konsistensi format antar section dan antar practice.

## References
- [Answering policy](answering-policy.md)
- [Manual editing policy](manual-editing-policy.md)
- [Data model](data-model.md)
