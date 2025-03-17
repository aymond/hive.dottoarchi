#!/usr/bin/env python3
import os
try:
    import cairosvg
    import PIL
    from PIL import Image
except ImportError:
    print("Required packages missing. Installing...")
    os.system("pip install cairosvg pillow")
    import cairosvg
    from PIL import Image

# Define paths
svg_path = "dot2archimate/web/static/img/favicon.svg"
png_path_32 = "dot2archimate/web/static/img/favicon-32.png"
png_path_16 = "dot2archimate/web/static/img/favicon-16.png"
ico_path = "dot2archimate/web/static/img/favicon.ico"
favicon_path = "dot2archimate/web/static/favicon.ico"

# Convert SVG to PNG (32x32)
print(f"Converting {svg_path} to PNG (32x32)...")
cairosvg.svg2png(url=svg_path, write_to=png_path_32, output_width=32, output_height=32)

# Convert SVG to PNG (16x16)
print(f"Converting {svg_path} to PNG (16x16)...")
cairosvg.svg2png(url=svg_path, write_to=png_path_16, output_width=16, output_height=16)

# Convert PNG to ICO (using both sizes)
print(f"Converting PNG files to ICO...")
img_32 = Image.open(png_path_32)
img_16 = Image.open(png_path_16)
img_32.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32)])

# Copy to favicon.ico in static directory
import shutil
print(f"Copying {ico_path} to {favicon_path}...")
shutil.copy(ico_path, favicon_path)

print("Favicon generation complete!") 