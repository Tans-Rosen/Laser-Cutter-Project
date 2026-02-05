"""Debug text sizing output."""

from validate import validate_inputs
from generate import generate_svg

test_inputs = {
    'length': 8.0,
    'width': 5.0,
    'height': 4.0,
    'numDividers': 0,
    'dividerPos1': None,
    'dividerPos2': None,
    'frontText': True,
    'frontTextContent': 'Hello',
    'frontFractal': False,
    'backText': False,
    'backTextContent': '',
    'backFractal': False,
    'leftText': False,
    'leftTextContent': '',
    'leftFractal': False,
    'rightText': False,
    'rightTextContent': '',
    'rightFractal': False,
}

params = validate_inputs(test_inputs)
print(f"Wall mode (front): {params['wall_mode'].get('front')}")
print(f"Wall text (front): {params['wall_text'].get('front')}")

svg = generate_svg(params)

# Save and check
with open('/tmp/simple_test.svg', 'w') as f:
    f.write(svg)

# Count text elements various ways
import re
count1 = svg.count('<text')
print(f"<text count: {count1}")

# Show a sample
if '<text' in svg:
    idx = svg.find('<text')
    print(f"Sample text element (first 300 chars):")
    print(svg[idx:idx+300])
else:
    print("No text elements found in SVG")
    
# Check for engraving groups
if '<g id="ENGRAVE' in svg:
    print("✓ ENGRAVE group found")
else:
    print("✗ No ENGRAVE group found")
    
# Check engraves list
print(f"\nSVG length: {len(svg)} chars")
