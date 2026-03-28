"""Split contract text into structured clauses."""
from __future__ import annotations

import re

from models.review import Clause


class ContractSplitter:
    """Split contract text by headings and paragraphs."""

    heading_pattern = re.compile(
        r"^(?:(?:第[一二三四五六七八九十百零\d]+条)[\s：:、.)）]*.*|(?:\d+(?:\.\d+)*[.、)]\s*.+))$",
        re.MULTILINE,
    )
    parent_heading_pattern = re.compile(r"^第[一二三四五六七八九十百零\d]+条(?:[\s：:、.)）].*)?$")
    child_heading_pattern = re.compile(r"^\d+(?:\.\d+)*[.、)]?\s*.+$")

    def split(self, text: str) -> list[Clause]:
        """Convert contract text into a sequence of clauses."""
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not normalized:
            return []

        matches = list(self.heading_pattern.finditer(normalized))
        if matches:
            return self._split_by_headings(normalized, matches)
        return self._split_by_paragraphs(normalized)

    def _split_by_headings(self, text: str, matches: list[re.Match[str]]) -> list[Clause]:
        clauses: list[Clause] = []
        clause_index = 1

        for index, match in enumerate(matches):
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            chunk = text[start:end].strip()
            title_line, body_text = self._split_heading_chunk(chunk)
            if not title_line:
                continue

            clause_text = self._resolve_clause_text(title_line, body_text)
            if not clause_text:
                continue

            clauses.append(
                Clause(
                    clause_id=f"clause_{clause_index}",
                    title=title_line[:80],
                    text=clause_text,
                    source_index=clause_index,
                )
            )
            clause_index += 1
        return clauses

    def _split_by_paragraphs(self, text: str) -> list[Clause]:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
        clauses: list[Clause] = []
        for index, paragraph in enumerate(paragraphs, start=1):
            title = self._derive_title(paragraph, index)
            clauses.append(Clause(clause_id=f"clause_{index}", title=title, text=paragraph, source_index=index))
        return clauses

    def _derive_title(self, clause_text: str, index: int) -> str:
        sentence = re.split(r"[。；\n]", clause_text, maxsplit=1)[0].strip()
        if not sentence:
            return f"Clause {index}"
        return sentence[:40]

    @staticmethod
    def _split_heading_chunk(chunk: str) -> tuple[str, str]:
        lines = [line.strip() for line in chunk.splitlines()]
        if not lines:
            return "", ""

        title_line = lines[0]
        body_lines = [line for line in lines[1:] if line]
        body_text = "\n".join(body_lines).strip()
        return title_line, body_text

    def _resolve_clause_text(self, title_line: str, body_text: str) -> str:
        if body_text:
            return body_text

        if self.child_heading_pattern.match(title_line):
            return title_line

        if self.parent_heading_pattern.match(title_line):
            return ""

        return title_line
