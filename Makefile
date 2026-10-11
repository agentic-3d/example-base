# Build, check and render every model. Run from the project root.
#   make            all models       make <name>      one model
#   make clean      remove out/      make sync-base   refresh CLAUDE.md and RULES.md from the base template
# out/ is committed: run make and commit its STL and PNG files together with the model change.

# Models bottom-up: a model comes after everything it imports.
MODELS := plate bracket assembly
# Expected body count where it is not 1.
BODIES_assembly := 2

# Base-owned files. Never edit them in a derived project, sync-base overwrites them.
BASE_REPO := agentic-3d/example-base
BASE_URL := https://raw.githubusercontent.com/$(BASE_REPO)/main
BASE_FILES := CLAUDE.md RULES.md

PY := uv run python

.PHONY: all clean sync-base $(MODELS)

all: $(MODELS)

$(MODELS):
	$(PY) tools/build.py $@
	$(PY) tools/check.py $@ --bodies $(or $(BODIES_$@),1)
	$(PY) tools/render.py $@

clean:
	rm -rf out

sync-base:
	@case "$$(git remote get-url origin 2>/dev/null)" in *$(BASE_REPO)*) echo "this is the base repo, nothing to sync"; exit 1;; esac
	@for f in $(BASE_FILES); do \
		curl -fsSL $(BASE_URL)/$$f -o $$f.tmp && mv $$f.tmp $$f && echo "synced $$f" || { rm -f $$f.tmp; echo "failed $$f"; exit 1; }; \
	done
	@git status --short $(BASE_FILES)
