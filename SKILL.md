---
name: make-pindou-pattern
description: Turn one or more portrait photos or an existing cartoon image into a cute, recognizable, connected fuse-bead pattern with MARD colour codes. Use when the user asks for 拼豆图纸, fuse-bead or Perler-bead portraits, AI cartoon-to-pattern conversion, a four-person connected pendant, fewer-but-clearer beads, MARD A2/A3/F17 labels, or repairs to ugly faces, broken glasses, green skin speckles, disconnected figures, or over-complex photo pixelation.
---

# Make Pindou Pattern

Create the attractive portrait first, then create the bead pattern. Never ask an image model to render the final grid, labels, counts, or MARD codes.

## Choose the route

- For a portrait photo, run the two-stage AI route below.
- For an already approved cartoon, skip to `Convert the approved cartoon`.
- For a requested standalone API integration, keep the provider outside the deterministic converter. The converter accepts any PNG/JPEG produced by GPT, Gemini, or another image model.

## Stage 1: create the cartoon master

1. Inspect every supplied photo before editing it.
2. Record identity-critical traits: person count and placement, hair silhouette, glasses or hood, visible clothing colour, and expression. Apply explicit user corrections over visual inference.
3. Use the available image-generation or image-editing tool. Preserve all people and edit the supplied photo instead of generating unrelated people.
4. Ask for a square, flat-colour, clean-line chibi illustration on a single plain light background. Make the people touch through hair, hoods, or short shoulders. Keep shoulders very short and faces large so the bead budget is spent on facial features.
5. Use the constraints in [quality-contract.md](references/quality-contract.md). Copy its prompt clauses when the request involves group portraits.
6. Inspect the generated cartoon at full size. Reject it before conversion when any person is missing or duplicated, an identity trait is wrong, a face contour is lumpy, an eyebrow is absent, an eye or glasses frame is broken, all expressions are identical, skin contains green/grey speckles, or the group is not visibly connected.
7. Prefer a local edit of the failed face or connector. Regenerate the whole image only when the layout or person count is wrong.

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
- Inspect `chart.png` at native pixel scale and enlarged scale. Check all faces, not just the overall silhouette.
- Do not accept a clean report as proof of attractiveness. The report proves structure and colour hygiene; visual inspection proves faces and expressions.

## Iteration order

Fix defects in this order:

1. wrong person count or identity traits
2. face contour, eyes, eyebrows, mouth, and glasses continuity
3. distinct expressions
4. connection strength
5. clothing simplification
6. colour count and minor speckles

Do not reduce the grid while a face is already unclear. Simplify clothing and hair shading first; preserve facial cells.

## Provider boundary

Use GPT or Gemini only to produce or edit the cartoon master. Keep the following deterministic and provider-independent: resizing, MARD mapping, speckle cleanup, grid/chart rendering, counts, connectivity analysis, and exports. This makes provider replacement cheap and prevents API changes from corrupting finished patterns.
