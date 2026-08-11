# Portrait quality contract

Use these clauses in the image-editing prompt and preserve user-specific corrections.

## Required composition

- Preserve exactly the people in the reference photo; do not add, remove, merge, or duplicate anyone.
- Arrange them as one compact connected cluster. Hair, hood, or short shoulders must touch naturally; no floating heads and no long thin one-pixel-looking connectors.
- Crop at the shoulders rather than showing a full upper body. Keep faces large, include only enough clothing to identify each person and connect the cluster, and keep that clothing flat and simple.
- Use a square canvas and a single plain warm off-white background with no texture, props, text, grid, labels, or decorative dots.

## Required face construction

- Draw smooth, continuous face contours with a stable chin and cheeks.
- Give every person two complete eyes and two complete eyebrows. Keep each eye a coherent shape; never scatter highlights or fragments around it.
- Keep glasses as two continuous closed frames with a visible bridge and temples. Do not let hair erase random sections of the frames.
- Preserve different expressions from the photo or requested design. Useful variants include an open smile, closed smile, small kiss mouth, and calm closed mouth.
- Keep important identity traits: hair silhouette and parting, glasses, hats or hoods, and visible clothing colour.
- For large anime eyes, use one dark iris mass per eye with at most one simple highlight. For simple eyes, use a complete dark oval. Do not use square white eye boxes.

## Bead-aware drawing constraints

- Use flat colour regions, thick clean outlines, and no photographic texture.
- Avoid blush freckles, skin mottling, green/grey facial marks, thin eyelashes, tiny jewellery, fabric texture, and isolated one-pixel details.
- Make eyebrows, mouth lines, glasses, and eye shapes thick enough to survive reduction to the selected target grid, then raise the grid when complete features still cannot fit cleanly.
- Limit shading to one shadow tone per material. Spend detail on faces, not clothing folds.
- Use natural warm skin colours only. Keep green and blue strictly out of skin regions.
- Spend the fewest cells that preserve complete facial features and a safe connection. Remove empty decoration, torso area and clothing detail before reducing any face.

## Visual rejection checklist

Reject the cartoon master when any answer is no:

1. Are all intended people present exactly once?
2. Can each person be distinguished by at least two traits?
3. Are all face contours smooth and appealing?
4. Are all eyes, brows, mouths, and glasses complete?
5. Are at least two expressions visibly different in a group portrait?
6. Does the cluster touch through broad natural regions?
7. Is the background plain and separable from every person?
