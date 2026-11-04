# Mermaid

Sequences, logic flows and component diagrams are edited directly as `diagrams/*.mmd`.

## Limits

- **No cloud icons:** `architecture-beta` needs an Iconify pack registered at render
  time, and GitHub and mermaid.live register none. Use draw.io for anything with an
  AWS icon.
- **No pinned layout:** declaration order is the only control, and an edge can still
  route behind an unrelated box. `check_layout.py` reads only `.drawio` files, so the
  inspection in `SKILL.md` is the only check of the layout.

If a diagram must be overlap-free, move it to draw.io and record that decision.

An edge often runs behind a box when one node fans out to several others that share a rank
with unrelated boxes. Give the fanning node a rank of its own, then render and inspect it.

## Colours

The starter `mermaid-config.json` uses `theme: base` with the C4 palette from
`drawio_lib.py`, so both toolchains match. Mermaid takes flowchart edge labels and `actor`
names from the same setting as node text, so white node text alone leaves them white on
white. The config's `themeCSS` sets them back to dark. Keep it if you change the palette.

## Box padding

If text is tight in its box, fix the font rather than the padding. Set `fontFamily`
in `mermaid-config.json` to a font that every machine rendering the diagrams has.

- Do not raise `wrapPadding`, which pushes message labels onto their arrows.
- Do not raise `noteMargin`, which leaves the text high in a taller note.
- Do not shorten the text to make one box fit.

A note over two participants takes its width from them, not from its text, so the font
cannot fix it. Start the text with `wrap:` to keep it inside the note:

```text
Note over W,D: wrap: The server checks its cache before it queries the database
```

## Self-messages

Never put text on a self-message. Mermaid centres the label on the lifeline, and
`autonumber` puts the step's number on the same line. Keep the step, with its number,
and put the text in a note:

```text
L->>L: #nbsp;
Note right of L: Parse the line and derive the interval start
```

`scripts/check_mermaid.py` fails on any self-message with visible text.

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
| `-c <file>` | Names the font and palette Mermaid uses |
| `-s 2` | Renders PNGs at twice the size, as draw.io does |
| `-p <file>` | Sets a puppeteer config, only when `PUPPETEER_CFG` is given |

If mermaid-cli cannot find Chrome, point it at one:

```bash
echo '{"executablePath":"/usr/bin/chromium"}' > pptr.json
```

```bash
make PUPPETEER_CFG=pptr.json
```
