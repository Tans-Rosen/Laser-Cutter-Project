"""Test text box scaling with various text lengths."""

from validate import validate_inputs
from generate import generate_svg
import re

# Test different text lengths to show how font size adapts
test_cases = [
    ('Hi', 'Short 2-char'),
    ('Box', 'Short 3-char'),
    ('Pencil', 'Medium 6-char'),
    ('Incline', 'Medium 7-char'),
    ('Storage', 'Medium 7-char'),
    ('Precision', 'Longer 9-char'),
    ('Engineering', 'Longer 11-char'),
    ('Professional', 'Very long 12-char'),
]

print("=" * 80)
print("TEXT BOX SCALING TEST - 6x4x3 inch box")
print("=" * 80)
print(f"\n{'Text':<20} {'Description':<20} {'Front Font':<12} {'Left Font':<12}")
print("-" * 80)

for text, desc in test_cases:
    inputs = {
        'length': 6.0, 'width': 4.0, 'height': 3.0, 'numDividers': 0,
        'frontText': True, 'frontTextContent': text, 'frontFractal': False,
        'backText': False, 'backTextContent': '', 'backFractal': False,
        'leftText': True, 'leftTextContent': text, 'leftFractal': False,
        'rightText': False, 'rightTextContent': '', 'rightFractal': False,
    }
    
    try:
        params = validate_inputs(inputs)
        svg = generate_svg(params)
        
        # Extract font sizes
        sizes = re.findall(r'font-size="([^"]+)"', svg)
        front_size = sizes[0].replace('mm', '').strip() if len(sizes) > 0 else 'N/A'
        left_size = sizes[1].replace('mm', '').strip() if len(sizes) > 1 else 'N/A'
        
        print(f"{text:<20} {desc:<20} {front_size:<12} {left_size:<12}")
        
    except Exception as e:
        print(f"{text:<20} {desc:<20} ERROR: {e}")

print("\n" + "=" * 80)
print("OBSERVATIONS:")
print("  - Text box scales proportionally with wall size (75% width, 50% height)")
print("  - Font size decreases iteratively until text fits in the box")
print("  - Rotated text (left wall) has different box dimensions than front wall")
print("  - Longer text gets smaller font size to fit in the same box")
print("=" * 80)
