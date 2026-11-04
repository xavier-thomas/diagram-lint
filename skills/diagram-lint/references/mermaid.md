# Mermaid

Sequences, logic flows and component diagrams are edited directly as `diagrams/*.mmd`.

## Limits

- **No cloud icons:** `architecture-beta` needs an Iconify pack registered at render
  time, and GitHub and mermaid.live register none. Use draw.io for anything with an
  AWS icon.
- **No pinned layout:** declaration order is the only control, and an edge can still
  route behind an unrelated box. `check_layout.py` reads only `.drawio` files, so the
  inspection in `SKILL.md` is the whole check.

If a diagram must be overlap-free, move it to draw.io and record that decision.

## Rendering

Install [mermaid-cli](https://github.com/mermaid-js/mermaid-cli), then render:

```bash
npm install -g @mermaid-js/mermaid-cli
```

```bash
make
```

`make` also renders draw.io diagrams. To render one Mermaid diagram alone:

```bash
make <name>.svg <name>.png
```

The `Makefile` passes these flags:

| Flag | Why |
|------|-----|
| `-b white` | Sets the background explicitly |
| `-w 2600` | Sets the page width. The default is 800 |
| `-p <file>` | Sets a puppeteer config, only when `PUPPETEER_CFG` is given |

If mermaid-cli cannot find Chrome, point it at one:

```bash
echo '{"executablePath":"/usr/bin/chromium"}' > pptr.json
```

```bash
make PUPPETEER_CFG=pptr.json
```
