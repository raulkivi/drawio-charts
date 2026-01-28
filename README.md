# draw.io Charts Project

Purpose

This repository provides resources, templates, and programmatic guidance for creating and managing draw.io diagrams. It is focused on making reproducible, scriptable diagrams (XML `mxfile` files) and includes style references, examples, and conventions to support automation and consistency.

Project structure

- `diagrams/`: Editable diagram files organized by category (e.g. `architecture/`, `samples/`). Diagram files use the `.drawio` extension. Note: this checkout includes `diagrams/samples/` with example diagrams.
- `docs/`: Human-readable documentation and references for the draw.io XML format and styling. Files include `drawio-quickstart.md`, `drawio-format-reference.md`, `drawio-style-reference.md`, `mxcell-api-reference.md`, and `mxgeometry-api-reference.md`.
- `.github/copilot-instructions.md`: Contributor guidance and programmatic editing patterns for this workspace (contains shape libraries, XML skeletons, and best practices).
- `.gitignore`: The repository ignores `*.drawio` files by default to avoid committing binary/large diagram files; update as needed.
- `exports/` (optional): Recommended location for exported images (`.svg`, `.png`, `.pdf`) and generated artifacts.

Getting started

1. Clone the repository and open it in VS Code.
2. Install the Draw.io integration extension (ID: `hediet.vscode-drawio`).
3. Open files under `diagrams/` to view or edit them with the extension.
4. Follow the programmatic patterns in `.github/copilot-instructions.md` when generating or editing diagrams by script.

Contributing

- Add new diagram templates under `diagrams/` and keep each diagram's purpose clear in its filename.
- Use the `docs/` guides and `.github/copilot-instructions.md` for conventions: unique `mxCell` ids, `parent="1"`, consistent styles, and image paths for libraries.

Documentation

See the `docs/` folder for format and style references and `.github/copilot-instructions.md` for workspace-specific guidelines and shape library lists.

Open the Draw.io extension to preview diagrams and verify shapes and connectors render correctly.