Architecture
============

*A Declarative, Content-Driven Architecture for CCDA to OMOP Transformation:
Design Rationale and Advantages over Traditional ETL Pipelines*

Abstract
--------

Clinical Document Architecture (CCDA) files are widely used for electronic
health record exchange, yet their hierarchical and variable structure presents
challenges for transformation into relational formats such as the Observational
Medical Outcomes Partnership (OMOP) Common Data Model. Traditional ETL pipelines
rely on sequential SQL transformations and table staging, which often obscure
provenance and complicate iteration over heterogeneous data. We describe a
lightweight, Python-based, rule-driven engine that leverages parse
configurations, content-driven extraction, fallback logic, transformation rules,
and content-based hashing to emit OMOP rows. This architecture simplifies
maintenance, accelerates iteration, and improves robustness while preserving
hierarchical context, in contrast to conventional pipelines.

1. Introduction
---------------

Mapping CCDA documents to OMOP tables requires handling nested structures,
optional elements, multiple template variations, and vendor-specific quirks.
Traditional pipeline approaches, dominated by SQL and batch transformations, are
familiar to data analysts but often introduce complexity, flatten hierarchical
data prematurely, and slow iterative development. In contrast, software
engineering principles suggest separating engine logic from data-driven mapping
specifications to create maintainable, flexible systems.

This paper presents a declarative, lightweight engine for CCDA parsing,
highlights its design rationale, and contrasts it with conventional ETL pipeline
approaches.

2. System Architecture
----------------------

The architecture is composed of three core layers.

2.1 Mapping Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~

Each OMOP domain (e.g., ``condition_occurrence``, ``drug_exposure``) has one or
more parse configurations. Each parse configuration defines:

- CCDA sections to parse
- Locales or structural variants within sections
- XPath extraction rules for each locale
- Fallback options (coalescing) for optional or inconsistent elements
- Transformation rules, such as date normalization or terminology mapping

This declarative specification captures the mapping logic in a compact, readable,
and maintainable format. Driving the conversion from configurations rather than
procedural code makes the structural mappings — which CCDA element goes to which
OMOP column and why — visible at a glance. The dense mapping files serve as
living documentation of the transformation logic without requiring anyone to wade
through engine code to understand what is being extracted.

2.2 Parsing Engine
~~~~~~~~~~~~~~~~~~

The engine iterates over sections and locales in the CCDA document:

1. Executes XPath queries for each rule
2. Applies fallback logic to select the first non-null value
3. Applies transformations, including date normalization and code translation
4. Emits rows for the target OMOP domain

2.3 Row Emission and Linking
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To maintain referential integrity without requiring intermediate tables or
temporary IDs, the engine uses content-based hashing:

- Each row's primary key is derived from a hash of its content
- Foreign keys are derived consistently from related content hashes
- This ensures reproducibility and deterministic linkage across multiple locales
  in a document

2.4 Advantages Over Traditional SQL Pipeline Thinking
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Aspect
     - Traditional ETL Pipeline
     - Declarative Parsing Engine
   * - Visibility
     - Logic spread across multiple staging tables
     - Mapping rules and engine clearly separate; mappings readable
   * - Iteration Speed
     - Slow; must rebuild or rerun batches
     - Fast; single-document execution and debugging
   * - Hierarchical Context
     - Flattened early; often loses provenance
     - Maintains CCDA structure until row emission
   * - Handling Variability
     - Complex joins and CASE statements
     - Coalesce/fallback logic declaratively handles multiple templates
   * - Maintenance
     - Changes require procedural edits
     - Changes often involve configuration edits only
   * - Scalability
     - Batch-oriented; table-first
     - Document-at-a-time; parallelizable without changing engine

2.5 Design Principles
~~~~~~~~~~~~~~~~~~~~~~

This architecture embodies several software engineering principles:

1. **Data-driven design**: rules and mappings encode variation, minimizing
   repeated code
2. **Declarative mapping**: separates "what to extract" from "how to extract it"
3. **Iteration-friendly**: enables rapid testing and debugging on single documents
4. **Content-addressed linking**: avoids fragile IDs and maintains integrity
5. **Transparency**: dense configuration provides an immediate view of the
   mapping without inspecting engine internals

While SQL pipelines are familiar to analysts and align with warehouse practices,
they can obscure complexity, particularly when input data is hierarchical and
heterogeneous. The engine approach better matches the document structure of CCDA
and allows for incremental adaptation to vendor differences.

3. Execution Environments
-------------------------

The engine runs in two complementary environments depending on the task at hand.

**Spark (production)** — ``layer_datasets.py`` wraps the parsing engine in a
Spark-compatible entry point for large-scale production volumes, making the
package suitable for enterprise clinical data pipelines.

**Command line or Jupyter (development and debugging)** — the same conversion
can be driven from a shell script or a Jupyter notebook against a single file or
a small directory. BI developers familiar with SQL pipelines sometimes overlook
how valuable this is: iterating on a single document takes seconds, intermediate
DataFrames can be inspected inline, and mapping changes can be validated
immediately without rebuilding a batch pipeline. Jupyter in particular is
well-suited to exploring CCDA structure, tracing a specific field through the
transformation, and spot-checking output — all before committing to a full run.

This symmetry between environments is a direct consequence of the document-at-a-time
architecture: because the engine processes one CCDA file independently, there is
no batch state to manage and no pipeline to rebuild when iterating on a mapping.

4. Conclusion
-------------

The CCDA → OMOP mapping engine provides a lightweight, declarative framework
that balances maintainability, robustness, and speed of iteration. It contrasts
with traditional SQL pipeline thinking by preserving hierarchical context,
centralizing mapping rules, and handling variable document structures elegantly.
Its content-driven PK/FK linking ensures deterministic row relationships without
requiring staging tables or arbitrary IDs. This architecture is broadly
applicable to clinical ETL work and provides a template for other
hierarchical-to-relational transformations in healthcare informatics.

References
----------

1. Rob Pike. *Notes on Programming in Go* — on emphasizing data structures over
   repeated code patterns.
2. HL7 Clinical Document Architecture (CCDA) Standard. Health Level Seven
   International, 2015.
3. Observational Medical Outcomes Partnership (OMOP) Common Data Model. OHDSI,
   2021.
4. Inmon, W. H. *Building the Data Warehouse*, 4th Edition. Wiley, 2005.
5. Kimball, R., Ross, M. *The Data Warehouse Toolkit*, 3rd Edition. Wiley, 2013.
6. Cormen, T., Leiserson, C., Rivest, R., Stein, C. *Introduction to
   Algorithms*, 4th Edition. MIT Press, 2022 — for graph and hashing principles.
