# Renders for the examples, using the skill's starter Makefile.
SKILL := ../../skills/diagram-lint
DRAWIO := aws-web-app.drawio c4-container.drawio kubernetes-platform.drawio \
          azure-telemetry.drawio lint-after.drawio
MERMAID_CFG := $(SKILL)/assets/mermaid-config.json

include $(SKILL)/assets/Makefile

# lint-before.drawio fails the layout check on purpose, so it stays out of DRAWIO.
lint-before.drawio: .drawio-sources ;
all: lint-before.png
.PHONY: clean-lint-before
clean: clean-lint-before
clean-lint-before:
	rm -f lint-before.drawio lint-before.png
