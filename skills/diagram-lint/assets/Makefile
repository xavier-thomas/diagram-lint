# Regenerates, checks and renders diagrams. Needs draw.io desktop and mermaid-cli.
# What every flag is for: references/ in this skill.
# Set SKILL to this skill's directory, relative to this file.

SKILL ?= ../.claude/skills/diagram-lint

MMD    := $(wildcard *.mmd)
DRAWIO ?= example.drawio

SVGS := $(MMD:.mmd=.svg) $(DRAWIO:.drawio=.svg)
PNGS := $(MMD:.mmd=.png) $(DRAWIO:.drawio=.png)

MERMAID_CFG ?= mermaid-config.json
MMDC_FLAGS := -b white -w 2600 -c $(MERMAID_CFG)
ifdef PUPPETEER_CFG
MMDC_FLAGS += -p $(PUPPETEER_CFG)
endif

DRAWIO_BIN ?= $(shell command -v drawio 2>/dev/null || \
                      echo /Applications/draw.io.app/Contents/MacOS/draw.io)
DRAWIO_FLAGS := --no-sandbox -x --theme light
DRAWIO_SVG_FLAGS := --embed-svg-fonts false
DRAWIO_PNG_SCALE := -s 2

.PHONY: all sources check clean

all: sources $(SVGS) $(PNGS)

# The library is an input: an edit to it regenerates every source.
sources: .drawio-sources
.drawio-sources: make_diagrams.py $(SKILL)/scripts/drawio_lib.py
	python3 make_diagrams.py
	@touch $@
# Without this, the first run cannot find a rule for the renders of a new .drawio file.
$(DRAWIO): .drawio-sources ;

# Exits non-zero while any edge is UNVERIFIED, so it gates nothing else.
check: sources
	python3 $(SKILL)/scripts/check_layout.py $(DRAWIO)

# The config is an input: a font change re-renders every Mermaid diagram.
%.svg: %.mmd $(MERMAID_CFG)
	mmdc $(MMDC_FLAGS) -i $< -o $@
%.png: %.mmd $(MERMAID_CFG)
	mmdc $(MMDC_FLAGS) -i $< -o $@
%.svg: %.drawio
	$(DRAWIO_BIN) $(DRAWIO_FLAGS) -f svg $(DRAWIO_SVG_FLAGS) -o $@ $<
%.png: %.drawio
	$(DRAWIO_BIN) $(DRAWIO_FLAGS) -f png $(DRAWIO_PNG_SCALE) -o $@ $<

clean:
	rm -f $(SVGS) $(PNGS) $(DRAWIO) .drawio-sources
