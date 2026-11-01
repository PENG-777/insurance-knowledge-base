import re
from pathlib import Path

from pypdf import PdfReader

CHAPTER_RE = re.compile(r"^第[一二三四五六七八九十百零〇0-9]+[章篇]")
ARTICLE_RE = re.compile(r"^第[一二三四五六七八九十百零〇0-9]+条")
CN_ITEM_RE = re.compile(r"^[一二三四五六七八九十]+[、.．]")
NUM_ITEM_RE = re.compile(r"^\d+(?:\.\d+)*[、.．]?\s*")


def parse_file(path: Path, filename: str) -> tuple[str, int]:
    """解析 pdf/txt/md，返回(全文, 页数)。"""
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        texts = []
        for page in reader.pages:
            texts.append((page.extract_text() or "").strip())
        return "\n".join(texts), len(reader.pages)
    if suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return text, max(1, text.count("\n") // 40 + 1)
    raise ValueError("仅支持 PDF、TXT、Markdown 文件")


def _heading(line: str) -> tuple[str, int, str] | None:
    """识别标题行，返回(章号, 层级, 标题)。"""
    if CHAPTER_RE.match(line):
        no = line.split()[0][:12]
        return no, 1, line[:120]
    if ARTICLE_RE.match(line):
        no = line.split()[0][:12]
        return no, 2, line[:120]
    if CN_ITEM_RE.match(line) and len(line) <= 40:
        return line[:2], 2, line[:120]
    if NUM_ITEM_RE.match(line) and len(line) <= 40 and not line.endswith("。"):
        no = NUM_ITEM_RE.match(line).group(0).strip()
        level = 3 if no.count(".") >= 2 else 2
        return no, level, line[:120]
    return None


def split_sections(text: str) -> list[dict]:
    """按章/条/编号标题切分；无标题时按段落聚合。"""
    lines = [ln.strip() for ln in (text or "").splitlines()]
    sections: list[dict] = []
    current: dict | None = None

    for line in lines:
        if not line:
            if current:
                current["content"] += "\n"
            continue
        head = _heading(line)
        if head:
            if current:
                sections.append(current)
            no, level, title = head
            current = {"chapter_no": no, "title": title, "level": level, "content": ""}
        elif current:
            current["content"] += line + "\n"
        else:
            current = {"chapter_no": "", "title": "前言", "level": 1, "content": line + "\n"}

    if current:
        sections.append(current)

    sections = [s for s in sections if s["content"].strip()]
    if not sections:
        paragraphs = [p.strip() for p in (text or "").split("\n") if p.strip()]
        buf, part = "", 1
        for p in paragraphs:
            if len(buf) + len(p) > 900:
                sections.append(
                    {"chapter_no": f"第{part}部分", "title": f"第{part}部分", "level": 1, "content": buf}
                )
                buf, part = "", part + 1
            buf += p + "\n"
        if buf:
            sections.append({"chapter_no": f"第{part}部分", "title": f"第{part}部分", "level": 1, "content": buf})
    return sections
