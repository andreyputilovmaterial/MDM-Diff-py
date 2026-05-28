.PHONY: build

hello:
	echo "Hello"

at_hello:
	@echo "Hello"

make:
	DIST_DIR := dist
	VERSION_FILE := src/GENERATED/_VERSION.py
	BUNDLE := $(DIST_DIR)/mdmtoolsap_bundle.py
	PINLINER := src_dev_build/lib/pinliner/pinliner/pinliner.py

	RUN_SCRIPT_PAIRS := \
	run_calling_bundle_mdd.bat:run_diff_mdd.bat \
	run_calling_bundle_aligned_diffs_mdd.bat:run_diff_aligned_workflows_mdds.bat \
	run_calling_bundle_mdd_report.bat:run_mdd_report.bat \
	run_calling_bundle_mdd_report_in_excel.bat:run_mdd_report_in_excel.bat \
	run_calling_bundle_textfile.bat:run_diff_textfile.bat \
	run_calling_bundle_msmarkitdown.bat:run_diff_msmarkitdown.bat \
	run_calling_bundle_excel.bat:run_diff_excel.bat \
	run_calling_bundle_excel_wholedirectory.bat:run_diff_excel_wholedirectory.bat \
	run_calling_bundle_spss.bat:run_diff_spss.bat


	all: clean version mdmread template bundle patch copy_scripts copy_test
	@echo
	@echo "All done"

	clean:
	@echo "Cleaning dist/"
	@mkdir -p $(DIST_DIR)
	@rm -f $(DIST_DIR)/*

	version:
	@echo
	@echo "Updating version"

	@mkdir -p src/GENERATED

	@echo "'''For auto-generated files'''" > src/GENERATED/__init__.py

	@echo "# THIS IS AUTO-GENERATED" > $(VERSION_FILE)

	@python -c "from datetime import datetime; print(f'# {datetime.now()}')" >> $(VERSION_FILE)

	@echo "_VERSION = '''" >> $(VERSION_FILE)

	@git describe --tags --dirty >> $(VERSION_FILE)

	@echo "'''" >> $(VERSION_FILE)

	mdmread:
	@echo
	@echo "Building mdmread"

	@cd src/lib/mdmreadpy && ./build.bat

	template:
	@echo
	@echo "Building template"

	@cd src/lib/mdmreadpy/src/lib/mdmreportpy && \
	./build.bat && \
	python build_compiled_template.py

	bundle:
	@echo
	@echo "Building bundle"

	@python $(PINLINER) src -o $(BUNDLE)

	patch:
	@echo
	@echo "Patching bundle"

	@echo "" >> $(BUNDLE)
	@echo "from src import launcher" >> $(BUNDLE)
	@echo "launcher.main()" >> $(BUNDLE)

	copy_scripts:
	@echo
	@echo "Copying and patching BAT scripts"

	@mkdir -p $(DIST_DIR)

	@for pair in $(RUN_SCRIPT_PAIRS); do \
	src=$${pair%%:*}; \
	dst=$${pair##*:}; \
	cp "src_bat_scripts/$$src" "$(DIST_DIR)/$$dst"; \
	sed -i.bak \
	-e 's#\(\.\./\)\?dist[\\/]\?mdmtoolsap_bundle\.py#mdmtoolsap_bundle.py#g' \
	"$(DIST_DIR)/$$dst"; \
	rm -f "$(DIST_DIR)/$$dst.bak"; \
	done

	@for pair1 in $(RUN_SCRIPT_PAIRS); do \
	src1=$${pair1%%:*}; \
	dst1=$${pair1##*:}; \
	for pair2 in $(RUN_SCRIPT_PAIRS); do \
	src2=$${pair2%%:*}; \
	dst2=$${pair2##*:}; \
	sed -i.bak \
	-e "s#$$src2#$$dst2#g" \
	"$(DIST_DIR)/$$dst1"; \
	rm -f "$(DIST_DIR)/$$dst1.bak"; \
	done; \
	done

	copy_test:
	@echo
	@echo "Copying bundle to tests folder"

	@cp $(BUNDLE) tests-real-sensitive-data/current/ \
	|| echo "Not updated"
