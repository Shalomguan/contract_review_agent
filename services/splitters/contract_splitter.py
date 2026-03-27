"""Split contract text into structured clauses."""
from __future__ import annotations

import re

from models.review import Clause


class ContractSplitter:
    """Split contract text by headings and paragraphs."""

    heading_pattern = re.compile(
        r"^(第[一二三四五六七八九十百零\d]+条[\s：:、.\-]*.*|[0-9]+[.、]\s*.+)$",
        re.MULTILINE,
    )

    def split(self, text: str) -> list[Clause]:
        """Convert contract text into a sequence of clauses."""
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not normalized:
            return []

        matches = list(self.heading_pattern.finditer(normalized))
        if matches:
            return self._split_by_headings(normalized, matches)
        return self._split_by_paragraphs(normalized)

    def _split_by_headings(self, text: str, matches) -> list[Clause]:
        clauses: list[Clause] = []
        for index, match in enumerate(matches, start=1):
            start = match.start()
            end = matches[index].start() if index < len(matches) else len(text)
            chunk = text[start:end].strip()
            title_line = match.group(0).strip()
            clauses.append(
                Clause(
                    clause_id=f"clause_{index}",
                    title=title_line[:80],
                    text=chunk,
                    source_index=index,
                )
            )
        return clauses

    def _split_by_paragraphs(self, text: str) -> list[Clause]:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
        clauses: list[Clause] = []
        for index, paragraph in enumerate(paragraphs, start=1):
            title = self._derive_title(paragraph, index)
            clauses.append(
                Clause(
                    clause_id=f"clause_{index}",
                    title=title,
                    text=paragraph,
                    source_index=index,
                )
            )
        return clauses

    def _derive_title(self, clause_text: str, index: int) -> str:
        sentence = re.split(r"[。；\n]", clause_text, maxsplit=1)[0].strip()
        if not sentence:
            return f"Clause {index}"
        return sentence[:40]

