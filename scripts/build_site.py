#!/usr/bin/env python3
"""Build the static site and generate the blog from posts/*.md."""

from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import html
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

import markdown

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://tonyd365.github.io"
SITE_FILES = ("index.html", "404.html", ".nojekyll", "favicon.svg", "main.js", "styles.css")
SITE_DIRS = ("Projects", "Blog", "Contact", "assets")
POST_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
LIST_BLOCK = re.compile(r"<!-- blog:list -->.*?<!-- /blog:list -->", re.S)
MAIN_BLOCK = re.compile(r'<main id="main">.*?</main>', re.S)


@dataclass(frozen=True)
class Post:
    title: str
    description: str
    date: dt.date
    slug: str
    body: str

    @property
    def path(self) -> str:
        return f"/Blog/{self.slug}/"


def parse_post(path: Path) -> Post | None:
    match = POST_NAME.match(path.name)
    if not match:
        raise ValueError(f"{path.name}: name must look like 2026-11-24-my-post.md")
    date = dt.date.fromisoformat(match.group(1))

    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    parts = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not parts:
        raise ValueError(f"{path.name}: must start with a --- front matter block")

    meta: dict[str, str] = {}
    for line in parts.group(1).splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"{path.name}: bad front matter line: {line!r}")
        meta[key.strip().lower()] = value.strip().strip("\"'")

    unknown = set(meta) - {"title", "description", "draft"}
    if unknown:
        raise ValueError(f"{path.name}: unknown front matter: {', '.join(sorted(unknown))}")
    if not meta.get("title") or not meta.get("description"):
        raise ValueError(f"{path.name}: title and description are required")
    if meta.get("draft", "false").lower() not in {"true", "false"}:
        raise ValueError(f"{path.name}: draft must be true or false")
    if meta.get("draft", "false").lower() == "true":
        return None
    if not parts.group(2).strip():
        raise ValueError(f"{path.name}: post body is empty")

    body = markdown.markdown(parts.group(2), extensions=["fenced_code", "tables"])
    return Post(meta["title"], meta["description"], date, match.group(2), body)


def load_posts(directory: Path) -> list[Post]:
    posts = []
    for path in sorted(directory.glob("*.md")):
        if path.name == "README.md":
            continue
        post = parse_post(path)
        if post:
            posts.append(post)
    slugs = [post.slug for post in posts]
    duplicates = sorted({slug for slug in slugs if slugs.count(slug) > 1})
    if duplicates:
        raise ValueError(f"duplicate post slugs: {', '.join(duplicates)}")
    return sorted(posts, key=lambda post: (post.date, post.slug), reverse=True)


def render_list(posts: list[Post]) -> str:
    if not posts:
        return '<p class="note">No posts yet. The first one is on the way.</p>'
    items = "\n".join(
        f'<li><time datetime="{post.date}">{post.date}</time>'
        f'<div><a href="{post.path}">{html.escape(post.title)}</a>'
        f"<p>{html.escape(post.description)}</p></div></li>"
        for post in posts
    )
    return f'<ol class="post-list">\n{items}\n</ol>\n<p class="more"><a href="/Blog/feed.xml">RSS feed</a></p>'


def render_post(template: str, post: Post) -> str:
    title = html.escape(post.title)
    description = html.escape(post.description)
    main = (
        '<main id="main"><article class="post">'
        '<p class="crumb"><a href="/Blog/">← all posts</a></p>'
        f'<p class="cmd">cat {post.slug}.md</p><h1 class="page-title">{title}</h1>'
        f'<p class="tag"><time datetime="{post.date}">{post.date}</time></p>'
        f"{post.body}</article></main>"
    )
    page = MAIN_BLOCK.sub(lambda _: main, template, count=1)
    page = re.sub(r"<title>.*?</title>", lambda _: f"<title>{title} · Tony Dong</title>", page, count=1)
    page = re.sub(
        r'<meta name="description" content=".*?">',
        lambda _: f'<meta name="description" content="{description}">',
        page,
        count=1,
    )
    page = page.replace('href="https://tonyd365.github.io/Blog/"', f'href="{SITE_URL}{post.path}"', 1)
    page = page.replace("tony@github.io:~/Blog", f"tony@github.io:~/Blog/{post.slug}", 1)
    return page.replace(' aria-current="page"', "", 1)


def render_feed(posts: list[Post]) -> str:
    items = []
    for post in posts:
        url = f"{SITE_URL}{post.path}"
        when = dt.datetime.combine(post.date, dt.time(), dt.timezone.utc)
        items.append(
            f"<item><title>{escape(post.title)}</title><link>{url}</link>"
            f'<guid isPermaLink="true">{url}</guid>'
            f"<pubDate>{email.utils.format_datetime(when)}</pubDate>"
            f"<description>{escape(post.description)}</description></item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
        f"<title>Tony Dong's Blog</title><link>{SITE_URL}/Blog/</link>"
        "<description>Notes on what I'm building and learning.</description>"
        f"{''.join(items)}</channel></rss>\n"
    )


def build(posts_dir: Path, out: Path) -> int:
    posts = load_posts(posts_dir)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for name in SITE_FILES:
        shutil.copy2(ROOT / name, out / name)
    for name in SITE_DIRS:
        shutil.copytree(ROOT / name, out / name)

    blog_index = out / "Blog" / "index.html"
    template = blog_index.read_text(encoding="utf-8")
    if not LIST_BLOCK.search(template):
        raise ValueError("Blog/index.html is missing the blog:list markers")
    feed_link = '<link rel="alternate" type="application/rss+xml" title="Tony Dong\'s Blog" href="/Blog/feed.xml">'
    template = template.replace("</head>", f"  {feed_link}\n</head>", 1)
    blog_index.write_text(LIST_BLOCK.sub(lambda _: render_list(posts), template), encoding="utf-8")

    for post in posts:
        target = out / "Blog" / post.slug / "index.html"
        target.parent.mkdir()
        target.write_text(render_post(template, post), encoding="utf-8")
    (out / "Blog" / "feed.xml").write_text(render_feed(posts), encoding="utf-8")
    return len(posts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--posts", type=Path, default=ROOT / "posts")
    parser.add_argument("--out", type=Path, default=ROOT / "_site")
    args = parser.parse_args()
    try:
        count = build(args.posts, args.out)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Built {args.out} with {count} post(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
