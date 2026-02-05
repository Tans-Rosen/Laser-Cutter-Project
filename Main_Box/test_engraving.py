#!/usr/bin/env python3
"""Test engraving features"""

import constants as C
from validate import validate_inputs
from generate import generate_svg

# Test 1: Text on left wall (should be rotated)
print("Test 1: Left wall text with 90° rotation")
inputs1 = {
    "length": 4.0, "width": 2.0, "height": 3.0,
    "numDividers": 0, "kerf_mm": C.KERF_MM_DEFAULT,
    "frontText": False, "frontFractal": False, "frontTextContent": "",
    "backText": False, "backFractal": False, "backTextContent": "",
    "leftText": True, "leftFractal": False, "leftTextContent": "SIDE",
    "rightText": False, "rightFractal": False, "rightTextContent": "",
}

try:
    params1 = validate_inputs(inputs1)
    svg1 = generate_svg(params1)
    if 'rotate(90)' in svg1:
        print("  ✓ Left wall text has 90° rotation")
    else:
        print("  ✗ Left wall text missing rotation")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 2: Text on right wall (should be rotated -90)
print("\nTest 2: Right wall text with -90° rotation")
inputs2 = {
    "length": 4.0, "width": 2.0, "height": 3.0,
    "numDividers": 0, "kerf_mm": C.KERF_MM_DEFAULT,
    "frontText": False, "frontFractal": False, "frontTextContent": "",
    "backText": False, "backFractal": False, "backTextContent": "",
    "leftText": False, "leftFractal": False, "leftTextContent": "",
    "rightText": True, "rightFractal": False, "rightTextContent": "SIDE2",
}

try:
    params2 = validate_inputs(inputs2)
    svg2 = generate_svg(params2)
    if 'rotate(-90)' in svg2:
        print("  ✓ Right wall text has -90° rotation")
    else:
        print("  ✗ Right wall text missing -90° rotation")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 3: Fractal on back wall
print("\nTest 3: Fractal generation")
inputs3 = {
    "length": 4.0, "width": 2.0, "height": 3.0,
    "numDividers": 0, "kerf_mm": C.KERF_MM_DEFAULT,
    "frontText": False, "frontFractal": False, "frontTextContent": "",
    "backText": False, "backFractal": True, "backTextContent": "",
    "leftText": False, "leftFractal": False, "leftTextContent": "",
    "rightText": False, "rightFractal": False, "rightTextContent": "",
}

try:
    params3 = validate_inputs(inputs3)
    svg3 = generate_svg(params3)
    path_count = svg3.count('<path')
    if path_count > 0:
        print(f"  ✓ Fractal generated with {path_count} paths")
    else:
        print("  ✗ No fractal paths found")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 4: Text is engraved (stroke, not fill)
print("\nTest 4: Text uses stroke (engraved)")
inputs4 = {
    "length": 4.0, "width": 2.0, "height": 3.0,
    "numDividers": 0, "kerf_mm": C.KERF_MM_DEFAULT,
    "frontText": True, "frontFractal": False, "frontTextContent": "Test",
    "backText": False, "backFractal": False, "backTextContent": "",
    "leftText": False, "leftFractal": False, "leftTextContent": "",
    "rightText": False, "rightFractal": False, "rightTextContent": "",
}

try:
    params4 = validate_inputs(inputs4)
    svg4 = generate_svg(params4)
    if 'fill="none"' in svg4 and 'stroke="black"' in svg4:
        print("  ✓ Text has fill=none and stroke=black (engraved)")
    else:
        print("  ✗ Text not properly engraved")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n" + "="*50)
print("All engraving tests complete!")
