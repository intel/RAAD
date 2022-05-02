# !/usr/bin/make
COMMIT_ID = $(shell git rev-parse --short=8 HEAD)
COMMIT_DATE = $(shell git show -s --format=%cd --date=short HEAD)
VERSION = $(COMMIT_DATE) $(COMMIT_ID)
TARNAME=RAAD
TARDIR=spaceballs
ZFILE=FILE
.DEFAULT_GOAL := help

info:
	@echo "----------------------------------------------------"
	@echo "RAAD $(VERSION)"
	@echo "----------------------------------------------------"
.PHONY: info

clean:
	@rm -f $(TARNAME)
	$(shell ./scripts/clean.sh)
.PHONY: clean

createExe:
	$(shell ./scripts/createExe.sh)
.PHONY: createExe

installer:
	$(shell ./scripts/installer.sh)
.PHONY: installer

vgen:
	@echo "RAAD $(VERSION)" > version.txt
.PHONY: vgen

bremove: vgen
	@mkdir -p $(TARDIR)
	echo '$(TARDIR)' > $(ZFILE)
	echo '$(TARDIR)/$(TARNAME).tar' >> $(ZFILE)
	echo '$(TARDIR)/$(TARNAME).tar.gz' >> $(ZFILE)
	echo '$(TARDIR)/$(TARNAME).tar.bz2' >> $(ZFILE)
	echo '$(TARDIR)/$(TARNAME)_tar' >> $(ZFILE)
	echo '$(TARDIR)/$(TARNAME)_tar_gz' >> $(ZFILE)
	echo '$(TARDIR)/$(TARNAME)_tar_bz2' >> $(ZFILE)
.PHONY: bremove

tarball_all: tarball tarballbz tarballgz
	echo "Tar'ing all"
.PHONY: tarball_all

tarball: bremove
	@echo "tar'ing $(TARDIR)/$(TARNAME).tar to $(TARDIR)/$(TARNAME).tar"
	@rm -f $(TARDIR)/$(TARNAME).tar
	@tar -cvf $(TARDIR)/$(TARNAME).tar --exclude $(ZFILE) *
.PHONY: tarball

dtarball: bremove
	@echo "un-tar'ing $(TARDIR)/$(TARNAME).tar to $(TARDIR)/$(TARNAME)_tar"
	@rm -rf $(TARDIR)/$(TARNAME)_tar
	@tar -xvf $(TARDIR)/$(TARNAME).tar $(TARDIR)/$(TARNAME)_tar
.PHONY: dtarball

tarballgz: bremove
	@echo "tar'ing gzipped $(TARNAME).tar.gz to $(TARDIR)/$(TARNAME).tar.gz"
	@rm -f $(TARDIR)/$(TARNAME).tar.gz
	@tar -cvzf $(TARNAME).tar.gz --exclude $(ZFILE) *
.PHONY: tarballgz

dtarballgz: bremove
	@echo "un-tar'ing gzipped $(TARDIR)/$(TARNAME).tar.gz to $(TARDIR)/$(TARNAME)_tar_gz"
	@rm -rf $(TARDIR)/$(TARNAME)_tar_gz
	@tar -xvfz $(TARNAME).tar.gz $(TARDIR)/$(TARNAME)_tar_gz
.PHONY: dtarballgz

tarballbz: bremove
	@echo "tar'ing bzipped to $(TARDIR)/$(TARNAME).tar.bz2"
	@rm -f $(TARDIR)/$(TARNAME).tar.bz2
	@tar -cvjf $(TARDIR)/$(TARNAME).tar.bz2 --exclude $(ZFILE) *
.PHONY: tarballbz

dtarballbz: bremove
	@echo "un-tar'ing bzipped $(TARDIR)/$(TARNAME).tar.bz2 to $(TARDIR)/$(TARNAME)_tar_bz2"
	@rm -rf $(TARDIR)/$(TARNAME)_tar_bz2
	@tar -xvfj $(TARNAME).tar.bz2 $(TARDIR)/$(TARNAME)_tar_bz2
.PHONY: dtarballbz

help: info
	@echo "----------------------------------------------------"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| sed -n 's/^\(.*\): \(.*\)##\(.*\)/\1\3/p' \
	| column -t  -s ' '
	@echo ""
	$(info Please note to start with README.md then folder dox.)
	@echo "----------------------------------------------------"
	@echo "Usage: make help"
	@echo "----------------------------------------------------"
	@cat README.md
	@echo ""
	@echo "----------------------------------------------------"
.PHONY: help
