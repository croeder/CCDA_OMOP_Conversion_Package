

# CCDA_OMOP_Conversion_Package:  ccda_to_omop

This is a project to convert CCDA documents to OMOP CDM format in Python.

[![ccda_to_omop Unit Tests](https://github.com/croeder/CCDA_OMOP_Conversion_Package/actions/workflows/unittests.yml/badge.svg)](https://github.com/croeder/CCDA_OMOP_Conversion_Package/actions/workflows/unittests.yml)

[![ccda_to_omop file comparisons](https://github.com/croeder/CCDA_OMOP_Conversion_Package/actions/workflows/file_comparisons.yml/badge.svg)](https://github.com/croeder/CCDA_OMOP_Conversion_Package/actions/workflows/file_comparisons.yml)
[![file comparisons](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/croeder/d0babd0799291fc23d3173de510eb1d8/raw/comparison-badge.json)](https://gist.github.com/croeder/d0babd0799291fc23d3173de510eb1d8)

[![Lint](https://github.com/croeder/CCDA_OMOP_Conversion_Package/actions/workflows/lint.yml/badge.svg)](https://github.com/croeder/CCDA_OMOP_Conversion_Package/actions/workflows/lint.yml)

[![codecov](https://codecov.io/gh/croeder/CCDA_OMOP_Conversion_Package/graph/badge.svg)](https://codecov.io/gh/croeder/CCDA_OMOP_Conversion_Package)

[Documentation](https://croeder.github.io/CCDA_OMOP_Conversion_Package/)

## What it does

Converts [C-CDA](https://www.hl7.org/ccdasearch/) (Consolidated Clinical Document Architecture) XML documents into [OMOP CDM](https://ohdsi.github.io/CommonDataModel/) tabular records. The conversion is driven by a metadata configuration layer so that new OMOP domains can be added without changing the core parsing engine.

## Concept map (map.csv)

The conversion requires a vocabulary cross-walk file `resources/map.csv` that maps
source codes (ICD-10, SNOMED, LOINC, etc., identified by OID) to OMOP concept IDs.
This file is not included in the repo because it is derived from licensed OMOP vocabulary data.

**For evaluation and testing**, a stub file `resources/map_stub.csv` is included.
It contains every `(OID, code)` pair that appears in the sample XML files in
`resources/`, but leaves `target_concept_id` and `source_concept_id` as `0` and
sets `target_domain` to `Observation` for all rows. This is enough to run the
conversion without errors, but concept ID lookups will return 0 and domain routing
will not be accurate — records may land in the wrong OMOP table.

To use the stub:
```bash
cp resources/map_stub.csv resources/map.csv
```

To use a full vocabulary map, populate `resources/map.csv` with the schema:
```
OID, code, codeSystem, target_id, target_domain, source_concept_id
```
where `OID` is the vocabulary OID, `target_id` is the OMOP `concept_id`, and
`target_domain` is the OMOP domain name (e.g. `Condition`, `Measurement`).

## Installation

```bash
git clone https://github.com/croeder/CCDA_OMOP_Conversion_Package.git
cd CCDA_OMOP_Conversion_Package
python -m venv env
source env/bin/activate
pip install -r requirements.txt
cp resources/map_stub.csv resources/map.csv   # or supply a full vocabulary map
```

## Basic usage

Convert a directory of CCDA XML files to CSV:

```bash
mkdir -p logs output
cd src
python -m ccda_to_omop.data_driven_parse -d ../resources -c
```

Output CSV files are written to `../output/` (one file per OMOP domain per input file).

Check results against the expected baseline:

```bash
bash bin/compare_correct.sh
# Expected: 205 missing / 0 errors
```

## Architecture overview

The conversion is table-driven. Each OMOP domain (Condition, Measurement, Visit, etc.) has a Python metadata file under `src/ccda_to_omop/metadata/` that describes:

- The XPath expression to find root elements in the CCDA XML
- Which fields to extract and how (field name, XPath, data type)
- Derived fields computed from other fields via transformation functions
- Vocabulary cross-walk lookups to map source codes to OMOP concept IDs

The core parsing engine (`data_driven_parse.py`) reads these metadata configs and applies them uniformly to any CCDA document. Vocabulary lookups are handled by `value_transformations.py` using a pre-loaded codemap dictionary.

Key modules:

| Module | Purpose |
|--------|---------|
| `data_driven_parse.py` | Main parsing engine; reads metadata configs and walks CCDA XML |
| `metadata/` | One Python file per OMOP domain/section mapping |
| `value_transformations.py` | Transformation functions (date casting, concept ID lookup, etc.) |
| `visit_reconciliation.py` | Links domain events to visit occurrences via FK reconciliation |
| `layer_datasets.py` | Foundry/Spark entry point; wraps parsing into DataFrames |
| `constants.py` | Business logic constants (concept ID sets, duration limits, etc.) |
| `util.py` | Utility functions (codemap dict builders, date parsing) |

## Adding a new OMOP domain mapping

1. Copy `src/ccda_to_omop/metadata/TEMPLATE.py` to a new file following the naming
   convention `DOMAIN-from-section_name.py` (e.g. `CONDITION-from-problems.py`).
   See `src/ccda_to_omop/metadata/condition.py` for the simplest real-world example.
2. Fill in the root XPath and field mappings. The template file is annotated with
   comments explaining each `config_type`. See also the
   [Field Types reference](https://croeder.github.io/CCDA_OMOP_Conversion_Package/field_types.html)
   in the generated docs.
3. Run the conversion and compare against expected output with `bash bin/compare_correct.sh`.

## Running the tests

Unit tests:

```bash
cd src
/path/to/env/bin/python -m pytest tests/
```

Or using the provided script (system Python must have dependencies):

```bash
bash bin/run_unittests.sh
```

Integration / regression test:

```bash
mkdir -p logs output
cd src
python -m ccda_to_omop.data_driven_parse -d ../resources -c
cd ..
bash bin/compare_correct.sh
```

## Dependency management

There are two dependency files with different purposes:

| File | Purpose |
|------|---------|
| `requirements.txt` | Pinned pip dependencies for local development and CI |
| `conda-versions.*.lock` | Conda lock files for the Gradle/Foundry build environment |

**Updating `requirements.txt`** — bump version pins manually and verify with
`bash bin/compare_correct.sh` (expected baseline: 205 missing / 0 errors).

**Conda lock files** — autogenerated by Gradle; do not edit by hand.
Regenerate with:

```bash
./gradlew --write-locks
```

Commit the updated lock files alongside any dependency changes.

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).

Third-party dependency licenses are documented in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
