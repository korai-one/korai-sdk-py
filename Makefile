# Korai Python SDK — codegen + dev tasks.
#
# `make gen` regenerates the typed transport core in src/korai/_generated
# from the canonical spec (../../specs/openapi.yaml) using
# openapi-python-client, installed into a local .venv (gitignored). The
# hand-written ergonomic layer in src/korai/{auth,llm,...} imports from
# _generated and is never touched by codegen.

VENV := .venv
PY := $(VENV)/Scripts/python    # On macOS/Linux use $(VENV)/bin/python
GEN := src/korai/_generated
# Public SDK reads the DERIVED public spec (built by openapi-format ahead of
# codegen — see scripts/codegen.sh) — every `x-internal: true` operation stripped.
SPEC := ../../specs/openapi.public.yaml
# Pin ruff so the committed _generated formatting is reproducible across machines.
# Bump deliberately (regenerate + commit the resulting diff), never implicitly.
RUFF_VERSION := 0.15.18

.PHONY: gen venv clean-gen

venv:
	python -m venv $(VENV)
	$(PY) -m pip install --quiet --upgrade pip openapi-python-client "ruff==$(RUFF_VERSION)"

gen: venv
	rm -rf $(GEN)
	$(VENV)/Scripts/openapi-python-client generate \
		--path $(SPEC) \
		--meta none \
		--output-path $(GEN) \
		--config openapi-python-client.yaml \
		--overwrite
	# Deterministic formatting with the pinned ruff (the generator's own hooks
	# are disabled in openapi-python-client.yaml). Same args the generator uses
	# for --meta none: import-sort + safe fixes, then format.
	$(PY) -m ruff check $(GEN) --fix-only --extend-select=I --quiet
	$(PY) -m ruff format $(GEN) --quiet

clean-gen:
	rm -rf src/korai/_generated
