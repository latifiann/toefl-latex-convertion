# Manual Editing Policy

## Purpose
Menentukan file mana yang boleh diedit manual dan mana yang tidak boleh.

## Safe manual edits
- `content/**/canonical/`
- `content/**/derived/`
- `scripts/`
- `tex/preamble/`
- `docs/`
- `AGENTS.md`

## Unsafe manual edits
- `build/generated-tex/*.tex`
- `build/pdf/*.pdf`

## Persistent vs non-persistent
- Perubahan di canonical/derived bersifat permanen.
- Perubahan di `build/` bersifat sementara dan akan ditimpa.

## Temporary preview editing
- Jika perlu tweak `.tex` untuk preview, lakukan cepat lalu buang perubahan.
- Jangan commit perubahan pada `build/`.

## Make edits permanent
Jika perubahan ada di PDF/TeX:
1. Temukan sumbernya di canonical atau renderer.
2. Terapkan perbaikan di sumber.
3. Rebuild PDF.

## Generated file rules
- `build/generated-tex/` hanya untuk output sementara.
- Jangan jadi acuan canonical.

## PDF rules
- Authoritative PDF hanya di `build/pdf/`.
- Jangan menyimpan PDF lain sebagai final.

## Quick decision tree
- Perlu edit konten? Ubah di canonical/derived.
- Perlu edit layout? Ubah di renderer atau preamble.
- Hanya ingin preview? Boleh edit TeX, tapi buang setelahnya.

## References
- [Build workflow](build-workflow.md)
- [Editorial style](editorial-style.md)
