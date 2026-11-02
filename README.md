[![GBIF Hosted Portal](https://docs.gbif.org/style/gbif-hosted-portal.svg)](https://github.com/gbif/hosted-portals)

# GBIF Data Blog – hosted portal version (test)

A test of running the [GBIF Data Blog](https://data-blog.gbif.org) as a GBIF hosted portal, using the
[hosted-portal Jekyll theme](https://github.com/gbif/jekyll-hp-base-theme). All posts were migrated from
[gbif/data-blog](https://github.com/gbif/data-blog) (Hugo) with `scripts/migrate_from_hugo.py`, keeping their
addresses (`/post/<slug>/`) and the RSS feed (`/index.xml`).

**Preview:** built automatically to GitHub Pages on every push (see `.github/workflows/preview.yml`).
The preview is marked as a test site, has no comments and is hidden from search engines.

## How readers find posts

- **Home** (`/`, also `/post/`): every post as cards or as a compact list (switch at the top right,
  remembered per browser), a search box and the topic chips.
- **Filtered lists** use the same page: `/?category=Taxonomy`, `/?author=john-waller`, `/?tag=rgbif`,
  `/?series=good-samaritans`. Author names and tags on a post link there.
- **Series** (`/series/`) and **Authors** (`/authors/`) are built automatically from the posts' front matter.
- Old Hugo addresses such as `/author/john-waller/` or `/tags/rgbif/` redirect to the matching filtered list.

No Jekyll plugins are involved, so the site builds with the standard hosted-portal Gemfile.

## Writing a post

1. Create `_posts/YYYY-MM-DD-your-post.md`.
2. Put images and data files in `post/YYYY-MM-DD-your-post/` and link them as
   `![Alt text](/post/YYYY-MM-DD-your-post/plot1.png)`.
3. Start the file with this header:

```yaml
---
title: Your title
author: Your Name                 # or a list: [Marie Grosjean, Kate Ingenloff]
date: 2026-11-02
categories: [APIs and downloads]  # one or two topics from the list below
tags: [rgbif, occurrence]         # optional, free keywords used by search
thumbnail: /post/YYYY-MM-DD-your-post/plot1.png  # optional picture for the post list
---
```

The address of the post will be `/post/your-post/` (the file name without the date).

**Authors** are picked up automatically: a new name appears on the Authors page and gets its own
filtered list the next time the site is built. Write your name exactly as on your earlier posts
(“John Waller”, not “J. Waller”), or you will show up as two people. With co-authors, use a list
(`author: [Marie Grosjean, Kate Ingenloff]`), not “Marie Grosjean and Kate Ingenloff”.
To choose a different one, add `slug: something-else`.

**Topics** (`categories`): APIs and downloads · Publishing data · Analysis and maps · Taxonomy ·
Data quality · Citation and data use · Collections · Citizen science · Molecular data.
New topics appear automatically, but please reuse these where possible.

### Optional settings

| Setting | What it does |
| --- | --- |
| `description: One sentence` | Subtitle under the title, and the text used by search engines |
| `toc: true` | Adds a table of contents next to the post (good for long tutorials) |
| `series: Good SAMaritans` | Links all posts of a series together at the end of each post |
| `excerpt_separator: <!--more-->` | Ends the summary on the post list at `<!--more-->` instead of after the first paragraph |
| `mathjax: true` | Renders LaTeX maths (`$...$`, `$$...$$`) |
| `published: false` | Draft: the post is not built |
| `excludeFromArchive: true` | The post is built but not listed |

### Things that differ from the Hugo blog

- No need to paste the long Hugo header. Only `title`, `author`, `date` and `categories` matter.
- Code that contains `{{` or `{%` (R glue strings, templates): add `render_with_liquid: false` to the header.
- Leave a blank line before a table.
- Markdown inside `<details>` needs `<details markdown="1">`.

## Running locally

Requires Ruby and Bundler (same setup as other GBIF hosted portals):

```bash
bundle install
bundle exec jekyll serve
```

Then open http://localhost:4000. See also the
[hosted portals getting-started guide](https://github.com/gbif/hosted-portals/tree/main/getting-started).
