from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]


class LocalReferences(HTMLParser):
    def __init__(self, page: Path):
        super().__init__(convert_charrefs=True)
        self.page = page
        self.references: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for attr in ("href", "src"):
            value = values.get(attr)
            if value:
                self.references.append((attr, value))
        srcset = values.get("srcset")
        if srcset:
            for candidate in srcset.split(","):
                value = candidate.strip().split(maxsplit=1)[0]
                if value:
                    self.references.append(("srcset", value))


errors: list[str] = []
pages = list(ROOT.rglob("*.html"))
if not pages:
    raise SystemExit("No HTML pages found")

for page in pages:
    if any(part in {".git", "node_modules", "dist"} for part in page.parts):
        continue
    parser = LocalReferences(page)
    parser.feed(page.read_text(encoding="utf-8"))
    for attr, value in parser.references:
        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        raw_path = unquote(parsed.path)
        target = ROOT / raw_path.lstrip("/") if raw_path.startswith("/") else page.parent / raw_path
        if raw_path.endswith("/"):
            target /= "index.html"
        if not target.exists():
            errors.append(f"{page.relative_to(ROOT)}: missing {attr} target {value}")

if errors:
    print("\\n".join(errors))
    raise SystemExit(1)
print(f"Checked local references in {len(pages)} HTML page(s)")
