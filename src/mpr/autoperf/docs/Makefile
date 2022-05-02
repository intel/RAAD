SOPTS    ?=
SBUILD   ?= sphinx-build
SOURCEDIR = source
BUILDDIR  = build

help:
	@$(SBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SOPTS) $(O)

.PHONY: help Makefile

%: Makefile
	@$(SBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SOPTS) $(O)
