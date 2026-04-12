Overview
========

``ccda_to_omop`` converts HL7 C-CDA (Consolidated Clinical Document
Architecture) XML documents into OMOP CDM tabular records.

Architecture
------------

The conversion is driven by a metadata configuration layer. Each OMOP domain
(e.g. ``condition_occurrence``, ``drug_exposure``, ``observation``) has a
corresponding metadata file that describes which C-CDA XPaths map to which
OMOP columns. Adding a new domain requires only a new metadata config — no
changes to the core parsing engine.

Key modules
-----------

- **data_driven_parse** — XPath-based C-CDA XML parser driven by metadata configs
- **layer_datasets** — orchestrates per-file, per-config parsing into pandas DataFrames
- **value_transformations** — concept code mapping and value normalization
- **visit_reconciliation** — links clinical events to visit_occurrence records
- **ddl** — OMOP table definitions and domain→table name mappings
- **domain_dataframe_column_types** — pandas dtype specifications per OMOP table
- **util** — shared helpers (codemap loading, etc.)

Installation
------------

.. code-block:: bash

    git clone https://github.com/croeder/CCDA_OMOP_Conversion_Package.git
    cd CCDA_OMOP_Conversion_Package
    python -m venv env
    source env/bin/activate
    pip install -r requirements.txt

Usage
-----

.. code-block:: bash

    bin/process.sh
