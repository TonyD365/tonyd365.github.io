# Writing a post

Add a file here named `YYYY-MM-DD-your-post-title.md`, using lowercase letters, numbers and hyphens:

```markdown
---
title: Why I built YTKTV
description: One sentence shown in the Blog list and RSS feed.
---

Write the post in Markdown.
```

Add `draft: true` to the top block to keep a post unpublished. Its URL will be `/Blog/your-post-title/`.

Preview locally:

```bash
python3 -m pip install -r requirements-blog.txt
python3 scripts/build_site.py
python3 -m http.server 4173 --directory _site
```
