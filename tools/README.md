# Report Template Designer

A zero-dependency, Python-based **visual designer** for the Handlebars
HTML templates used by your reporting engine (POS receipts and A4
reports). Build templates from blocks, customise theme and page setup,
preview live, and save anywhere in the repo - no `pip install`, no
Node.js, just `python3`.

## At a glance

```
python3 tools/server.py
# open http://127.0.0.1:5173
```

You get:

- **Block-based editor** - 14 block types (Title, Company header, Info
  row, Party, Meta table, Items table, Totals, Grand total, Footer,
  Image, Divider, Spacer, Text, Raw HTML). Add from a palette,
  drag to reorder, click to edit each block in place.
- **Theme controls** - 4 preset themes (POS, A4 Modern, A4 Minimal, A4
  Dark) plus full custom (font, font size, text colour, accent, border
  colour and style, uppercase toggle).
- **Page setup** - 80mm / 58mm thermal, A4, US Letter, or custom
  width; configurable margin and orientation.
- **Data namespace** - one click switches between
  `invoiceMainData` / `poMainData` / `grnMainData` / etc. so block
  fields like `qty` resolve to the right Handlebars path.
- **Live WYSIWYG preview** - iframe re-renders on every change with
  sample data. Hover any block in the rail to outline the matching
  section in the preview.
- **File menu** - **New** from preset, **Open** (any HTML file in the
  repo), **Save**, and **Save as...** (with folder picker and
  conflict detection).
- **Round-trip persistence** - saved files embed a hidden
  `<!-- RT_DESIGN_V1: ... -->` comment so re-opening pulls you back
  into the visual editor with every block intact, not into a raw
  source view.

## Requirements

- Python 3.10+ (standard library only)
- A modern browser (Chrome, Firefox, Safari, Edge)

## Run

```bash
python3 tools/server.py            # localhost:5173
python3 tools/server.py --host 0.0.0.0 --port 8080
```

Open <http://127.0.0.1:5173> in your browser.

## Workflow

### Create a new template

1. Click **File -> New from preset...** and pick a starting point
   (Blank for a clean slate, or one of the four document presets).
2. Use **+ Add block** in the toolbar to insert blocks. Each block
   appears in the rail and the live preview simultaneously.
3. Click a block in the rail to expand its config: edit text, fields,
   table columns, alignment, etc. The preview updates live.
4. Drag the **left handle** on any block to reorder.
5. Open the **Theme** tab to pick a preset or override font, colours,
   border style.
6. Open the **Page** tab to set page size and margins.
7. Open the **Data** tab to set the document title, file name, and
   the main / details data namespaces (e.g. `invoiceMainData`).
8. **File -> Save as...** to write the file. Pick a folder
   (`generated/` is the default) and a filename.

Keyboard shortcuts: `Ctrl/Cmd+S` saves, `Ctrl/Cmd+Shift+S` save-as,
`Esc` closes any modal.

### Modify an existing template

Click **File -> Open file...** to browse every editable HTML template
in the repo (grouped by folder, with a filter box). Each row shows a
badge:

- **designer** - the file was created here. Picking it reloads the
  exact block tree, theme, and page setup back into the editor.
- **raw** - the file was authored elsewhere. Picking it imports the
  whole HTML into a single Raw-HTML block; from there you can wrap
  it, replace pieces with structured blocks, and re-save.

`Save` writes back to the original path. `Save as...` writes to a
new path, leaving the original untouched.

### Save-as

The save-as dialog has:

- **Folder** - dropdown of every existing repo folder (excluding
  `tools/`, `.git/`, etc.) plus `generated/`.
- **Filename** - `.html` is added automatically.
- **Overwrite if it already exists** - unchecked by default. If the
  target exists, the server returns 409 and the editor surfaces a
  clear error rather than silently overwriting.

### Safety

The server validates every write:

- Only `.html` files may be edited or saved.
- Paths that resolve outside the repo root are rejected.
- `tools/`, `.git/`, `.github/`, and `node_modules/` are excluded
  from the file picker and rejected for save.

## Layout

```
tools/
  designer.py       # block-based renderer (design dict -> HTML+CSS)
  block_types.py    # editor schema for every block type
  designs.py        # built-in preset designs
  hbs.py            # tiny Handlebars-compatible renderer (preview only)
  sample_data.py    # data used by the live preview
  server.py         # local HTTP server + API
  public/
    index.html
    style.css
    app.js          # designer front-end
  builder.py        # legacy spec -> HTML (still used by CLI)
  presets.py        # legacy CLI presets
  cli.py            # interactive terminal front-end
  README.md
generated/          # default output folder (auto-created)
```

## CLI (legacy, still works)

```bash
python3 tools/cli.py
```

The CLI walks through a simpler, prompt-by-prompt flow that emits the
same kind of HTML the designer produces. It's useful for scripted
generation but doesn't support the full designer feature set.

## How a design is stored

A design is a JSON-serialisable dict:

```python
{
    "name":  "salesInvoice",
    "title": "SALES INVOICE",
    "data":  {"main": "invoiceMainData", "details": "invoiceDetailsData"},
    "page":  {"size": "80mm", "margin": "3mm", "orientation": "portrait"},
    "theme": {"preset": "pos", "accent": "#000000", ...},
    "blocks": [
        {"id": "b1", "type": "title",
         "config": {"text": "SALES INVOICE", "level": 1, "align": "center"}},
        {"id": "b2", "type": "items-table",
         "config": {"columns": [...], "headerStyle": "underline", ...}},
        ...
    ],
}
```

When saved, the design is base64-encoded into an HTML comment placed
**after** `</html>` so it never affects rendering:

```html
<!DOCTYPE html>
<html>...
</html>
<!-- RT_DESIGN_V1:eyJuYW1lIjogInNhbGVz... -->
```

`/api/design/load` reads this back, and the **Open** picker shows the
**designer** badge so you know which files reopen visually.

## API (for scripts)

| Method | Path                       | Body / Query                          | Returns                       |
| ------ | -------------------------- | ------------------------------------- | ----------------------------- |
| GET    | `/api/block-types`         | -                                     | block schemas + theme presets |
| GET    | `/api/designs`             | -                                     | built-in design presets       |
| GET    | `/api/templates`           | -                                     | list of editable .html files  |
| GET    | `/api/template?path=...`   | -                                     | file content + design (if any)|
| POST   | `/api/design/render`       | `{design}`                            | `{html, rendered}`            |
| POST   | `/api/design/save`         | `{design, path}`                      | `{path, bytes}`               |
| POST   | `/api/design/save-as`      | `{design, path, overwrite}`           | `{path, bytes}` or 409        |
| POST   | `/api/design/load`         | `{path}`                              | `{path, content, design?}`    |
| POST   | `/api/render`              | `{html}`                              | `{rendered}` (raw HTML)       |
| POST   | `/api/template/save`       | `{path, content}`                     | `{path, bytes}` (raw save)    |

## Notes

- The live preview uses placeholder sample data from `sample_data.py`;
  it's only for visual checking. The generated file is real Handlebars
  HTML that your reporting engine will populate at runtime.
- Generated HTML uses the same `{{var}}`, `{{#if}}`, and `{{#each}}`
  patterns as the existing templates, so files saved by the designer
  drop straight into your reporting engine.
- Move freshly-created files out of `generated/` once you're happy
  with them - they belong wherever the rest of your invoice/PO/GRN
  templates live.
