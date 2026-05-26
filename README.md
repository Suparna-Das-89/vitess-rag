# vitess-rag

Structure-aware RAG pipeline for VITESS documentation with semantic parsing, table-aware indexing, ambiguity-aware retrieval, and ChromaDB integration.

---

# Quick Start

## 1. Clone the repository

```bash
git clone https://github.com/Suparna-Das-89/vitess-rag-package
cd vitess-rag-package
```

## 2. Install dependencies

```bash
uv sync
```

This automatically:
- creates the virtual environment
- installs dependencies
- installs the package

---

## 3. Configure environment variables

Create a `.env` file in the project root:

```env
BLABLADOR_API_KEY=your_api_key_here
BLABLADOR_BASE_URL=https://api.helmholtz-blablador.fz-juelich.de/v1/
VITESS_AGENT_MODEL=alias-large
BLABLADOR_EMBEDDING_MODEL=text-embedding-ada-002
```

---

## 4. Build the vector index

```bash
uv run vitess-rag index
```

Expected output:

```text
Indexed chunks: 379
Collection count: 379
```

---

## 5. Ask questions

```bash
uv run vitess-rag ask "What is guide ideal?"
```

Example queries:

```bash
uv run vitess-rag ask "What does option -z mean?"
uv run vitess-rag ask "Explain filter2D"
uv run vitess-rag ask "What are the neutron reflectivity properties of different mirror coatings?"
```
---

# Overview

`vitess-rag` is a retrieval-augmented generation system designed for technical VITESS documentation.

The original documentation was HTML-derived and difficult to process directly because it contained:

* nested documentation structure
* markdown tables
* mathematical equations
* code blocks
* external links
* formatting artifacts
* repeated command options across modules

Instead of flattening documentation into plain text, the project builds a structure-aware indexing pipeline that preserves semantic and contextual information during parsing and retrieval.

The resulting chunks are embedded into ChromaDB and queried through a metadata-aware retrieval pipeline optimized for technical documentation and command-oriented workflows.

---

# Retrieval Challenge

Technical documentation frequently contains context-dependent terminology and overloaded command options.

For example:

```text
What does option -z mean?
```

may resolve to different meanings depending on the module being referenced.

Traditional vector search often fails on these queries because embedding similarity alone cannot resolve contextual ambiguity.

`vitess-rag` addresses this through:

* module-aware retrieval
* command-option extraction
* metadata-guided reranking
* ambiguity detection
* contextual candidate selection

---

# Architecture

```text
HTML / Markdown Documentation
              ↓
Structure-Aware Parser
              ↓
Semantic Chunk Generation
              ↓
Metadata Enrichment
              ↓
Embedding Pipeline
              ↓
ChromaDB Vector Index
              ↓
Candidate Retrieval
              ↓
Metadata-Guided Reranking
              ↓
Ambiguity Detection
              ↓
Context Builder
              ↓
LLM / Agent Response
```

---

# Core Components

## Structure-Aware Parser

The parser converts documentation into semantic chunks instead of flat text blocks.

Supported parsing includes:

* text sections
* markdown tables
* mathematical equations
* code blocks
* hierarchical headings
* inline markdown formatting
* external links

The parser preserves contextual hierarchy during chunk generation to improve downstream retrieval quality.

---

## Table Parsing

Markdown tables are parsed into structured row-level representations.

The indexing pipeline extracts:

* parameter names
* command options
* descriptions
* table descriptors
* contextual hierarchy

This is particularly important for technical CLI documentation where command options are primarily documented in tables.

---

## Chunk Representation

Instead of storing only raw text, indexed chunks preserve structured contextual information extracted during parsing.

Depending on the chunk type, chunks may contain:

### Hierarchical metadata

* module
* section
* subsection
* subsubsection
* source file

### Table-aware fields

* table title
* table descriptors
* row-level parameter fields
* command options
* parameter descriptions

### Structural indicators

* chunk type
* code-block indicators
* pre-table context markers
* external links

Example indexed chunk:

```json
{
  "chunk_id": "filter_md__vitess_module_filter__table__13",
  "chunk_type": "table",
  "metadata": {
    "module": "VITESS Module Filter",
    "section": null,
    "subsection": null,
    "subsubsection": null,
    "source_file": "filter.md",
    "is_pre_table_text": false,
    "is_code_block": false
  },
  "content": "Row: Parameter Unit: filter parameter 4 | Description: 4th parameter determining which trajectories are kept | Range or Values: none, posy, posz, divy, divz, lambda, energy, time, ky, kz, r, phi, colvert, colhor, color | Command Option: -L",
  "external_links": null,
  "descriptor": [
    "Parameter Unit",
    "Description",
    "Range or Values",
    "Command Option"
  ],
  "table_title": "The following table lists the parameters of the module 'filter'.",
  "row_fields": {
    "parameter_unit": "filter parameter 4",
    "description": "4th parameter determining which trajectories are kept",
    "range_or_values": "none, posy, posz, divy, divz, lambda, energy, time, ky, kz, r, phi, colvert, colhor, color",
    "command_option": "-L"
  }
}
```

This structured representation enables metadata-aware retrieval and context-sensitive reranking.

---

## Retrieval Pipeline

The retrieval layer combines semantic similarity with rule-based reranking strategies.

Implemented retrieval stages include:

* query normalization
* command-option extraction
* module hint detection
* candidate retrieval
* metadata-aware reranking
* ambiguity detection
* context construction

The reranking system explicitly boosts:

* exact command-option matches
* module-consistent results
* table-derived chunks
* metadata-aligned results

---

## Ambiguity Detection

The system explicitly detects conflicting interpretations across modules.

When multiple valid meanings exist for a command option, the retrieval layer generates clarification prompts instead of returning incorrect matches.

Example:

```text
The option `-z` has different meanings depending on the specific VITESS module you are using. It generally refers to a **vertical position filter** (in cm):

*   **Filter Module**: Sets the **minimum z** (lower bound of the filter range in the vertical direction).
*   **Monitor Module**: Defines the **low and up bounds for the z-position** (minimal and maximal vertical position). *Note: In some contexts, it may also refer to wavelength bounds, but the primary definition is position.*
*   **Writeout Module**: Specifies the **minimum and maximum Z position** to filter neutrons; only neutrons within this vertical space range are read.

Please specify which module you are using if you need a more precise definition.
```

---

## ChromaDB Integration

Parsed chunks are transformed into Chroma-compatible documents with normalized metadata and persistent vector storage.

The indexing layer handles:

* chunk serialization
* metadata flattening
* embedding generation
* persistent indexing

---

## Embeddings

The project includes a custom OpenAI-compatible embedding implementation using the Blablador API.

The embedding layer supports:

* configurable embedding endpoints
* credential validation
* reusable embedding abstractions
* Chroma-compatible embedding functions

---

## Agent Layer

A LangChain-based research agent integrates retrieval tools with the indexed VITESS knowledge base.

The agent layer supports:

* retrieval-augmented answering
* structured context injection
* technical documentation querying

---

# Project Structure

```text
vitess-rag-package/
│
├── data/
│   ├── filter.md
│   ├── guide.md
│   ├── monitor.md
│   ├── read_in.md
│   └── writeout.md
│
├── src/
│   └── vitess_rag/
│       ├── __init__.py
│       ├── __main__.py
│       ├── agent.py
│       ├── chroma.py
│       ├── embeddings.py
│       ├── io.py
│       ├── markdown_rendering.py
│       ├── models.py
│       ├── parser.py
│       ├── retrieval.py
│       ├── table_parser.py
│       ├── text_utils.py
│       └── tools.py
│
├── tests/
│   ├── __init__.py
│   ├── test_chroma.py
│   ├── test_embeddings.py
│   ├── test_parser.py
│   └── test_retrieval.py
│
├── .env.example
├── .gitignore
├── README.md
├── pyproject.toml
└── uv.lock
```

---

# CLI Workflow

Available commands:

```bash
vitess-rag index
vitess-rag ask
```

---


# Environment Configuration

```bash
cp .env.example .env
```

Configure required API credentials inside `.env`.

---

# Build the Vector Index

```bash
uv run vitess-rag index
```

---

# Query the System

Example:

```bash
uv run vitess-rag ask "What are the neutron reflectivity properties of different mirror coatings?"
```

```bash
uv run vitess-rag ask "What does option -z mean?"
```

---

# Testing

Run the complete test suite:

```bash
uv run pytest
```

Current tests include:

* parser behavior
* table parsing
* metadata extraction
* retrieval normalization
* reranking
* ambiguity detection
* embedding validation

---

# Reproducibility

Verified from a clean clone:

```bash
git clone https://github.com/Suparna-Das-89/vitess-rag-package.git
cd vitess-rag-package

uv sync

cp .env.example .env
# add your own Blablador API key to .env

uv run pytest

uv run vitess-rag index
uv run vitess-rag ask "What does option -z mean?"
```

---

# Requirements

* Python 3.10+
* uv
* ChromaDB
* Blablador/OpenAI-compatible API endpoint

---

# Author

Suparna Das
