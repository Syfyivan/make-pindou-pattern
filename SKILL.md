---
name: make-pindou-pattern
description: Turn photos or illustrations of people, pets, recognizable objects, mascots, or simple icons into cute, clear, connected fuse-bead patterns with MARD colour codes and printable PNG/PDF charts. Use when the user asks for 拼豆图纸, fuse-bead or Perler-bead patterns, photo-to-cartoon-to-pattern conversion, portrait or pet bead art, object or logo pixel patterns, connected pendants, fewer-but-clearer beads, MARD A2/A3/F17 labels, or repairs to ugly faces, broken glasses, green skin speckles, disconnected regions, or over-complex photo pixelation.
---

# Make Pindou Pattern

Create an attractive bead-aware cartoon master first, then create the bead pattern. Never ask an image model to render the final grid, labels, counts, or MARD codes.

This Skill creates fuse-bead / Perler-bead charts, not jigsaw-puzzle cutting templates.

The end-to-end photo route requires the host agent to provide an image-generation or image-editing tool. `scripts/pindou` is a deterministic converter and never calls an AI API. If the host has no image tool, accept an approved cartoon or clean flat illustration, or explain that a photographic source cannot be beautified automatically in that environment.

## Understand the input

Read [input-guide.md](references/input-guide.md) before choosing a route.

- Accept one clear JPG or PNG as the ordinary input. One image is enough; extra reference images are optional when a face, marking, or colour is hidden or ambiguous.
- Support people, pets, animals, recognizable single objects, toys, vehicles, food, plants, mascots, simple logos, and flat illustrations.
- Give the best default results to one to four large, clearly visible subjects. More subjects can be attempted, but require a larger grid or split charts and may exceed the bead budget.
- Treat landscapes, crowds, text-heavy screenshots, highly reflective or transparent objects, and scenes full of tiny details as redesign tasks. Simplify them into a clear icon-like composition before conversion; do not promise photographic fidelity.
- Do not require a square source or a removed background. Crop and simplify during the cartoon stage, but prefer subjects that are in focus, not cut off, and not heavily occluded.

## Choose the route

- For a portrait photo, run the two-stage AI route below.
- For a pet, animal, or textured object photo, also use the two-stage AI route; preserve its silhouette, count, main markings, and defining colours.
- For an already approved cartoon, skip to `Convert the approved cartoon`.
- For a clean flat icon or simple illustration, direct conversion is appropriate.
- For a photographic portrait, do not use direct conversion unless the user explicitly accepts a more pixelated result and weaker likeness.
- For a requested standalone API integration, keep the provider outside the deterministic converter. The converter accepts any PNG/JPEG produced by GPT, Gemini, or another image model.

## Stage 1: create the cartoon master

1. Inspect every supplied photo before editing it.
2. Record identity-critical traits. For people, record count and placement, hair silhouette, glasses or hood, visible clothing colour, and expression. For pets or objects, record count, outer silhouette, main markings, defining parts, and dominant colours. Apply explicit user corrections over visual inference.
3. Use the available image-generation or image-editing tool. Preserve every intended subject and edit the supplied image instead of generating unrelated subjects.
4. Ask for a square, flat-colour, clean-line illustration on a single plain light background. For people, use a cute head-and-short-shoulder style and make the group touch through hair, hoods, or shoulders. For pets or objects, preserve the outer silhouette and defining parts, simplify texture, and create a broad natural connection when the result must be one pendant.
5. Use the constraints in [quality-contract.md](references/quality-contract.md) for portraits. For pets and objects, use the non-human rules in [input-guide.md](references/input-guide.md).
6. Inspect the generated cartoon at full size. Reject it before conversion when a subject is missing or duplicated, an identity trait is wrong, a defining shape is broken, unwanted speckles appear, or a requested pendant is not visibly connected. For portraits, also reject lumpy face contours, absent eyebrows, broken eyes or glasses, identical group expressions, and green/grey skin marks.
7. Prefer a local edit of the failed face, defining part, or connector. Regenerate the whole image only when the layout or subject count is wrong.

## Convert the approved cartoon

Run:

```bash
sh scripts/pindou CARTOON.png --output-dir OUTPUT_DIR --grid 72 --colors 22 --max-beads 3400
```

Use `--grid 72` as the default four-person balance. Raise the grid only when the resulting bead count still fits the user's budget. Keep `--colors` between 18 and 30 for portraits unless the user requests otherwise. The wrapper uses the Codex image runtime when available and otherwise falls back to the active `python3`.

The converter writes:

- `chart.png`: high-resolution labelled chart for WeChat, albums, and ordinary sharing
- `chart.pdf`: single-page vector chart for printing and lossless zooming

Keep the ordinary delivery directory limited to those two files. Use `--debug-exports` only during diagnosis when SVG, CSV, pattern JSON, or a saved report is genuinely needed.

It requires Pillow. Use ReportLab when available for a vector PDF and fall back to a high-resolution image PDF otherwise. If Pillow is unavailable, report that narrow missing runtime instead of changing the user's project dependencies.

## Enforce the quality gate

Read the JSON quality report printed by the command after every conversion. Do not save it in the ordinary delivery directory.

- Require `components == 1` for a pendant or keychain.
- Require `safe_for_pendant == true` before claiming the piece is structurally safe.
- Require `within_bead_budget == true` and `passes_quality_gate == true` before presenting the chart as final. The default ceiling is 3400 beads because the user's Little Prince reference is the accepted upper bound.
- Treat `critical_articulations > 0` as a thin-bridge warning. Edit the cartoon so adjacent hair, hood, or shoulder regions overlap more, then reconvert.
- Inspect `chart.png` at native pixel scale and enlarged scale. For portraits, check all faces. For pets and objects, check the outer silhouette, main markings, and defining parts.
- Do not accept a clean report as proof of attractiveness. The report proves structure and colour hygiene; visual inspection proves likeness and defining features.

## Iteration order

Fix defects in this order:

1. wrong subject count or identity-defining traits
2. face contour, eyes, eyebrows, mouth, and glasses continuity for portraits; silhouette and defining-part continuity for pets or objects
3. distinct expressions
4. connection strength
5. clothing, fur, texture, reflection, and secondary-part simplification
6. colour count and minor speckles

Do not reduce the grid while a face or defining feature is already unclear. Simplify background, clothing, fur, reflections, and secondary texture first.

## Provider boundary

Use GPT or Gemini only to produce or edit the cartoon master. Keep the following deterministic and provider-independent: resizing, MARD mapping, speckle cleanup, grid/chart rendering, counts, connectivity analysis, and exports. This makes provider replacement cheap and prevents API changes from corrupting finished patterns.
