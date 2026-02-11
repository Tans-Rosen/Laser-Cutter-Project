# Laser-Cut Pencil Holder Generator

A Python program that generates SVG files for laser cutting a pencil holder from acrylic.

## Example Output

![Example pencil holders](https://github.com/user-attachments/Images/example_pencil_holders.png)

The image above showcases two example configurations produced directly from this script. These pencil holders were laser-cut from the generated SVG files without any manual modifications—demonstrating the script's production-ready output. With customizable dimensions, text engravings, fractal patterns, and divider configurations, these examples represent just a fraction of the nearly endless design possibilities this generator offers.

## Usage

```bash
python3 pencil_holder_generator.py
```

The program will prompt you for:

- **Length, Width, Height** (inches) — dimensions of the pencil holder
- **Right wall** — text (y/n), and if yes: text content; if no: fractal (y/n)
- **Left wall** — same options
- **Dividers** — 0, 1, or 2 (evenly spaced)

## Output

- Saves `pencil_holder.svg` in the current directory
- Pieces are laid out with shelf packing and 2mm gaps between them
- If pieces don't fit on an 18" × 12" sheet, you'll be prompted to enter smaller dimensions

## SVG Layers (for laser cutter setup)

1. **Engravings** — Text and Sierpinski fractal (vector engrave)
2. **T-slots** — Nut pockets, shaft slots, and screw holes
3. **Divider slots** — Slots in FRONT and BACK walls
4. **Outlines** — Wall outlines with finger joints (cut)

## Requirements

- Python 3.6+
- No external dependencies (uses only the standard library)
