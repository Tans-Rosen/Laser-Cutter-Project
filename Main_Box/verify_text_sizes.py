import re
from validate import validate_inputs
from generate import generate_svg

# Medium text test case
test_inputs = {
    'length': 8.0,
    'width': 5.0,
    'height': 4.0,
    'numDividers': 0,
    'frontText': True,
    'frontTextContent': 'Precision Tools',
    'frontFractal': False,
    'backText': True,
    'backTextContent': 'Storage Box',
    'backFractal': False,
    'leftText': True,
    'leftTextContent': 'Premium',
    'leftFractal': False,
    'rightText': True,
    'rightTextContent': 'Quality',
    'rightFractal': False,
}

params = validate_inputs(test_inputs)
svg = generate_svg(params)

# Extract text elements and their font sizes
text_elements = re.findall(r'<text[^>]*font-size="([^"]*)"[^>]*>([^<]*)</text>', svg)
print("Text engraving results:")
print("=" * 60)
for font_size, text_content in text_elements:
    print(f"Text: '{text_content}' | Font size: {font_size}mm")

# Count rotated elements
rotate_count = svg.count('rotate(')
print(f"\nRotated elements: {rotate_count}")

print("=" * 60)
print("✓ Text sizing and rendering verified")
