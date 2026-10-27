# Contributing

Thanks for considering a contribution. This template stays small and dependency-free (Python stdlib only), so please keep changes aligned with that.

## Quick start

```bash
git clone https://github.com/jonyfs/llm-wiki-template.git
cd llm-wiki-template
python3 -m unittest discover -s tests -t .
python3 scripts/lint.py
python3 scripts/refresh.py
```

## Guidelines

- Run the test suite and lint before opening a PR; both must pass.
- Keep the always-loaded `AGENTS.md` under 8 KB; move detail into skills or `docs/`.
- Prefer updating existing pages/code over creating near-duplicates.
- Match the existing style: lowercase kebab-case slugs, YAML frontmatter, one logical line per paragraph.
- Do not add runtime dependencies; the zero-dependency rule is intentional.
- Do not write into `raw/` from tooling; it is a protected corpus.

## Reporting issues

Use the issue templates. For security issues, see `SECURITY.md`.

## License

By contributing, you agree your contributions are licensed under the MIT License.
