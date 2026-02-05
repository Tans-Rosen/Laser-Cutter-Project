"""Test with longer text on side walls to check for overflow."""

from validate import validate_inputs
from generate import generate_svg

# Create a box with longer text on the left wall
test_inputs = {
    'length': 6.0,
    'width': 4.0,
    'height': 3.0,
    'numDividers': 0,
    'frontText': False,
    'frontTextContent': '',
    'frontFractal': False,
    'backText': False,
    'backTextContent': '',
    'backFractal': False,
    'leftText': True,
    'leftTextContent': 'Incline',  # This is the word from the user's image
    'leftFractal': False,
    'rightText': False,
    'rightTextContent': '',
    'rightFractal': False,
}

print("Generating SVG with 'Incline' on left wall...")
params = validate_inputs(test_inputs)
svg = generate_svg(params)

with open('/tmp/test_incline.svg', 'w') as f:
    f.write(svg)

print("✓ SVG generated: /tmp/test_incline.svg")

# Find the text element
import re
rotated = re.findall(r'<g transform="translate\(([^,]+),([^)]+)\) rotate\(([^)]*)\)">.*?<text[^>]*font-size="([^"]*)"[^>]*>([^<]+)</text>', svg, re.DOTALL)

print(f"\nText elements with rotation: {len(rotated)}")
for x, y, angle, size, text in rotated:
    print(f"  Text: '{text}'")
    print(f"    Position: ({float(x):.1f}, {float(y):.1f})")
    print(f"    Font size: {size}")
    print(f"    Rotation: {angle}°")

# Also extract the piece boundaries to understand the safe zone
paths = re.findall(r'<g transform="translate\(([^,]+),([^)]+)\)".*?<path[^>]*d="([^"]*)"', svg, re.DOTALL)
if paths:
    print(f"\nPieces found: {len(paths)}")
    # Last path should be the left wall
    if paths:
        tx, ty, path_d = paths[-1]
        # Extract min/max from path
        m = re.search(r'L\s+([\d.]+)\s+0', path_d)
        if m:
            width = float(m.group(1))
            print(f"  Left wall approximate width: {width:.1f}mm")
