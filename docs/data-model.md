# Data Model

## Repository data layers
- Source: `source/original/*.docx`
- Canonical: `content/practice-XX/canonical/`
- Derived: `content/practice-XX/derived/`
- Generated: `build/generated-tex/`
- Authoritative: `build/pdf/`

## Practice layout
```
content/practice-01/
  canonical/
    listening/
    structure/
    reading/
  derived/
  anomalies.json
  meta.json
```

## ID conventions
- Listening: `P01-LA-01`, `P01-LB-31`, `P01-LC-39`
- Structure: `P01-ST-01` .. `P01-ST-40`
- Reading: `P01-RC-01-Q01`

## Canonical schema notes
### Structure completion
- `examples[]`: object dengan `title`, `stem`, `choices`, `explanation_lines`.
- `questions[]`: `id`, `source_number`, `prompt`, `choices`.

### Reading section
- `sample_passage_lines[]`: raw lines, preserve token `Line`.
- `examples[]`: format sama dengan Structure.
- `line_map`: mapping line ke index text.
- `paragraph_ranges`: daftar rentang line per paragraf.

### Error identification
- `segments[]` berisi tekstual plus marker underline.

## Derived answer schema
- `proposed_answer`: jawaban draft.
- `validated_answer`: jawaban final.
- `confidence_label`: `high|medium|low`.
- `validation_status`: `needs-manual-review|validated`.

## Anomaly schema
- `anomalies[]`: id, severity, section, detail.
- `canonical_placeholder_id` jika ada placeholder.

## References
- [Build workflow](build-workflow.md)
- [Answering policy](answering-policy.md)
- [Anomalies policy](anomalies-policy.md)
