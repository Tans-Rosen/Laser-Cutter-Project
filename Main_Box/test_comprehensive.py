#!/usr/bin/env python3
"""Comprehensive engraving test"""

import constants as C
from validate import validate_inputs
from generate import generate_svg, build_pieces

inputs = {
    "length": 5.0, "width": 3.0, "height": 4.0,
    "numDividers": 1,
    "dividerPos1": 2.5,
    "kerf_mm": C.KERF_MM_DEFAULT,
    "frontText": True, "frontFractal": False, "frontTextContent": "FRONT",
    "backText": False, "backFractal": True, "backTextContent": "",
    "leftText": True, "leftFractal": False, "leftTextContent": "LEFT",
    "rightText": False, "rightFractal": True, "rightTextContent": "",
}

try:
    print("Generating complex design...")
    params = validate_inputs(inputs)
    pieces = build_pieces(params)
    print(f"  {len(pieces)} pieces created")
    
    svg = generate_svg(params)
    
    checks = [
        ("Text on front", "FRONT" in svg),
        ("Text on left (rotated 90)", "rotate(90)" in svg),
        ("Fractal on back", svg.count('<path') >= 40),
        ("Fractal on right", svg.count('<path') >= 80),
        ("All engraved (black stroke)", svg.count('stroke="black"') >= 2),
        ("Text not filled", svg.count('fill="none"') >= 2),
    ]
    
    for check_name, result in checks:
        print(f"  {'✓' if result else '✗'} {check_name}")
    
    with open("output.svg", "w") as f:
        f.write(svg)
    print("\n✓ Wrote output.svg")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
