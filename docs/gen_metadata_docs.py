"""
Generate RST documentation from metadata configs and data_driven_parse.py.

Writes:
  - docs/metadata/<config_name>.rst  — one page per parse config
  - docs/metadata/index.rst          — index of all configs
  - docs/field_types.rst             — one section per do_* function in
                                       data_driven_parse, documenting each
                                       config_type from its docstring

Run before sphinx-build:
    python docs/gen_metadata_docs.py
"""

import inspect
import os
import sys
import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent
METADATA_DIR = REPO_ROOT / "src" / "ccda_to_omop" / "metadata"
OUT_DIR = pathlib.Path(__file__).parent / "metadata"

# config_type descriptions for the legend / column notes
CONFIG_TYPE_DESC = {
    "ROOT":     "Defines the XPath root element for this config",
    "FIELD":    "Extracts an XML attribute value via XPath",
    "DERIVED":  "Computed by a Python function from other fields",
    "HASH":     "MD5/hash of a set of fields, used as a surrogate key",
    "FK":       "Foreign key copied from a joined dataset",
    "CONSTANT": "Fixed literal value written to every row",
    "PRIORITY": "Coalesces the first non-null value from prioritized candidates",
    "FILENAME": "The source XML filename",
    None:       "Not populated (placeholder)",
}


class _VTFn:
    """Sentinel returned for any VT.* attribute — records the function name."""
    def __init__(self, name): self._name = name
    def __repr__(self): return f"VT.{self._name}"
    def __call__(self, *a, **kw): return None


class _VTStub:
    def __getattr__(self, name): return _VTFn(name)


def _make_stubs() -> dict:
    """Return sys.modules stubs for ccda_to_omop imports."""
    import types
    vt_stub = _VTStub()
    vt_module = types.ModuleType("ccda_to_omop.value_transformations")
    vt_module.__getattr__ = lambda name: _VTFn(name)  # type: ignore
    ccda_module = types.ModuleType("ccda_to_omop")
    ccda_module.value_transformations = vt_stub  # type: ignore
    return {
        "ccda_to_omop": ccda_module,
        "ccda_to_omop.value_transformations": vt_module,
    }


# Install stubs once — before any exec() so numpy's C extensions are never
# evicted from sys.modules (mock.patch.dict would remove them on exit).
_STUBS = _make_stubs()
for _k, _v in _STUBS.items():
    sys.modules.setdefault(_k, _v)


def _load_metadata(path: pathlib.Path) -> dict:
    """Execute a metadata file and return its ``metadata`` dict."""
    ns: dict = {}
    exec(compile(path.read_text(), str(path), "exec"), ns)
    return ns.get("metadata", {})


def _rst_title(text: str, char: str = "=") -> str:
    return f"{text}\n{char * len(text)}\n"


def _rst_table(rows: list[tuple], headers: list[str]) -> str:
    """Render a simple RST grid table."""
    if not rows:
        return "(no fields)\n"

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    def _sep(char="-"):
        return "+" + "+".join(char * (w + 2) for w in col_widths) + "+"

    def _row(cells):
        return "|" + "|".join(f" {str(c):<{w}} " for c, w in zip(cells, col_widths)) + "|"

    lines = [_sep(), _row(headers), _sep("=")]
    for r in rows:
        lines += [_row(r), _sep()]
    return "\n".join(lines) + "\n"


def _describe_field(field_name: str, cfg: dict) -> tuple:
    """Return a table row tuple for one field entry."""
    ctype = cfg.get("config_type")

    # Details column: vary by config_type
    if ctype == "ROOT":
        details = cfg.get("element", "")
    elif ctype == "FIELD":
        element = cfg.get("element", "")
        attr = cfg.get("attribute", "")
        dtype = cfg.get("data_type", "")
        parts = [f"``{element}`` @{attr}"]
        if dtype:
            parts.append(f"[{dtype}]")
        if "priority" in cfg:
            parts.append(f"→ priority {cfg['priority']}")
        details = " ".join(parts)
    elif ctype == "DERIVED":
        fn = cfg.get("FUNCTION", "")
        fn_name = getattr(fn, "__name__", repr(fn))
        args = cfg.get("argument_names", {})
        arg_str = ", ".join(f"{k}={v}" for k, v in args.items())
        details = f"``{fn_name}({arg_str})``"
    elif ctype == "HASH":
        fields = cfg.get("fields", [])
        details = "hash(" + ", ".join(fields) + ")"
    elif ctype == "FK":
        details = f"FK → ``{cfg.get('FK', '')}``"
    elif ctype == "CONSTANT":
        details = f"``{cfg.get('constant_value', '')}``"
    elif ctype == "PRIORITY":
        details = "coalesce candidates by priority"
    elif ctype == "FILENAME":
        details = "source XML filename"
    elif ctype is None:
        details = "—"
    else:
        details = str(cfg)

    order = str(cfg.get("order", ""))
    return (field_name, str(ctype), order, details)


def generate_config_rst(config_name: str, config: dict, source_file: str) -> str:
    """Generate RST content for one parse configuration."""
    lines = []
    lines.append(_rst_title(config_name))
    lines.append(f"*Source file:* ``{source_file}``\n")

    # Root XPath
    root = config.get("root", {})
    if root:
        lines.append(_rst_title("Root XPath", "-"))
        lines.append(f".. code-block:: xpath\n\n    {root.get('element', '')}\n")
        domain = root.get("expected_domain_id", "")
        if domain:
            lines.append(f"**Expected OMOP domain:** {domain}\n")

    # Fields table (skip root, sort by order then name)
    field_entries = [
        (name, cfg) for name, cfg in config.items() if name != "root"
    ]
    field_entries.sort(key=lambda x: (x[1].get("order", 999), x[0]))

    rows = [_describe_field(name, cfg) for name, cfg in field_entries]

    lines.append(_rst_title("Fields", "-"))
    lines.append(_rst_table(rows, ["Field", "Type", "Order", "Details"]))

    # Config-type legend
    lines.append(_rst_title("Config type reference", "-"))
    legend_rows = [(k or "None", v) for k, v in CONFIG_TYPE_DESC.items()]
    lines.append(_rst_table(legend_rows, ["config_type", "Meaning"]))

    return "\n".join(lines)


# Map do_* function name → the config_type string it handles (for the section heading)
_FN_TO_CONFIG_TYPE = {
    "do_none_fields":         "None",
    "do_constant_fields":     "CONSTANT",
    "do_filename_fields":     "FILENAME",
    "do_basic_fields":        "FIELD",
    "do_foreign_key_fields":  "FK",
    "do_derived_fields":      "DERIVED",
    "do_derived2_fields":     "DERIVED2",
    "do_hash_fields":         "HASH",
    "do_priority_fields":     "PRIORITY",
}


def generate_field_types_rst() -> str:
    """Return RST content documenting each config_type from its do_* function docstring."""
    src_path = str(REPO_ROOT / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    # Temporarily remove our stubs so the real package can be imported
    saved_stubs = {k: sys.modules.pop(k) for k in list(_STUBS) if k in sys.modules}
    try:
        import ccda_to_omop.data_driven_parse as ddp
    finally:
        sys.modules.update(saved_stubs)

    lines = [
        _rst_title("Field Types (config_type reference)"),
        "Each field in a parse configuration has a ``config_type`` that controls how\n"
        "the parser populates it. The behaviour of each type is implemented in\n"
        "``data_driven_parse.py`` by a corresponding ``do_*`` function.\n",
    ]

    fns = [
        (name, fn)
        for name, fn in inspect.getmembers(ddp, inspect.isfunction)
        if name.startswith("do_")
    ]
    # Sort by source line so the page follows execution order
    fns.sort(key=lambda nf: inspect.getsourcelines(nf[1])[1])

    for fn_name, fn in fns:
        config_type = _FN_TO_CONFIG_TYPE.get(fn_name, fn_name)
        doc = inspect.getdoc(fn) or "(no docstring)"

        lines.append(_rst_title(config_type, "-"))
        lines.append(f"*Implemented by:* ``{fn_name}()``\n")
        lines.append(doc + "\n")

    return "\n".join(lines)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    py_files = sorted(
        p for p in METADATA_DIR.iterdir()
        if p.suffix == ".py" and p.name not in ("__init__.py",)
        and not p.name.endswith(".py~")
    )

    generated = []

    for path in py_files:
        try:
            metadata = _load_metadata(path)
        except Exception as e:
            print(f"  WARNING: could not load {path.name}: {e}")
            continue

        for config_name, config in metadata.items():
            rst = generate_config_rst(config_name, config, path.name)
            # Safe filename: replace hyphens and spaces with underscores
            safe_name = config_name.replace("-", "_").replace(" ", "_")
            out_path = OUT_DIR / f"{safe_name}.rst"
            out_path.write_text(rst)
            generated.append((config_name, safe_name))
            print(f"  wrote {out_path.name}")

    # Write metadata index
    index_lines = [
        _rst_title("Parse Configurations"),
        "One page per metadata configuration file. Each config defines how a\n"
        "C-CDA section is parsed into an OMOP domain table.\n",
        ".. toctree::\n   :maxdepth: 1\n",
    ]
    for config_name, safe_name in sorted(generated):
        index_lines.append(f"   {safe_name}")
    index_lines.append("")

    (OUT_DIR / "index.rst").write_text("\n".join(index_lines))
    print(f"  wrote metadata/index.rst ({len(generated)} configs)")

    # Field types page
    field_types_path = pathlib.Path(__file__).parent / "field_types.rst"
    field_types_path.write_text(generate_field_types_rst())
    print(f"  wrote field_types.rst")


if __name__ == "__main__":
    main()
