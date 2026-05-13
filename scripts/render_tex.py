#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def latex_escape(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for original, escaped in replacements.items():
        text = text.replace(original, escaped)
    return text


def render_paragraphs(paragraphs: list[str]) -> list[str]:
    rendered: list[str] = []
    for paragraph in paragraphs:
        if not paragraph:
            continue
        rendered.append(latex_escape(paragraph) + r"\par")
    return rendered


def render_multiline_block(lines: list[str]) -> list[str]:
    rendered: list[str] = [r"\begin{exampleblock}"]
    for line in lines:
        if not line:
            continue
        escaped = latex_escape(line)
        if re.match(r"^EXAMPLE\b", line):
            escaped = rf"\textbf{{{escaped}}}"
        rendered.append(escaped + r"\par")
    rendered.append(r"\end{exampleblock}")
    return rendered


def render_multiple_choice_examples(examples: list[dict]) -> list[str]:
    lines: list[str] = []
    for example in examples:
        lines.append(r"\begin{exampleblock}")
        lines.append(rf"\textbf{{{latex_escape(example['title'])}}}\par")
        lines.append(rf"\noindent {latex_escape(example['stem'])}")
        lines.append(r"\begin{enumerate}[label=(\Alph*),leftmargin=*,itemsep=0.2em]")
        for letter in ["A", "B", "C", "D"]:
            lines.append(rf"\item {latex_escape(example['choices'][letter])}")
        lines.append(r"\end{enumerate}")
        lines.append(r"\vspace{0.25\baselineskip}")
        for explanation_line in example.get("explanation_lines", []):
            lines.append(latex_escape(explanation_line) + r"\par")
        lines.append(r"\end{exampleblock}")
    return lines


def render_reading_source_block(lines: list[str]) -> list[str]:
    rendered: list[str] = [r"\begin{exampleblock}", r"\small", r"\sloppy"]
    for line in lines:
        if not line:
            continue
        escaped = latex_escape(line)
        rendered.append(escaped + r"\par")
    rendered.append(r"\end{exampleblock}")
    return rendered


def render_transcript_block(lines: list[str]) -> list[str]:
    rendered: list[str] = [r"\begin{exampleblock}"]
    rendered.append(r"\textbf{Transkrip rekonstruksi AI (draft; bukan resmi)}\par")
    for line in lines:
        if not line:
            continue
        rendered.append(latex_escape(line) + r"\par")
    rendered.append(r"\end{exampleblock}")
    return rendered


def load_answer_map(derived_dir: Path, filename: str) -> dict[str, dict]:
    data = load_json_file(derived_dir / filename)
    return {entry["id"]: entry for entry in data.get("answers", [])}


def load_transcript_map(derived_dir: Path, filename: str) -> dict[str, list[str]]:
    data = load_json_file(derived_dir / filename)
    transcript_map: dict[str, list[str]] = {}
    for question in data.get("questions", []):
        transcript = question.get("transcript_lines") or []
        if transcript:
            transcript_map[question["id"]] = transcript
    return transcript_map


def resolve_final_answer(answer: dict) -> str | None:
    return answer.get("validated_answer") or answer.get("proposed_answer")


def review_label(answer: dict) -> str:
    if answer.get("validated_answer"):
        return "Validated"
    if answer.get("proposed_answer"):
        return "AI-proposed"
    return "Unreviewed"


def should_render_review(answer: dict | None) -> bool:
    if not answer:
        return False
    if resolve_final_answer(answer):
        return True
    return any(
        [
            answer.get("grammar_rule"),
            answer.get("correct_form"),
            answer.get("rationale_id"),
            answer.get("rationale_en"),
            answer.get("evidence_refs"),
            answer.get("evidence_quote"),
            answer.get("needs_manual_review"),
        ]
    )


def format_line_refs(refs: list[dict]) -> str:
    formatted: list[str] = []
    for ref in refs:
        start = ref.get("start")
        end = ref.get("end")
        if start == end:
            formatted.append(f"line {start}")
        else:
            formatted.append(f"lines {start}-{end}")
    return ", ".join(formatted)


def render_error_segments(segments: list[dict]) -> str:
    parts: list[str] = []
    for segment in segments:
        raw_text = segment.get("text", "")
        if not segment.get("underlined") and raw_text and not raw_text.strip():
            parts.append(" ")
            continue
        text = latex_escape(raw_text)
        if segment.get("underlined"):
            marker = segment.get("marker", "")
            parts.append(rf"\uline{{{text}}}({marker})")
        else:
            parts.append(text)
    return "".join(parts)


def render_error_examples(examples: list[dict]) -> list[str]:
    lines: list[str] = []
    for example in examples:
        lines.append(r"\begin{exampleblock}")
        lines.append(rf"\textbf{{{latex_escape(example['title'])}}}\par")
        lines.append(render_error_segments(example.get("sentence_segments", [])) + r"\par")
        for explanation_line in example.get("explanation_lines", []):
            lines.append(latex_escape(explanation_line) + r"\par")
        lines.append(r"\end{exampleblock}")
    return lines


def render_line_map(line_map: list[dict], paragraph_ranges: list[dict]) -> list[str]:
    lines: list[str] = []
    lines.append(r"\begingroup")
    lines.append(r"\small")
    lines.append(r"\sloppy")
    lines.append(r"\setlength{\parskip}{0pt}")
    lines.append(r"\setlength{\parindent}{0pt}")
    for item in line_map:
        lines.append(latex_escape(item["text"]) + r"\par")
    lines.append(r"\endgroup")
    return lines


def render_review_details(answer: dict, context: dict) -> list[str]:
    lines: list[str] = []
    lines.append(r"\begingroup")
    lines.append(r"\setlength{\parskip}{0pt}")
    lines.append(r"\setlength{\parindent}{0pt}")
    lines.append(r"\textbf{Review}\par")
    final_answer = resolve_final_answer(answer)
    if final_answer:
        lines.append(latex_escape(f"Answer: {final_answer}") + r"\par")
    if answer.get("confidence_label"):
        lines.append(latex_escape(f"Confidence: {answer['confidence_label']}") + r"\par")

    if context["section"] == "structure":
        if answer.get("grammar_rule"):
            lines.append(latex_escape(f"Grammar rule: {answer['grammar_rule']}") + r"\par")
        if answer.get("correct_form"):
            lines.append(latex_escape(f"Correct form: {answer['correct_form']}") + r"\par")

    if context["section"] == "reading":
        if answer.get("evidence_refs"):
            lines.append(latex_escape(f"Evidence refs: {format_line_refs(answer['evidence_refs'])}") + r"\par")
        if answer.get("evidence_quote"):
            lines.append(latex_escape(f"Evidence quote: \"{answer['evidence_quote']}\"") + r"\par")

    if answer.get("rationale_id"):
        lines.append(latex_escape(answer["rationale_id"]) + r"\par")
    if answer.get("needs_manual_review"):
        lines.append(latex_escape("Needs manual review: true") + r"\par")
    lines.append(r"\endgroup")
    return lines


def render_question_block(question: dict, answer: dict | None = None, context: dict | None = None) -> list[str]:
    lines: list[str] = []
    context = context or {}
    transcript_lines = context.get("transcript_lines") or []
    if transcript_lines:
        lines.extend(render_transcript_block(transcript_lines))
    source_number = question.get("source_number", "")
    if question.get("missing_from_source"):
        lines.append(rf"\noindent\textbf{{{source_number}.}} {latex_escape(question.get('prompt', '[Missing source question]'))}")
        if question.get("choices"):
            lines.append(r"\begin{enumerate}[label=(\Alph*),leftmargin=*,itemsep=0.2em]")
            for letter in ["A", "B", "C", "D"]:
                lines.append(rf"\item {latex_escape(question['choices'][letter])}")
            lines.append(r"\end{enumerate}")
    else:
        if context.get("section") == "structure" and context.get("subtype") == "error-identification" and question.get("render_segments"):
            lines.append(rf"\noindent\textbf{{{source_number}.}} {render_error_segments(question['render_segments'])}")
        elif question.get("prompt"):
            lines.append(rf"\noindent\textbf{{{source_number}.}} {latex_escape(question['prompt'])}")
        else:
            lines.append(rf"\noindent\textbf{{{source_number}.}}")
        if question.get("choices"):
            lines.append(r"\begin{enumerate}[label=(\Alph*),leftmargin=*,itemsep=0.2em]")
            for letter in ["A", "B", "C", "D"]:
                lines.append(rf"\item {latex_escape(question['choices'][letter])}")
            lines.append(r"\end{enumerate}")
    if should_render_review(answer):
        lines.append(r"\par")
        lines.extend(render_review_details(answer, context))
    lines.append(r"\par")
    if context.get("section") == "structure" and context.get("subtype") == "error-identification":
        lines.append(r"\vspace{\questionblockgap}")
    else:
        lines.append(r"\vspace{0.25\baselineskip}")
    return lines


def render_answer_key_section(title: str, questions: list[dict], answer_map: dict[str, dict]) -> list[str]:
    lines: list[str] = [rf"\subsection*{{{title}}}"]
    answered_items: list[str] = []
    unanswered = 0
    for question in questions:
        answer = answer_map.get(question["id"])
        final_answer = resolve_final_answer(answer or {}) if answer else None
        if final_answer:
            answered_items.append(f"{question['source_number']}: {final_answer}")
        else:
            unanswered += 1

    if unanswered:
        lines.append(latex_escape(f"Answered items shown below. {unanswered} item(s) remain unreviewed."))
    if answered_items:
        lines.append(r"\begin{itemize}[leftmargin=*]")
        for item in answered_items:
            lines.append(rf"\item {latex_escape(item)}")
        lines.append(r"\end{itemize}")
    else:
        lines.append(latex_escape("No answers available yet."))
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--practice-id", default="P01")
    parser.add_argument("--mode", choices=["tryout", "review"], default="tryout")
    args = parser.parse_args()

    practice_slug = f"practice-{args.practice_id[-2:]}"
    canonical = ROOT / "content" / practice_slug / "canonical"
    derived = ROOT / "content" / practice_slug / "derived"
    output_path = ROOT / "build" / "generated-tex" / f"{args.practice_id}-{args.mode}.tex"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stray_pdf_path = output_path.with_suffix(".pdf")
    if stray_pdf_path.exists():
        stray_pdf_path.unlink()

    meta = load_json_file(ROOT / "content" / practice_slug / "meta.json")
    listening_answers: dict[str, dict] = {}
    listening_transcripts: dict[str, list[str]] = {}
    structure_answers: dict[str, dict] = {}
    reading_answers: dict[str, dict] = {}
    if args.mode == "review":
        listening_answers = load_answer_map(derived, "listening.answers.ai.json")
        structure_answers = load_answer_map(derived, "structure.answers.ai.json")
        reading_answers = load_answer_map(derived, "reading.answers.ai.json")

    for part in ["a", "b", "c"]:
        transcript_map = load_transcript_map(derived / "listening", f"part-{part}.reconstruction.json")
        listening_transcripts.update(transcript_map)

    lines: list[str] = [
        r"\documentclass[12pt]{article}",
        r"\input{../../tex/preamble/packages.tex}",
        r"\input{../../tex/preamble/macros.tex}",
        r"\input{../../tex/preamble/style.tex}",
        r"\begin{document}",
        rf"\section*{{{latex_escape(meta['title'])} - {args.mode.title()}}}",
        latex_escape("Source of truth: DOCX only."),
    ]

    listening_files = [
        canonical / "listening" / "part-a.json",
        canonical / "listening" / "part-b.json",
        canonical / "listening" / "part-c.json",
    ]
    lines.append(r"\section*{Listening Comprehension}")
    listening_questions: list[dict] = []
    for part_file in listening_files:
        part = load_json_file(part_file)
        last_transcript_signature: tuple[str, ...] | None = None
        lines.append(rf"\subsection*{{Part {part['part']}}}")
        lines.extend(render_paragraphs(part.get("directions", [])))
        lines.extend(render_multiline_block(part.get("example_lines", [])))
        for question in part.get("questions", []):
            listening_questions.append(question)
            transcript_lines = listening_transcripts.get(question["id"], [])
            transcript_signature = tuple(transcript_lines) if transcript_lines else None
            if transcript_signature and transcript_signature == last_transcript_signature:
                transcript_lines = []
            else:
                last_transcript_signature = transcript_signature
            lines.extend(
                render_question_block(
                    question,
                    listening_answers.get(question["id"]),
                    {
                        "section": "listening",
                        "part": part["part"],
                        "transcript_lines": transcript_lines,
                    },
                )
            )

    structure_files = [
        canonical / "structure" / "completion.json",
        canonical / "structure" / "error-identification.json",
    ]
    lines.append(r"\section*{Structure and Written Expression}")
    structure_questions: list[dict] = []
    for structure_file in structure_files:
        section = load_json_file(structure_file)
        title = "Sentence Completion" if section["subtype"] == "completion" else "Error Identification"
        lines.append(rf"\subsection*{{{title}}}")
        lines.extend(render_paragraphs(section.get("intro", [])))
        lines.extend(render_paragraphs(section.get("directions", [])))
        if section["subtype"] == "completion":
            lines.extend(render_multiple_choice_examples(section.get("examples", [])))
        else:
            lines.extend(render_error_examples(section.get("examples", [])))
        for question in section.get("questions", []):
            structure_questions.append(question)
            lines.extend(render_question_block(question, structure_answers.get(question["id"]), {"section": "structure", "subtype": section["subtype"]}))

    lines.append(r"\section*{Reading Comprehension}")
    reading_section = load_json_file(canonical / "reading" / "section.json")
    if reading_section.get("time_label"):
        lines.append(r"\begin{center}")
        lines.append(rf"\textbf{{{latex_escape(reading_section['time_label'])}}}")
        lines.append(r"\end{center}")
    lines.extend(render_paragraphs(reading_section.get("directions", [])))
    lines.extend(render_reading_source_block(reading_section.get("sample_passage_lines", [])))
    lines.extend(render_multiple_choice_examples(reading_section.get("examples", [])))
    reading_questions: list[dict] = []
    for question_file in sorted((canonical / "reading").glob("passage-*.questions.json")):
        question_data = load_json_file(question_file)
        range_start, range_end = question_data["source_question_range"]
        lines.append(rf"\subsection*{{Questions {range_start}-{range_end}}}")
        lines.extend(render_line_map(question_data.get("line_map", []), question_data.get("paragraph_ranges", [])))
        lines.append(r"\medskip")
        for question in question_data.get("questions", []):
            reading_questions.append(question)
            lines.extend(render_question_block(question, reading_answers.get(question["id"]), {"section": "reading", "passage_id": question_data["passage_id"]}))

    if args.mode == "review":
        lines.append(r"\newpage")
        lines.append(r"\section*{Answer Key Appendix}")
        lines.extend(render_answer_key_section("Listening", listening_questions, listening_answers))
        lines.extend(render_answer_key_section("Structure", structure_questions, structure_answers))
        lines.extend(render_answer_key_section("Reading", reading_questions, reading_answers))

    lines.append(r"\end{document}")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(output_path.relative_to(ROOT))


if __name__ == "__main__":
    main()
