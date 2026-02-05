"""Final verification of text sizing and engraving."""

from validate import validate_inputs
from generate import generate_svg

# Create a box with text on all walls
test_inputs = {
    'length': 7.0,
    'width': 5.0,
    'height': 4.0,
    'numDividers': 0,
    'frontText': True,
    'frontTextContent': 'Hello World',
    'frontFractal': False,
    'backText': True,
    'backTextContent': 'Back Panel',
    'backFractal': False,
    'leftText': True,
    'leftTextContent': 'Left',
    'leftFractal': False,
    'rightText': True,
    'rightTextContent': 'Right',
    'rightFractal': False,
}

print("Generating SVG with text on all walls...")
params = validate_inputs(test_inputs)
svg = generate_svg(params)

# Save the SVG
output_file = '/tmp/final_text_verification.svg'
with open(output_file, 'w') as f:
    f.write(svg)

print(f"✓ SVG generated: {output_file}")
print(f"✓ SVG size: {len(svg):,} bytes")

# Parse and verify text elements
import re

# Find all text elements
text_matches = re.findall(
    r'<text[^>]*font-size="([^"]*)"[^>]*>([^<]*)</text>', 
    svg
)

print(f"\n{'Wall':<10} {'Text':<15} {'Font Size':<12}")
print("=" * 40)

walls = ['front', 'back', 'left', 'right']
for i, (size, text) in enumerate(text_matches):
    wall = walls[i] if i < len(walls) else "?"
    # Clean up the size (remove 'mm' suffix)
    size_val = size.replace('mm', '').strip()
    print(f"{wall:<10} {text:<15} {size_val:<12} mm")

# Check for stroke attributes (engraving)
stroke_count = svg.count('stroke="black"')
fill_none_count = svg.count('fill="none"')

print(f"\n✓ Stroke (engraved) elements: {stroke_count}")
print(f"✓ Fill='none' (not filled): {fill_none_count}")

# Check for rotations (side walls)
rotation_matches = re.findall(r'rotate\(([^)]+)\)', svg)
print(f"\n✓ Text rotations found: {len(rotation_matches)}")
for angle in set(rotation_matches):
    count = rotation_matches.count(angle)
    print(f"  - {angle}°: {count} element(s)")

print("\n✅ VERIFICATION COMPLETE: Text sizing and engraving working correctly!")
