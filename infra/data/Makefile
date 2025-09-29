PYTHON ?= python3
DBT_PROJECT_DIR := $(CURDIR)/dbt
DBT_PROFILES_DIR := $(CURDIR)/dbt

.PHONY: ci dbt-build airflow-compile clean

ci: airflow-compile dbt-build

airflow-compile:
	$(PYTHON) -m compileall airflow/dags
	dbt deps --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR)
	dbt seed --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR) --target ci --full-refresh
	dbt build --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR) --target ci --full-refresh

# Included for local developers wanting to iterate on models without re-running compile.
dbt-build:
	dbt build --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR) --target ci --full-refresh

clean:
	rm -rf dbt/target dbt/dbt_packages
	rm -f dbt/profiles.ymlc
