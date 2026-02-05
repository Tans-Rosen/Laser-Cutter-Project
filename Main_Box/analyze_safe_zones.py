"""Analyze safe zone and text positioning for debugging."""

from validate import validate_inputs
from generate import generate_svg
import re

test_inputs = {
    'length': 6.0,
    'width': 4.0,
    'height': 3.0,
    'numDividers': 0,
    'frontText': True,
    'frontTextContent': 'Incline',
    'frontFractal': False,
    'backText': False,
    'backTextContent': '',
    'backFractal': False,
    'leftText': True,
    'leftTextContent': 'Left',
    'leftFractal': False,
    'rightText': False,
    'rightTextContent': '',
    'rightFractal': False,
}

print("Generating SVG with text on front and left walls...\n")
params = validate_inputs(test_inputs)
svg = generate_svg(params)

# Extract text elements and their bounding info
print("Text elements in SVG:")
print("-" * 60)

# Find rotated text
rotated = re.findall(r'<g transform="translate\(([^,]+),([^)]+)\) rotate\(([^)]*)\)">.*?<text[^>]*>([^<]+)</text>', svg, re.DOTALL)
print(f"Rotated text: {len(rotated)}")
for x, y, angle, text in rotated:
    print(f"  {text:15} at ({float(x):.1f}, {float(y):.1f}), rotated {angle}°")

# Find non-rotated text
non_rotated = re.findall(r'<text x="([^"]+)"[^>]*y="([^"]+)"[^>]*>([^<]+)</text>', svg)
print(f"\nNon-rotated text: {len(non_rotated)}")
for x, y, text in non_rotated:
    print(f"  {text:15} at ({float(x):.1f}, {float(y):.1f})")

with open('/tmp/analyze_safe_zones.svg', 'w') as f:
    f.write(svg)

print("\nSVG saved to /tmp/analyze_safe_zones.svg")
