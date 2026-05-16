#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CYRILLIC_TO_LATIN = str.maketrans(
    {
        "А": "A",
        "В": "B",
        "Е": "E",
        "К": "K",
        "М": "M",
        "Н": "H",
        "О": "O",
        "Р": "P",
        "С": "C",
        "Т": "T",
        "Х": "X",
        "а": "a",
        "е": "e",
        "о": "o",
        "р": "p",
        "с": "c",
        "у": "y",
        "х": "x",
    }
)


def write_json_file(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def clean_line(text: str) -> str:
    text = text.translate(CYRILLIC_TO_LATIN)
    text = text.replace("\u200b", "")
    text = text.replace("\ufeff", "")
    text = text.replace("\xa0", " ")
    text = text.replace("\t", " ")
    text = text.replace("…", "...")
    text = text.replace("•", "")
    text = text.replace("(D)He", "(D) He")
    text = text.replace("(D)For", "(D) For")
    text = text.replace("take. off", "take off")
    text = text.replace("andcan", "and can")
    for broken, fixed in {
        " t o ": " to ",
        " a n ": " an ",
        " b e ": " be ",
        " i n ": " in ",
        " o f ": " of ",
        " h e ": " he ",
    }.items():
        text = text.replace(broken, fixed)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:?])", r"\1", text)
    return text


def first_index(lines: list[str], pattern: str, start: int = 0) -> int:
    regex = re.compile(pattern)
    for index in range(start, len(lines)):
        if regex.search(lines[index]):
            return index
    raise ValueError(f"Pattern not found: {pattern}")


def extract_text(docx_path: Path, practice_slug: str) -> tuple[Path, list[str]]:
    extracted_path = ROOT / "build" / "extracted" / f"{practice_slug}.txt"
    extracted_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "textutil",
            "-convert",
            "txt",
            str(docx_path),
            "-output",
            str(extracted_path),
        ],
        check=True,
    )
    raw = extracted_path.read_text(encoding="utf-8")
    raw = raw.replace("\f", "\n")
    lines = [clean_line(line) for line in raw.splitlines()]
    return extracted_path, lines


def normalize_fragment(text: str, strip: bool = False, collapse_spaces: bool = False) -> str:
    text = text.translate(CYRILLIC_TO_LATIN)
    text = text.replace("\u200b", "")
    text = text.replace("\ufeff", "")
    text = text.replace("\xa0", " ")
    text = text.replace("\t", " ")
    text = text.replace("…", "...")
    text = text.replace("•", "")
    text = text.replace("(D)He", "(D) He")
    text = text.replace("(D)For", "(D) For")
    text = text.replace("take. off", "take off")
    text = text.replace("andcan", "and can")
    for broken, fixed in {
        " t o ": " to ",
        " a n ": " an ",
        " b e ": " be ",
        " i n ": " in ",
        " o f ": " of ",
        " h e ": " he ",
    }.items():
        text = text.replace(broken, fixed)
    if collapse_spaces:
        text = re.sub(r"\s+", " ", text)
    if strip:
        text = text.strip()
    return text


def extract_html(docx_path: Path, practice_slug: str) -> tuple[Path, list[dict]]:
    html_path = ROOT / "build" / "extracted" / f"{practice_slug}.html"
    html_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "textutil",
            "-convert",
            "html",
            str(docx_path),
            "-output",
            str(html_path),
        ],
        check=True,
    )
    raw_html = html_path.read_text(encoding="utf-8")
    paragraphs: list[dict] = []
    for match in re.finditer(r'<p class="([^"]+)">(.*?)</p>', raw_html, re.DOTALL):
        inner_html = match.group(2)
        text = html_to_text(inner_html)
        paragraphs.append(
            {
                "class": match.group(1),
                "html": inner_html,
                "text": text,
            }
        )
    return html_path, paragraphs


def html_to_text(inner_html: str, strip: bool = True) -> str:
    inner_html = inner_html.replace('<span class="Apple-converted-space">\xa0</span>', " ")
    inner_html = re.sub(r"<br\s*/?>", "\n", inner_html)
    inner_html = re.sub(r"<[^>]+>", "", inner_html)
    text = html.unescape(inner_html)
    return normalize_fragment(text, strip=strip, collapse_spaces=False)


def find_html_paragraph_index(paragraphs: list[dict], pattern: str, start: int = 0) -> int:
    regex = re.compile(pattern)
    for index in range(start, len(paragraphs)):
        if regex.search(paragraphs[index]["text"]):
            return index
    raise ValueError(f"HTML paragraph pattern not found: {pattern}")


def collect_html_text_lines(paragraphs: list[dict], start: int, end: int) -> list[str]:
    lines: list[str] = []
    for paragraph in paragraphs[start:end]:
        for part in paragraph["text"].splitlines():
            cleaned = clean_line(part)
            if cleaned:
                lines.append(cleaned)
    return lines


def parse_underlined_segments(inner_html: str) -> list[dict]:
    inner_html = inner_html.replace('<span class="Apple-converted-space">\xa0</span>', " ")
    pieces = re.split(r'(<span class="s1">.*?</span>)', inner_html)
    segments: list[dict] = []
    first_plain = True
    for piece in pieces:
        if not piece:
            continue
        span_match = re.fullmatch(r'<span class="s1">(.*?)</span>', piece)
        if span_match:
            span_text = html.unescape(span_match.group(1))
            span_text = normalize_fragment(span_text, strip=False, collapse_spaces=False)
            marker_match = re.match(r"^(.*)\(([A-D])\)\s*$", span_text)
            if marker_match:
                segments.append(
                    {
                        "text": marker_match.group(1),
                        "underlined": True,
                        "marker": marker_match.group(2),
                    }
                )
            else:
                segments.append({"text": span_text, "underlined": True, "marker": ""})
            continue

        plain_text = html_to_text(piece, strip=False)
        if first_plain:
            plain_text = re.sub(r"^\d+\.\s*", "", plain_text)
            first_plain = False
        marker_prefix = re.match(r"^\(([A-D])\)(.*)$", plain_text, re.DOTALL)
        if marker_prefix and segments and segments[-1].get("underlined") and not segments[-1].get("marker"):
            segments[-1]["marker"] = marker_prefix.group(1)
            plain_text = marker_prefix.group(2)
        if plain_text != "":
            segments.append({"text": plain_text, "underlined": False})
    return segments


def collect_nonempty_lines(lines: list[str]) -> list[str]:
    return [clean_line(line) for line in lines if clean_line(line)]


def parse_choice_line(line: str) -> tuple[str, str] | None:
    match = re.match(r"^\((?P<letter1>[A-D])\s*\)?\s*(?P<text1>.*)$", line)
    if match:
        return match.group("letter1"), clean_line(match.group("text1"))

    match = re.match(r"^(?P<letter2>[A-D])\s*\)\s*(?P<text2>.*)$", line)
    if match:
        return match.group("letter2"), clean_line(match.group("text2"))

    return None


def collect_error_examples(paragraphs: list[dict], start: int, end: int) -> list[dict]:
    examples: list[dict] = []
    index = start
    while index < end:
        text = paragraphs[index]["text"]
        if not text.startswith("EXAMPLE"):
            index += 1
            continue
        title = clean_line(text)
        sentence_segments = parse_underlined_segments(paragraphs[index + 1]["html"])
        explanation_lines: list[str] = []
        index += 2
        while index < end and not paragraphs[index]["text"].startswith("EXAMPLE"):
            paragraph_text = clean_line(paragraphs[index]["text"])
            if paragraph_text:
                explanation_lines.append(paragraph_text)
            index += 1
        examples.append(
            {
                "title": title,
                "sentence_segments": sentence_segments,
                "explanation_lines": explanation_lines,
            }
        )
    return examples


def collect_multiple_choice_examples(paragraphs: list[dict], start: int, end: int) -> list[dict]:
    examples: list[dict] = []
    index = start
    while index < end:
        title = clean_line(paragraphs[index]["text"])
        if not title.startswith("EXAMPLE"):
            index += 1
            continue

        index += 1
        while index < end and not clean_line(paragraphs[index]["text"]):
            index += 1
        if index >= end:
            break

        stem = clean_line(paragraphs[index]["text"])
        index += 1

        choices: dict[str, str] = {}
        while index < end and len(choices) < 4:
            line = clean_line(paragraphs[index]["text"])
            if not line:
                index += 1
                continue
            choice_match = parse_choice_line(line)
            if not choice_match:
                break
            choices[choice_match[0]] = choice_match[1]
            index += 1

        explanation_lines: list[str] = []
        while index < end:
            line = clean_line(paragraphs[index]["text"])
            if not line:
                index += 1
                continue
            if line.startswith("EXAMPLE"):
                break
            explanation_lines.append(line)
            index += 1

        examples.append(
            {
                "title": title,
                "stem": stem,
                "choices": choices,
                "explanation_lines": explanation_lines,
            }
        )
    return examples


def collect_error_render_segments_by_number(paragraphs: list[dict], start: int, end: int) -> dict[int, list[dict]]:
    mapping: dict[int, list[dict]] = {}
    for paragraph in paragraphs[start:end]:
        text = paragraph["text"]
        match = re.match(r"^(\d+)\s*\.\s", text)
        if not match:
            continue
        mapping[int(match.group(1))] = parse_underlined_segments(paragraph["html"])
    return mapping


def collect_paragraphs(lines: list[str]) -> list[str]:
    paragraphs: list[str] = []
    current = ""
    for original in lines:
        line = clean_line(original)
        if not line:
            if current:
                paragraphs.append(current.strip())
                current = ""
            continue
        if current.endswith("-"):
            current = current[:-1] + line
        else:
            current = f"{current} {line}".strip()
    if current:
        paragraphs.append(current.strip())
    paragraphs = [re.sub(r"\bLine\s+", "", paragraph) for paragraph in paragraphs]
    return paragraphs


def build_line_map(lines: list[str]) -> list[dict]:
    mapped: list[dict] = []
    for original in lines:
        line = clean_line(original)
        if not line:
            continue
        line = re.sub(r"^Line\s+", "", line)
        line = re.sub(r"([A-Za-z])Line\s+([A-Za-z])", r"\1\2", line)
        mapped.append({"line": len(mapped) + 1, "text": line})
    return mapped


def line_map_to_paragraphs(line_map: list[dict]) -> list[str]:
    paragraphs: list[str] = []
    current = ""
    for item in line_map:
        text = item["text"]
        if current.endswith("-"):
            current = current[:-1] + text
        else:
            current = f"{current} {text}".strip()
    if current:
        paragraphs.append(current)
    return paragraphs


def infer_reading_paragraph_ranges(lines: list[str], line_map: list[dict]) -> list[dict]:
    if not line_map:
        return []

    ranges: list[dict] = []
    current_start: int | None = None
    current_line = 0

    for original in lines:
        cleaned = clean_line(original)
        if not cleaned:
            if current_start is not None:
                ranges.append({"start": current_start, "end": current_line})
                current_start = None
            continue

        current_line += 1
        if current_start is None:
            current_start = current_line

    if current_start is not None:
        ranges.append({"start": current_start, "end": current_line})

    if not ranges or current_line != len(line_map):
        return [{"start": 1, "end": len(line_map)}]

    return ranges


def extract_referenced_lines(prompt: str) -> dict | None:
    match = re.search(r"\b[Ll]ines?\s+(\d+)(?:\s*-\s*(\d+))?", prompt)
    if not match:
        return None
    start = int(match.group(1))
    end = int(match.group(2) or start)
    return {"start": start, "end": end}


def parse_question_blocks(lines: list[str], id_builder, include_missing: dict[int, dict] | None = None) -> list[dict]:
    questions: list[dict] = []
    include_missing = include_missing or {}
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r"^(\d+)\s*(?:\.|\))?\s*(.*)$", line)
        if not match:
            i += 1
            continue
        source_number = int(match.group(1))
        while include_missing:
            missing_numbers = sorted(n for n in include_missing if n < source_number)
            if not missing_numbers:
                break
            missing_number = missing_numbers[0]
            questions.append(include_missing.pop(missing_number))
        question = {
            "id": id_builder(source_number, len(questions) + 1),
            "source_number": source_number,
        }
        tail = clean_line(match.group(2))
        prompt_parts: list[str] = []
        choices: dict[str, str] = {}
        if tail:
            choice_match = parse_choice_line(tail)
            if choice_match:
                choices[choice_match[0]] = choice_match[1]
            else:
                prompt_parts.append(tail)
        i += 1
        while i < len(lines) and not re.match(r"^\d+\s*(?:\.|\))?\s*", lines[i]):
            next_line = lines[i]
            if not next_line:
                i += 1
                continue
            choice_match = parse_choice_line(next_line)
            if choice_match:
                choices[choice_match[0]] = choice_match[1]
            else:
                prompt_parts.append(clean_line(next_line))
            i += 1
        if prompt_parts:
            question["prompt"] = " ".join(prompt_parts)
        question["choices"] = choices
        questions.append(question)
    for missing_number in sorted(include_missing):
        questions.append(include_missing[missing_number])
    return questions


def reading_passage_markers(lines: list[str]) -> list[tuple[int, int, int]]:
    markers: list[tuple[int, int, int]] = []
    for index, line in enumerate(lines):
        match = re.match(r"^Questions\s+(\d+)-(\d+)$", line)
        if match:
            markers.append((index, int(match.group(1)), int(match.group(2))))
    return markers


def question_choices_complete(question: dict) -> bool:
    return all(letter in question.get("choices", {}) for letter in ["A", "B", "C", "D"])


def build_listening(practice_id: str, lines: list[str], html_paragraphs: list[dict], out_dir: Path, anomalies: list[dict]) -> None:
    part_a_index = first_index(lines, r"^Part A$")
    part_b_index = first_index(lines, r"^Part B$", part_a_index)
    part_c_index = first_index(lines, r"^Part C$", part_b_index)
    section_2_index = first_index(lines, r"^Section 2$", part_c_index)

    part_a_question_index = first_index(lines, r"^1\s*\.\s*(?:\(A\)|A\))", part_a_index)
    part_b_question_index = first_index(lines, r"^31\s*\.\s*(?:\(A\)|A\))", part_b_index)
    part_c_question_index = first_index(lines, r"^\d+\s*\.\s*(?:\(A\)|A\))", part_c_index)

    html_part_a_index = find_html_paragraph_index(html_paragraphs, r"^Part A$", 0)
    html_part_b_index = find_html_paragraph_index(html_paragraphs, r"^Part B$", html_part_a_index)
    html_part_c_index = find_html_paragraph_index(html_paragraphs, r"^Part C$", html_part_b_index)
    html_section_2_index = find_html_paragraph_index(html_paragraphs, r"^Section 2$", html_part_c_index)

    html_part_a_example_index = find_html_paragraph_index(html_paragraphs, r"^Listen to the following example\.$", html_part_a_index)
    html_part_b_example_index = find_html_paragraph_index(html_paragraphs, r"^Listen to the following example:$", html_part_b_index)
    html_part_c_example_index = find_html_paragraph_index(html_paragraphs, r"^Listen to this sample talk\.$", html_part_c_index)

    html_part_a_question_index = find_html_paragraph_index(html_paragraphs, r"^1\.\s", html_part_a_index)
    html_part_b_question_index = find_html_paragraph_index(html_paragraphs, r"^31\.\s", html_part_b_index)
    html_part_c_question_index = find_html_paragraph_index(html_paragraphs, r"^\d+\.\s", html_part_c_example_index)

    part_a_meta = {
        "practice_id": practice_id,
        "section": "listening",
        "part": "A",
        "directions": collect_html_text_lines(html_paragraphs, html_part_a_index + 1, html_part_a_example_index),
        "example_lines": collect_html_text_lines(html_paragraphs, html_part_a_example_index, html_part_a_question_index),
    }
    part_b_meta = {
        "practice_id": practice_id,
        "section": "listening",
        "part": "B",
        "directions": collect_html_text_lines(html_paragraphs, html_part_b_index + 1, html_part_b_example_index),
        "example_lines": collect_html_text_lines(html_paragraphs, html_part_b_example_index, html_part_b_question_index),
    }
    part_c_meta = {
        "practice_id": practice_id,
        "section": "listening",
        "part": "C",
        "directions": collect_html_text_lines(html_paragraphs, html_part_c_index + 1, html_part_c_example_index),
        "example_lines": collect_html_text_lines(html_paragraphs, html_part_c_example_index, html_part_c_question_index),
    }

    part_a_questions = parse_question_blocks(
        lines[part_a_question_index:part_b_index],
        lambda source_number, _: f"{practice_id}-LA-{source_number:02d}",
    )
    part_b_questions = parse_question_blocks(
        lines[part_b_question_index:part_c_index],
        lambda source_number, _: f"{practice_id}-LB-{source_number:02d}",
    )
    part_c_questions = parse_question_blocks(
        lines[part_c_question_index:section_2_index],
        lambda source_number, _: f"{practice_id}-LC-{source_number:02d}",
    )

    part_c_first_number = part_c_questions[0]["source_number"] if part_c_questions else 39
    expected_part_b_numbers = list(range(31, part_c_first_number))
    part_b_numbers = [question["source_number"] for question in part_b_questions]
    missing_part_b_numbers = [number for number in expected_part_b_numbers if number not in part_b_numbers]
    part_b_meta["expected_source_range"] = [31, expected_part_b_numbers[-1]] if expected_part_b_numbers else [31, 30]
    if missing_part_b_numbers:
        missing_questions = {
            number: {
                "id": f"{practice_id}-LB-{number:02d}",
                "source_number": number,
                "missing_from_source": True,
                "prompt": f"[Question {number} is missing from the DOCX source.]",
                "choices": {},
                "notes": f"Placeholder added to preserve the documented Part B source range 31-{expected_part_b_numbers[-1]}.",
            }
            for number in missing_part_b_numbers
        }
        part_b_questions = parse_question_blocks(
            lines[part_b_question_index:part_c_index],
            lambda source_number, _: f"{practice_id}-LB-{source_number:02d}",
            include_missing=missing_questions,
        )
        for missing_number in missing_part_b_numbers:
            anomalies.append(
                {
                    "id": f"listening-part-b-missing-{missing_number}",
                    "severity": "high",
                    "section": "listening",
                    "detail": f"Question {missing_number} is absent from the DOCX source. A placeholder item was created in canonical content instead of guessing its text.",
                    "canonical_placeholder_id": f"{practice_id}-LB-{missing_number:02d}",
                }
            )
    elif part_b_numbers != expected_part_b_numbers:
        anomalies.append(
            {
                "id": "listening-part-b-unexpected-numbering",
                "severity": "high",
                "section": "listening",
                "detail": f"Part B numbering did not match the expected extracted sequence 31-{expected_part_b_numbers[-1]}.",
                "observed_source_numbers": part_b_numbers,
            }
        )

    part_a_meta["questions"] = part_a_questions
    part_b_meta["questions"] = part_b_questions
    part_c_meta["questions"] = part_c_questions

    write_json_file(out_dir / "canonical" / "listening" / "part-a.json", part_a_meta)
    write_json_file(out_dir / "canonical" / "listening" / "part-b.json", part_b_meta)
    write_json_file(out_dir / "canonical" / "listening" / "part-c.json", part_c_meta)


def build_structure(practice_id: str, lines: list[str], html_paragraphs: list[dict], out_dir: Path) -> None:
    section_2_index = first_index(lines, r"^Section 2$")
    section_3_index = first_index(lines, r"^Section 3", section_2_index)
    completion_directions_index = first_index(lines, r"^DIRECTIONS: Questions 1-15", section_2_index)
    completion_marker = first_index(lines, r"^1\s*\.\s", section_2_index)
    error_directions_index = first_index(lines, r"^DIRECTIONS: In questions 16-40", completion_marker)
    error_questions_index = first_index(lines, r"^16\s*\.\s", error_directions_index)

    html_section_2_index = find_html_paragraph_index(html_paragraphs, r"^Section 2$", 0)
    html_completion_directions_index = find_html_paragraph_index(html_paragraphs, r"^DIRECTIONS: Questions 1-15", html_section_2_index)
    html_completion_example_index = find_html_paragraph_index(html_paragraphs, r"^EXAMPLE I$", html_completion_directions_index)
    html_completion_question_index = find_html_paragraph_index(html_paragraphs, r"^1\s*\.\s", html_completion_example_index)
    html_error_directions_index = find_html_paragraph_index(html_paragraphs, r"^DIRECTIONS: In questions 16-40", html_completion_question_index)
    html_error_example_index = find_html_paragraph_index(html_paragraphs, r"^EXAMPLE I$", html_error_directions_index)
    html_error_question_index = find_html_paragraph_index(html_paragraphs, r"^16\s*\.\s", html_error_example_index)

    intro = collect_html_text_lines(html_paragraphs, html_section_2_index + 2, html_completion_directions_index)
    completion_directions = collect_html_text_lines(html_paragraphs, html_completion_directions_index, html_completion_example_index)
    completion_examples = collect_multiple_choice_examples(html_paragraphs, html_completion_example_index, html_completion_question_index)
    error_directions = collect_html_text_lines(html_paragraphs, html_error_directions_index, html_error_example_index)
    error_examples = collect_error_examples(html_paragraphs, html_error_example_index, html_error_question_index)
    error_render_segments_by_number = collect_error_render_segments_by_number(html_paragraphs, html_error_question_index, html_section_3_index := find_html_paragraph_index(html_paragraphs, r"^Section 3", html_error_question_index))

    completion_questions = parse_question_blocks(
        lines[completion_marker:error_directions_index],
        lambda source_number, _: f"{practice_id}-ST-{source_number:02d}",
    )
    error_questions = parse_question_blocks(
        lines[error_questions_index:section_3_index],
        lambda source_number, _: f"{practice_id}-ST-{source_number:02d}",
    )

    completion_data = {
        "practice_id": practice_id,
        "section": "structure",
        "subtype": "completion",
        "choice_mode": "external-options",
        "intro": intro,
        "directions": completion_directions,
        "examples": completion_examples,
        "questions": completion_questions,
    }

    for question in error_questions:
        render_segments = error_render_segments_by_number.get(question["source_number"])
        if render_segments:
            question["render_segments"] = render_segments

    error_data = {
        "practice_id": practice_id,
        "section": "structure",
        "subtype": "error-identification",
        "choice_mode": "embedded-markers",
        "directions": error_directions,
        "examples": error_examples,
        "questions": error_questions,
    }

    write_json_file(out_dir / "canonical" / "structure" / "completion.json", completion_data)
    write_json_file(out_dir / "canonical" / "structure" / "error-identification.json", error_data)


def build_reading(practice_id: str, lines: list[str], html_paragraphs: list[dict], out_dir: Path, anomalies: list[dict]) -> None:
    section_3_index = first_index(lines, r"^Section 3")
    markers = reading_passage_markers(lines)
    intro_end = markers[0][0]
    first_start, first_end = markers[0][1], markers[0][2]

    html_section_3_index = find_html_paragraph_index(html_paragraphs, r"^Section 3", 0)
    html_time_index = find_html_paragraph_index(html_paragraphs, r"^Time 55 minutes$", html_section_3_index)
    html_directions_index = find_html_paragraph_index(html_paragraphs, r"^DIRECTIONS: In this section", html_time_index)
    html_read_passage_index = find_html_paragraph_index(html_paragraphs, r"^Read the following passage:$", html_directions_index)
    html_reading_example_index = find_html_paragraph_index(html_paragraphs, r"^EXAMPLE I$", html_read_passage_index)
    html_first_marker_index = find_html_paragraph_index(
        html_paragraphs,
        rf"^Questions\s*{first_start}\s*-\s*{first_end}$",
        html_reading_example_index,
    )

    reading_section = {
        "practice_id": practice_id,
        "section": "reading",
        "time_label": clean_line(html_paragraphs[html_time_index]["text"]),
        "directions": collect_html_text_lines(html_paragraphs, html_directions_index, html_read_passage_index),
        "sample_passage_lines": collect_html_text_lines(html_paragraphs, html_read_passage_index, html_reading_example_index),
        "examples": collect_multiple_choice_examples(html_paragraphs, html_reading_example_index, html_first_marker_index),
    }
    write_json_file(out_dir / "canonical" / "reading" / "section.json", reading_section)

    for passage_number, (marker_index, source_start, source_end) in enumerate(markers, start=1):
        next_marker_index = markers[passage_number][0] if passage_number < len(markers) else len(lines)
        question_index = first_index(lines, rf"^{source_start}\.\s", marker_index)
        passage_lines = lines[marker_index + 1 : question_index]
        question_lines = lines[question_index:next_marker_index]
        line_map = build_line_map(passage_lines)

        questions = parse_question_blocks(
            question_lines,
            lambda source_number, local_index, passage_number=passage_number: f"{practice_id}-RC-{passage_number:02d}-Q{local_index:02d}",
        )
        questions = sorted(questions, key=lambda question: question["source_number"])

        if passage_number == 5:
            duplicate_candidates = [question for question in questions if question["source_number"] == 44]
            if len(duplicate_candidates) > 1:
                questions = [
                    question
                    for question in questions
                    if not (
                        question["source_number"] == 44
                        and "not a trace" in question.get("prompt", "").lower()
                    )
                ]
                anomalies.append(
                    {
                        "id": "reading-passage-05-duplicate-44",
                        "severity": "medium",
                        "section": "reading",
                        "detail": "The extracted DOCX text contains a duplicate question 44 in passage 05 that refers to the previous passage. The duplicate was excluded from canonical questions.",
                    }
                )

        for local_index, question in enumerate(questions, start=1):
            question["id"] = f"{practice_id}-RC-{passage_number:02d}-Q{local_index:02d}"
            referenced_lines = extract_referenced_lines(question.get("prompt", ""))
            if referenced_lines:
                question["referenced_lines"] = referenced_lines

        passage_text = line_map_to_paragraphs(line_map)
        passage_md = [f"# Passage {passage_number:02d}", "", f"Source question range: {source_start}-{source_end}", ""]
        passage_md.extend(passage_text)
        (out_dir / "canonical" / "reading" / f"passage-{passage_number:02d}.md").write_text(
            "\n\n".join(passage_md).strip() + "\n",
            encoding="utf-8",
        )

        question_data = {
            "practice_id": practice_id,
            "section": "reading",
            "passage_id": f"{practice_id}-RC-{passage_number:02d}",
            "source_question_range": [source_start, source_end],
            "line_map": line_map,
            "paragraph_ranges": infer_reading_paragraph_ranges(passage_lines, line_map),
            "questions": questions,
        }
        write_json_file(
            out_dir / "canonical" / "reading" / f"passage-{passage_number:02d}.questions.json",
            question_data,
        )


def build_structure_answers(practice_id: str, out_dir: Path) -> None:
    answers: list[dict] = []
    for structure_file in [
        out_dir / "canonical" / "structure" / "completion.json",
        out_dir / "canonical" / "structure" / "error-identification.json",
    ]:
        data = json.loads(structure_file.read_text(encoding="utf-8"))
        for question in data.get("questions", []):
            answers.append(
                {
                    "id": question["id"],
                    "source_number": question.get("source_number"),
                    "subtype": data.get("subtype"),
                    "proposed_answer": None,
                    "validated_answer": None,
                    "validation_status": "unvalidated",
                    "validation_source": "",
                    "confidence_label": None,
                    "status": "not-reviewed",
                    "grammar_rule": "",
                    "incorrect_marker": "",
                    "correct_form": "",
                    "rationale_id": "",
                    "rationale_en": "",
                    "needs_manual_review": False,
                }
            )

    write_json_file(
        out_dir / "derived" / "structure.answers.ai.json",
        {
            "practice_id": practice_id,
            "section": "structure",
            "status": "ai-draft",
            "language_policy": "bilingual-id-priority-with-english-when-more-precise",
            "answers": answers,
        },
    )


def build_reading_answers(practice_id: str, out_dir: Path) -> None:
    answers: list[dict] = []
    for reading_file in sorted((out_dir / "canonical" / "reading").glob("passage-*.questions.json")):
        data = json.loads(reading_file.read_text(encoding="utf-8"))
        for question in data.get("questions", []):
            answers.append(
                {
                    "id": question["id"],
                    "passage_id": data.get("passage_id"),
                    "source_number": question.get("source_number"),
                    "proposed_answer": None,
                    "validated_answer": None,
                    "validation_status": "unvalidated",
                    "validation_source": "",
                    "confidence_label": None,
                    "status": "not-reviewed",
                    "evidence_refs": [],
                    "evidence_quote": "",
                    "rationale_id": "",
                    "rationale_en": "",
                    "needs_manual_review": False,
                }
            )

    write_json_file(
        out_dir / "derived" / "reading.answers.ai.json",
        {
            "practice_id": practice_id,
            "section": "reading",
            "status": "ai-draft",
            "language_policy": "bilingual-id-priority-with-english-when-more-precise",
            "answers": answers,
        },
    )


def build_listening_answers(practice_id: str, out_dir: Path) -> None:
    answers: list[dict] = []
    for part_file in [
        out_dir / "canonical" / "listening" / "part-a.json",
        out_dir / "canonical" / "listening" / "part-b.json",
        out_dir / "canonical" / "listening" / "part-c.json",
    ]:
        data = json.loads(part_file.read_text(encoding="utf-8"))
        for question in data.get("questions", []):
            missing_from_source = question.get("missing_from_source", False)
            answers.append(
                {
                    "id": question["id"],
                    "part": data.get("part"),
                    "source_number": question.get("source_number"),
                    "missing_from_source": missing_from_source,
                    "proposed_answer": None,
                    "validated_answer": None,
                    "validation_status": "unvalidated",
                    "validation_source": "",
                    "confidence_label": None,
                    "status": "blocked-missing-source" if missing_from_source else "not-reviewed",
                    "rationale_id": "",
                    "rationale_en": "",
                    "needs_manual_review": False,
                }
            )

    write_json_file(
        out_dir / "derived" / "listening.answers.ai.json",
        {
            "practice_id": practice_id,
            "section": "listening",
            "status": "ai-draft",
            "language_policy": "bilingual-id-priority-with-english-when-more-precise",
            "answering_policy": "defer-reconstruction-until-better-key-coverage",
            "answers": answers,
        },
    )


def build_listening_reconstructions(out_dir: Path) -> None:
    for part in ["a", "b", "c"]:
        part_file = out_dir / "canonical" / "listening" / f"part-{part}.json"
        part_data = json.loads(part_file.read_text(encoding="utf-8"))
        reconstruction = {
            "practice_id": part_data.get("practice_id"),
            "section": "listening",
            "part": part.upper(),
            "ai_generated": True,
            "kind": "reconstruction",
            "note": "The DOCX source only includes answer choices, so these fields are placeholders for plausible reconstructions rather than official transcripts.",
            "questions": [
                {
                    "id": question["id"],
                    "source_number": question.get("source_number"),
                    "missing_from_source": question.get("missing_from_source", False),
                    "speaker_1": "",
                    "speaker_2": "",
                    "narrator_question": "",
                    "proposed_answer": None,
                    "confidence_label": None,
                    "alternate_reconstruction": "",
                    "notes_id": "",
                    "notes_en": "",
                }
                for question in part_data.get("questions", [])
            ],
        }
        write_json_file(out_dir / "derived" / "listening" / f"part-{part}.reconstruction.json", reconstruction)


def build_derived(practice_id: str, out_dir: Path) -> None:
    legacy_answers = out_dir / "derived" / "answers.ai.json"
    if legacy_answers.exists():
        legacy_answers.unlink()

    build_structure_answers(practice_id, out_dir)
    build_reading_answers(practice_id, out_dir)
    build_listening_answers(practice_id, out_dir)
    build_listening_reconstructions(out_dir)

    review_notes = "# Review Notes\n\n- Semua jawaban di folder `derived/` masih `AI-proposed`.\n- Gunakan istilah English ketika lebih natural, tetapi penjelasan inti tetap prioritaskan Bahasa Indonesia.\n- Untuk listening, jangan klaim hasil rekonstruksi sebagai transcript official.\n"
    (out_dir / "derived" / "review-notes.md").write_text(review_notes, encoding="utf-8")


def build_meta(practice_id: str, practice_slug: str, docx_path: Path, extracted_path: Path, extracted_html_path: Path, out_dir: Path) -> None:
    meta = {
        "practice_id": practice_id,
        "practice_slug": practice_slug,
        "title": f"TOEFL Practice {practice_slug.split('-')[-1]}",
        "source_of_truth": "docx",
        "source_docx": str(docx_path.relative_to(ROOT)),
        "extracted_text": str(extracted_path.relative_to(ROOT)),
        "extracted_html": str(extracted_html_path.relative_to(ROOT)),
        "language_policy": "bilingual-id-priority-with-english-when-more-precise",
        "listening_reconstruction_policy": "reconstruction-only",
        "official_answer_key_available": False,
        "derived_answer_layout": "split-by-section",
    }
    write_json_file(out_dir / "meta.json", meta)


def build_anomalies(out_dir: Path, anomalies: list[dict]) -> None:
    data = {
        "anomalies": anomalies,
        "note": "Anomalies record source problems or deliberate normalization decisions. Canonical files should stay close to the DOCX while avoiding silent guessing.",
    }
    write_json_file(out_dir / "anomalies.json", data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--practice-id", default="P01")
    parser.add_argument("--source", default="source/original/practice-01.docx")
    args = parser.parse_args()

    practice_slug = f"practice-{args.practice_id[-2:]}"
    source_path = (ROOT / args.source).resolve()
    out_dir = ROOT / "content" / practice_slug

    extracted_path, lines = extract_text(source_path, practice_slug)
    extracted_html_path, html_paragraphs = extract_html(source_path, practice_slug)
    anomalies: list[dict] = [
        {
            "id": "normalization-whitespace-and-formfeed",
            "severity": "low",
            "section": "global",
            "detail": "Whitespace, form-feed characters, zero-width characters, and obvious mixed-script confusables were normalized during ingestion.",
        }
    ]

    build_meta(args.practice_id, practice_slug, source_path, extracted_path, extracted_html_path, out_dir)
    build_listening(args.practice_id, lines, html_paragraphs, out_dir, anomalies)
    build_structure(args.practice_id, lines, html_paragraphs, out_dir)
    build_reading(args.practice_id, lines, html_paragraphs, out_dir, anomalies)
    build_derived(args.practice_id, out_dir)
    build_anomalies(out_dir, anomalies)


if __name__ == "__main__":
    main()
