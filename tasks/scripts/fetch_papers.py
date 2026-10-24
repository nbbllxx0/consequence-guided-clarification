"""Download arXiv full text for screening and convert it to plain text.

For each id: try https://arxiv.org/html/<id>; if no HTML rendering exists,
fetch the abs page and https://arxiv.org/pdf/<id> and convert the PDF with
pdftotext. Writes into OUTDIR/<id_safe>/:
  source.html | abs.html + paper.pdf, text.txt, meta.json
text.txt marks section headings with '## ' and figure captions with
'[FIGURE <n>] <caption> {img: <url>}' so figure-only details can be traced.

Usage: python fetch_papers.py OUTDIR ID [ID ...]
       python fetch_papers.py OUTDIR --fig URL DEST   (download one figure)
Requests are sequential with a 3 s pause before each arXiv request.
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from lxml import html as LH

UA = "python-urllib/3 (literature-screen script)"
PAUSE_S = 3.0
_last = [0.0]


LOCK = Path(__file__).resolve().parent / ".arxiv_request.lock"
STAMP = Path(__file__).resolve().parent / ".arxiv_last_request"


def _acquire_lock():
    """Cross-process lock so that concurrent screeners still send arXiv requests one at a time."""
    while True:
        try:
            fd = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return
        except FileExistsError:
            try:
                if time.time() - LOCK.stat().st_mtime > 300:
                    LOCK.unlink()  # stale lock from a killed process
            except FileNotFoundError:
                pass
            time.sleep(0.5)


def _open_serialized(req):
    _acquire_lock()
    try:
        last = float(STAMP.read_text()) if STAMP.exists() else 0.0
        wait = PAUSE_S - (time.time() - max(last, _last[0]))
        if wait > 0:
            time.sleep(wait)
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.geturl(), r.status, r.read()
        finally:
            _last[0] = time.time()
            STAMP.write_text(str(_last[0]))
    finally:
        LOCK.unlink(missing_ok=True)


def get(url: str, retries: int = 5):
    """Return (final_url, status, bytes). 404 returns status without raising."""
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            return _open_serialized(req)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return url, 404, b""
            if e.code in (429, 503):
                time.sleep(PAUSE_S * 10 * (attempt + 1))
                continue
            return url, e.code, b""
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"  {url}: {e}; retrying", file=sys.stderr)
            time.sleep(PAUSE_S * 5 * (attempt + 1))
    return url, -1, b""


def html_to_text(raw: bytes, base_url: str) -> tuple[str, list]:
    doc = LH.fromstring(raw)
    for bad in doc.xpath("//script|//style|//nav|//header|//footer"):
        bad.drop_tree()
    for m in doc.xpath("//math"):
        alt = m.get("alttext") or ""
        tail = m.tail
        span = LH.Element("span")
        span.text = f" ${alt}$ " if alt else " "
        span.tail = tail
        m.getparent().replace(m, span)
    figs = []
    lines = []
    base = base_url

    def emit_fig(fig):
        cap = fig.xpath(".//figcaption")
        cap_txt = " ".join(" ".join(c.text_content().split()) for c in cap)
        imgs = [urllib.request.urljoin(base, i.get("src")) for i in fig.xpath(".//img") if i.get("src")]
        imgs += [urllib.request.urljoin(base, o.get("data")) for o in fig.xpath(".//object") if o.get("data")]
        figs.append({"caption": cap_txt, "imgs": imgs, "id": fig.get("id")})
        lines.append(f"[FIGURE {fig.get('id')}] {cap_txt} {{img: {' | '.join(imgs)}}}")

    body = doc.xpath("//article") or [doc]
    for el in body[0].iter():
        if not isinstance(el.tag, str):
            continue
        cls = el.get("class") or ""
        if el.tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            lines.append("\n## " + " ".join(el.text_content().split()))
        elif el.tag == "figure" and "ltx_table" not in cls:
            if not any(a.tag == "figure" for a in el.iterancestors()):
                emit_fig(el)
        elif el.tag == "figure" and "ltx_table" in cls:
            lines.append("[TABLE] " + " ".join(el.text_content().split()))
        elif "ltx_listing" in cls.split() and not any("ltx_listing" in (a.get("class") or "").split() for a in el.iterancestors()):
            # code listings (e.g. MATLAB boundary-condition lines); one line per listing line
            rows = [" ".join(r.text_content().split()) for r in el.xpath(".//*[contains(@class,'ltx_listingline')]")]
            body_txt = " | ".join(r for r in rows if r) or " ".join(el.text_content().split())
            lines.append("[LISTING] " + body_txt)
        elif el.tag == "table" and ("ltx_equation" in cls or "ltx_equationgroup" in cls):
            if not any(a.tag == "table" or a.tag == "figure" for a in el.iterancestors()):
                lines.append("[EQ] " + " ".join(el.text_content().split()))
        elif el.tag == "p" or (el.tag == "div" and "ltx_para" in cls and not el.xpath(".//p")):
            if any(a.tag == "figure" for a in el.iterancestors()):
                continue
            t = " ".join(el.text_content().split())
            if t:
                lines.append(t)
    return "\n".join(lines), figs


def fetch_one(outdir: Path, aid: str):
    d = outdir / aid.replace("/", "_")
    d.mkdir(parents=True, exist_ok=True)
    meta = {"id": aid}
    url, st, raw = get(f"https://arxiv.org/html/{aid}")
    meta["html_url"], meta["html_status"] = url, st
    is_html = st == 200 and b"ltx_document" in raw
    if is_html:
        (d / "source.html").write_bytes(raw)
        text, figs = html_to_text(raw, url)
        meta["source"] = "arxiv_html"
        meta["n_figures"] = len(figs)
        (d / "figures.json").write_text(json.dumps(figs, indent=1, ensure_ascii=False), encoding="utf-8")
    else:
        aurl, ast, araw = get(f"https://arxiv.org/abs/{aid}")
        meta["abs_status"] = ast
        if ast == 200:
            (d / "abs.html").write_bytes(araw)
        purl, pst, praw = get(f"https://arxiv.org/pdf/{aid}")
        meta["pdf_url"], meta["pdf_status"] = purl, pst
        text = ""
        if pst == 200 and praw[:4] == b"%PDF":
            (d / "paper.pdf").write_bytes(praw)
            subprocess.run(["pdftotext", str(d / "paper.pdf"), str(d / "text.txt")], check=False)
            text = (d / "text.txt").read_text(encoding="utf-8", errors="replace") if (d / "text.txt").exists() else ""
            meta["source"] = "arxiv_pdf"
        else:
            meta["source"] = "inaccessible"
    (d / "text.txt").write_text(text, encoding="utf-8")
    meta["text_chars"] = len(text)
    (d / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"{aid}: {meta['source']} ({len(text)} chars)", file=sys.stderr)


def main():
    outdir = Path(sys.argv[1])
    if sys.argv[2] == "--reconvert":
        # Re-run HTML-to-text on already downloaded source.html files (no network).
        for d in sorted(outdir.iterdir()):
            src, metaf = d / "source.html", d / "meta.json"
            if src.exists() and metaf.exists():
                meta = json.loads(metaf.read_text(encoding="utf-8"))
                text, figs = html_to_text(src.read_bytes(), meta["html_url"])
                (d / "text.txt").write_text(text, encoding="utf-8")
                (d / "figures.json").write_text(json.dumps(figs, indent=1, ensure_ascii=False), encoding="utf-8")
                meta["text_chars"], meta["n_figures"] = len(text), len(figs)
                metaf.write_text(json.dumps(meta, indent=1), encoding="utf-8")
        return
    if sys.argv[2] == "--fig":
        url, dest = sys.argv[3], Path(sys.argv[4])
        _, st, raw = get(url)
        if st != 200:
            sys.exit(f"figure fetch failed: {st}")
        dest.write_bytes(raw)
        print(f"saved {dest} ({len(raw)} bytes)")
        return
    for aid in sys.argv[2:]:
        if (outdir / aid.replace("/", "_") / "meta.json").exists():
            continue
        fetch_one(outdir, aid)


if __name__ == "__main__":
    main()
