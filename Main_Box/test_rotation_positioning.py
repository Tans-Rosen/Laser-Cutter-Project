"""Test text positioning with rotation."""

from validate import validate_inputs
from generate import generate_svg

# Create a box with text on all walls, especially test the side walls
test_inputs = {
    'length': 8.0,
    'width': 5.0,
    'height': 4.0,
    'numDividers': 0,
    'frontText': True,
    'frontTextContent': 'Front',
    'frontFractal': False,
    'backText': True,
    'backTextContent': 'Back',
    'backFractal': False,
    'leftText': True,
    'leftTextContent': 'Incline',  # Longer text to test overflow
    'leftFractal': False,
    'rightText': True,
    'rightTextContent': 'Right',
    'rightFractal': False,
}

print("Generating test SVG with text on all walls...")
params = validate_inputs(test_inputs)
svg = generate_svg(params)

# Save
with open('/tmp/test_rotation.svg', 'w') as f:
    f.write(svg)

print("✓ SVG generated: /tmp/test_rotation.svg")

# Check text positions and rotations
import re

text_elements = re.findall(
    r'<g transform="translate\(([^,]+),([^)]+)\) rotate\(([^)]+)\)">.*?<text[^>]*>([^<]+)</text>',
    svg,
    re.DOTALL
)

print(f"\nRotated text elements: {len(text_elements)}")
for x, y, angle, text in text_elements:
    print(f"  {text:15} at ({float(x):.1f}, {float(y):.1f}) rotated {angle}°")

# Non-rotated text - simpler approach
non_rotated_count = svg.count('<text x=')
print(f"\nNon-rotated text elements: {non_rotated_count}")

print("\n✅ Test complete - Check /tmp/test_rotation.svg in browser")
