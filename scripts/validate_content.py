#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

VALID_ANSWER_VALUES = {"A", "B", "C", "D"}
VALID_CONFIDENCE_VALUES = {None, "high", "medium", "low"}
VALID_VALIDATION_STATUS = {"unvalidated", "validated", "conflict", "needs-manual-review"}


def load_json_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_choices(question: dict, require_choices: bool = True) -> bool:
    if question.get("missing_from_source"):
        return True
    if not require_choices:
        return bool(question.get("prompt"))
    choices = question.get("choices", {})
    return all(letter in choices and choices[letter] for letter in ["A", "B", "C", "D"])


def collect_canonical_ids(question_sets: list[dict]) -> list[str]:
    ids: list[str] = []
    for question_set in question_sets:
        for question in question_set.get("questions", []):
            ids.append(question["id"])
    return ids


def line_map_is_contiguous(line_map: list[dict]) -> bool:
    return [item.get("line") for item in line_map] == list(range(1, len(line_map) + 1))


def paragraph_ranges_are_valid(paragraph_ranges: list[dict], line_map_length: int) -> bool:
    if not paragraph_ranges:
        return False
    covered: list[int] = []
    for paragraph_range in paragraph_ranges:
        start = paragraph_range.get("start")
        end = paragraph_range.get("end")
        if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start or end > line_map_length:
            return False
        covered.extend(range(start, end + 1))
    return covered == list(range(1, line_map_length + 1))


def multiple_choice_examples_are_valid(examples: list[dict]) -> bool:
    if not examples:
        return False
    for example in examples:
        if not example.get("title") or not example.get("stem"):
            return False
        choices = example.get("choices", {})
        if not all(letter in choices and choices[letter] for letter in ["A", "B", "C", "D"]):
            return False
        if not example.get("explanation_lines"):
            return False
    return True


def final_answer(entry: dict) -> str | None:
    return entry.get("validated_answer") or entry.get("proposed_answer")


def validate_answer_entry_common(entry: dict, failures: list[str]) -> None:
    if entry.get("confidence_label") not in VALID_CONFIDENCE_VALUES:
        failures.append(f"Invalid confidence_label for {entry['id']}.")
    if entry.get("validation_status") not in VALID_VALIDATION_STATUS:
        failures.append(f"Invalid validation_status for {entry['id']}.")
    for field in ["proposed_answer", "validated_answer"]:
        value = entry.get(field)
        if value is not None and value not in VALID_ANSWER_VALUES:
            failures.append(f"Invalid {field} for {entry['id']}.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--practice-id", default="P01")
    args = parser.parse_args()

    practice_slug = f"practice-{args.practice_id[-2:]}"
    base = ROOT / "content" / practice_slug / "canonical"

    part_a = load_json_file(base / "listening" / "part-a.json")
    part_b = load_json_file(base / "listening" / "part-b.json")
    part_c = load_json_file(base / "listening" / "part-c.json")
    completion = load_json_file(base / "structure" / "completion.json")
    error_identification = load_json_file(base / "structure" / "error-identification.json")
    reading_files = sorted((base / "reading").glob("passage-*.questions.json"))
    reading_sets = [load_json_file(path) for path in reading_files]
    derived_base = ROOT / "content" / practice_slug / "derived"
    structure_answers = load_json_file(derived_base / "structure.answers.ai.json")
    reading_answers = load_json_file(derived_base / "reading.answers.ai.json")
    listening_answers = load_json_file(derived_base / "listening.answers.ai.json")

    failures: list[str] = []

    if len(part_a["questions"]) != 30:
        failures.append(f"Listening Part A expected 30 questions, found {len(part_a['questions'])}.")
    if [question.get("source_number") for question in part_a["questions"]] != list(range(1, 31)):
        failures.append("Listening Part A source numbering is not 1-30.")
    listening_tail_numbers = [question.get("source_number") for question in part_b["questions"] + part_c["questions"]]
    if listening_tail_numbers != list(range(31, 51)):
        failures.append("Listening Part B/C source numbering is not contiguous from 31-50.")
    if len(completion["questions"]) != 15:
        failures.append(f"Structure completion expected 15 questions, found {len(completion['questions'])}.")
    if len(error_identification["questions"]) != 25:
        failures.append(f"Structure error identification expected 25 questions, found {len(error_identification['questions'])}.")
    if len(reading_sets) != 5:
        failures.append(f"Reading expected 5 passages, found {len(reading_sets)}.")

    if not multiple_choice_examples_are_valid(completion.get("examples", [])):
        failures.append("Invalid structured examples for Structure completion.")
    if not reading_sets:
        failures.append("Reading sets are missing.")

    reading_section = load_json_file(base / "reading" / "section.json")
    if not reading_section.get("sample_passage_lines"):
        failures.append("Reading section is missing sample_passage_lines.")
    if not multiple_choice_examples_are_valid(reading_section.get("examples", [])):
        failures.append("Invalid structured examples for Reading section.")

    for reading_set in reading_sets:
        line_map = reading_set.get("line_map", [])
        if not line_map:
            failures.append(f"Missing line_map for {reading_set.get('passage_id', 'unknown-passage')}.")
            continue
        if not line_map_is_contiguous(line_map):
            failures.append(f"Non-contiguous line_map for {reading_set.get('passage_id', 'unknown-passage')}.")
        paragraph_ranges = reading_set.get("paragraph_ranges", [])
        if not paragraph_ranges_are_valid(paragraph_ranges, len(line_map)):
            failures.append(f"Invalid paragraph_ranges for {reading_set.get('passage_id', 'unknown-passage')}.")
        max_line = line_map[-1]["line"]
        for question in reading_set.get("questions", []):
            referenced_lines = question.get("referenced_lines")
            if referenced_lines:
                start = referenced_lines.get("start")
                end = referenced_lines.get("end")
                if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start or end > max_line:
                    failures.append(f"Invalid referenced_lines for {question['id']}.")

    for question_set in [part_a, part_b, part_c, completion, *reading_sets]:
        for question in question_set.get("questions", []):
            if not check_choices(question, require_choices=True):
                failures.append(f"Incomplete choices for {question['id']}.")

    for question in error_identification.get("questions", []):
        if not check_choices(question, require_choices=False):
            failures.append(f"Missing embedded prompt for {question['id']}.")

    canonical_listening_ids = collect_canonical_ids([part_a, part_b, part_c])
    canonical_structure_ids = collect_canonical_ids([completion, error_identification])
    canonical_reading_ids = collect_canonical_ids(reading_sets)

    derived_listening_ids = [entry["id"] for entry in listening_answers.get("answers", [])]
    derived_structure_ids = [entry["id"] for entry in structure_answers.get("answers", [])]
    derived_reading_ids = [entry["id"] for entry in reading_answers.get("answers", [])]

    if canonical_listening_ids != derived_listening_ids:
        failures.append("Listening answer IDs do not match canonical listening IDs.")
    if canonical_structure_ids != derived_structure_ids:
        failures.append("Structure answer IDs do not match canonical structure IDs.")
    if canonical_reading_ids != derived_reading_ids:
        failures.append("Reading answer IDs do not match canonical reading IDs.")

    reading_line_map_by_passage = {
        reading_set["passage_id"]: reading_set.get("line_map", []) for reading_set in reading_sets
    }

    for entry in listening_answers.get("answers", []):
        validate_answer_entry_common(entry, failures)

    for entry in structure_answers.get("answers", []):
        validate_answer_entry_common(entry, failures)
        if entry.get("incorrect_marker") and entry["incorrect_marker"] not in VALID_ANSWER_VALUES:
            failures.append(f"Invalid incorrect_marker for {entry['id']}.")

    for entry in reading_answers.get("answers", []):
        validate_answer_entry_common(entry, failures)
        line_map = reading_line_map_by_passage.get(entry.get("passage_id"), [])
        max_line = line_map[-1]["line"] if line_map else 0
        for ref in entry.get("evidence_refs", []):
            start = ref.get("start")
            end = ref.get("end")
            if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start or end > max_line:
                failures.append(f"Invalid evidence_refs for {entry['id']}.")

    if failures:
        print("Validation failed:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    listening_missing_placeholders = sum(
        1 for question_set in [part_a, part_b, part_c] for question in question_set.get("questions", []) if question.get("missing_from_source")
    )

    print("Validation passed.")
    if listening_missing_placeholders:
        print(f"- Listening: 50 entries including {listening_missing_placeholders} missing-source placeholder(s)")
    else:
        print("- Listening: 50 entries with no missing-source placeholders")
    print("- Structure: 40 questions")
    print("- Reading: 50 canonical questions across 5 passages with source line maps")
    print("- Derived answers: split by section and aligned with canonical IDs")


if __name__ == "__main__":
    main()
