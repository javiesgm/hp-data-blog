#!/usr/bin/env python3
"""
Give every fenced code block in _posts a language, so it gets colours, line numbers and
the right label ("SQL", "R", "Shell", ...). Blocks that already name a language are left alone.

Usage:  python3 scripts/label_code_blocks.py          (rewrites _posts/*.md in place)
        python3 scripts/label_code_blocks.py --dry-run

Guessing rules, first match wins:
  SQL keywords at the start (SELECT, WITH, INSTALL, LOAD, COPY, CREATE, ...)   -> sql
  starts with { or [ or "key":                                                 -> json
  shell commands (pip, conda, curl, wget, export, cd, $ ...)                   -> shell
  starts with a # comment in a post whose other blocks are mostly R or Python  -> that language
  anything else (program output, URLs, file paths, tables)                     -> text
"""
import re, sys, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
FENCE = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>```+|~~~+)(?P<info>[^\n`]*)$")

SQL = re.compile(r"^\s*(SELECT|WITH|INSTALL|LOAD|COPY|CREATE|INSERT|UPDATE|DELETE|DROP|ALTER)\b", re.I)
JSON = re.compile(r'^\s*(\{|\[|"[^"]+"\s*:)')
SHELL = re.compile(r"^\s*(\$ |pip |pip3 |conda |curl |wget |export |cd |mkdir |git |brew |apt(-get)? |sudo )")


def guess(body, post_langs):
    first = next((l for l in body.splitlines() if l.strip()), "")
    if SQL.match(first):
        return "sql"
    if JSON.match(first):
        return "json"
    if SHELL.match(first):
        return "shell"
    if first.lstrip().startswith("#") and post_langs:
        lang, _ = post_langs.most_common(1)[0]
        if lang in ("r", "python"):
            return lang
    return "text"


def label(text):
    lines = text.split("\n")
    # languages already used in this post
    post_langs = collections.Counter(
        m.group("info").strip().split()[0].lower()
        for l in lines if (m := FENCE.match(l)) and m.group("info").strip()
    )
    out, i, changed = [], 0, 0
    while i < len(lines):
        m = FENCE.match(lines[i])
        if not m:
            out.append(lines[i]); i += 1; continue
        fence = m.group("fence")
        j = i + 1
        while j < len(lines) and not lines[j].strip().startswith(fence[:3]):
            j += 1
        body = "\n".join(lines[i + 1:j])
        if m.group("info").strip():
            out.append(lines[i])
        else:
            out.append(f"{m.group('indent')}{fence}{guess(body, post_langs)}")
            changed += 1
        out.extend(lines[i + 1:j + 1])
        i = j + 1
    return "\n".join(out), changed


def main():
    dry = "--dry-run" in sys.argv
    total = 0
    for f in sorted((ROOT / "_posts").glob("20*.md")):
        text = f.read_text(encoding="utf-8")
        m = re.match(r"^---\n.*?\n---\n", text, re.S)
        head, body = (text[:m.end()], text[m.end():]) if m else ("", text)
        new_body, n = label(body)
        if n:
            total += n
            print(f"{n:3}  {f.name}")
            if not dry:
                f.write_text(head + new_body, encoding="utf-8")
    print(f"{total} code blocks labelled{' (dry run)' if dry else ''}")


if __name__ == "__main__":
    main()
