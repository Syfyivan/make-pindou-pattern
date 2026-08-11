# Input image guide

Use this guide to decide whether to convert directly, create an AI cartoon master first, or ask for a better source image.

## Accepted inputs

- Accept one JPG, JPEG, or PNG as the normal starting point.
- One image is enough when the subject is clear. Accept optional reference images only when a face, marking, hidden side, or important colour is ambiguous.
- Do not require a square image or a transparent background. Recompose and separate the background during the cartoon stage.
- Prefer a short edge of roughly 800 pixels or more, but treat clarity and subject size as more important than raw resolution.

## Supported subjects

### People

- Support individual portraits and groups, with one to four people as the best default range.
- Preserve count, placement, hair silhouette, glasses, hats or hoods, visible clothing colour, and distinct expressions.
- Prefer head-and-short-shoulder compositions. Simplify clothes before reducing facial detail.
- For more than four people, explain that recognizable faces require a larger grid, more beads, or separate charts.

### Pets and animals

- Preserve species, ear and head silhouette, muzzle shape, main coat patches, eye placement, and dominant colours.
- Simplify individual hairs, whiskers, and subtle fur gradients into a few coherent regions.
- Keep small dark features such as the nose and eyes complete rather than scattered.

### Objects, toys, vehicles, food, and plants

- Preserve the outer silhouette, count, dominant colours, and two or three defining parts.
- Remove reflections, texture, tiny labels, repeated small parts, and background clutter.
- For transparent or reflective objects, redesign them as a flat icon before conversion.

### Mascots, simple logos, icons, and flat illustrations

- Direct conversion is usually appropriate when the source already uses flat colours, a clean outline, little texture, and no tiny text.
- Preserve negative spaces only when they remain wide enough to survive the target grid.
- Do not reproduce tiny lettering. Replace it with a larger symbol or omit it with the user's knowledge.

## Route selection

Use the AI cartoon stage for:

- photographs of people, pets, animals, or textured objects
- complex lighting, shadows, clothing, fur, or backgrounds
- subjects that must be rearranged into one connected pendant

Use direct conversion for:

- an approved cartoon master
- a clean mascot, simple logo, icon, or flat illustration
- a simple object photo only when the background is plain and the user accepts a more literal pixel result

Do not directly pixelate a portrait by default. It spends cells on photographic noise and often damages the face, eyes, skin, and glasses.

## Image quality checklist

Prefer an image where:

1. Every intended subject is visible exactly once.
2. The main subject occupies a substantial part of the frame.
3. Faces or defining parts are in focus and not heavily covered.
4. Lighting and colour are natural enough to identify skin, coat, or object colours.
5. The crop leaves enough room to make connected hair, shoulders, paws, leaves, or object edges.

Ask for another image, or explain the limitation, when:

- motion blur or compression destroys the eyes or defining edges
- strong backlight, filters, or colour casts hide natural colours
- faces are tiny, turned away, covered, or merged into a crowd
- the scene contains many small subjects, dense text, or important thin lines
- photographic landscape detail is itself the user's main requirement

## Complexity guidance

- Simple icon or single object: start around 40–60 grid cells and 8–16 colours.
- Single portrait or pet: start around 56–72 grid cells and 18–24 colours.
- Two to four connected people or subjects: start around 72–100 grid cells and 18–30 colours, then enforce the bead budget.
- Do not lower the grid to solve a bead-budget problem when it already damages a face or defining feature. Simplify background, clothing, fur, reflections, and secondary parts first.

## Delivery promise

Promise a bead-aware interpretation, not photographic reproduction. Deliver `chart.png` for sharing and `chart.pdf` for printing. For a pendant or keychain, require one connected component and no critical thin bridge before describing it as structurally safe.
