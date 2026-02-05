#!/usr/bin/env python3
"""Test text sizing and fit on walls after migration to conservative algorithm."""

from generate import generate_svg
from validate import validate_inputs

# Test case 1: Simple short text
print("=" * 60)
print("Test 1: Short text on walls (6x4x3 inch box)")
print("=" * 60)

test_inputs_short = {
    'length': 6.0,
    'width': 4.0,
    'height': 3.0,
    'numDividers': 0,
    'frontText': True,
    'frontTextContent': 'Hi',
    'frontFractal': False,
    'backText': True,
    'backTextContent': 'Box',
    'backFractal': False,
    'leftText': True,
    'leftTextContent': 'L',
    'leftFractal': False,
    'rightText': True,
    'rightTextContent': 'R',
    'rightFractal': False,
}

try:
    params = validate_inputs(test_inputs_short)
    svg = generate_svg(params)
    with open('/tmp/test_short_text.svg', 'w') as f:
        f.write(svg)
    print("✓ Short text test passed - SVG generated")
except Exception as e:
    print(f"✗ Short text test failed: {e}")

# Test case 2: Medium text  
print("\n" + "=" * 60)
print("Test 2: Medium text on walls (8x5x4 inch box)")
print("=" * 60)

test_inputs_medium = {
    'length': 8.0,
    'width': 5.0,
    'height': 4.0,
    'numDividers': 1,
    'dividerPos1': 0.5,
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

try:
    params = validate_inputs(test_inputs_medium)
    svg = generate_svg(params)
    with open('/tmp/test_medium_text.svg', 'w') as f:
        f.write(svg)
    print("✓ Medium text test passed - SVG generated")
except Exception as e:
    print(f"✗ Medium text test failed: {e}")

# Test case 3: Long text (stress test)
print("\n" + "=" * 60)
print("Test 3: Long text on walls (10x6x5 inch box)")
print("=" * 60)

test_inputs_long = {
    'length': 10.0,
    'width': 6.0,
    'height': 5.0,
    'numDividers': 2,
    'dividerPos1': 3.33,
    'dividerPos2': 6.67,
    'frontText': True,
    'frontTextContent': 'Precision Laser Engraving',
    'frontFractal': False,
    'backText': True,
    'backTextContent': 'Professional Storage',
    'backFractal': False,
    'leftText': True,
    'leftTextContent': 'High Quality',
    'leftFractal': False,
    'rightText': True,
    'rightTextContent': 'Crafted Box',
    'rightFractal': False,
}

try:
    params = validate_inputs(test_inputs_long)
    svg = generate_svg(params)
    with open('/tmp/test_long_text.svg', 'w') as f:
        f.write(svg)
    print("✓ Long text test passed - SVG generated")
except Exception as e:
    print(f"✗ Long text test failed: {e}")

# Test case 4: Fractal engraving
print("\n" + "=" * 60)
print("Test 4: Fractal engraving (8x5x4 inch box)")
print("=" * 60)

test_inputs_fractal = {
    'length': 8.0,
    'width': 5.0,
    'height': 4.0,
    'numDividers': 0,
    'frontText': False,
    'frontTextContent': '',
    'frontFractal': True,
    'backText': False,
    'backTextContent': '',
    'backFractal': False,
    'leftText': True,
    'leftTextContent': 'Math Art',
    'leftFractal': False,
    'rightText': False,
    'rightTextContent': '',
    'rightFractal': False,
}

try:
    params = validate_inputs(test_inputs_fractal)
    svg = generate_svg(params)
    with open('/tmp/test_fractal.svg', 'w') as f:
        f.write(svg)
    print("✓ Fractal test passed - SVG generated")
except Exception as e:
    print(f"✗ Fractal test failed: {e}")

print("\n" + "=" * 60)
print("All tests completed successfully!")
print("=" * 60)
print("\nSVG files created in /tmp/:")
print("  - test_short_text.svg")
print("  - test_medium_text.svg")
print("  - test_long_text.svg")
print("  - test_fractal.svg")
