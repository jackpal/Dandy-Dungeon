import base64
import os
import re

# Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
strike_js_path = os.path.join(current_dir, "../../dandy-js/strike.js")
output_png_path = os.path.join(current_dir, "../assets/strike_original.png")

# Create assets directory if it doesn't exist
os.makedirs(os.path.dirname(output_png_path), exist_ok=True)

print(f"Reading base64 sprite data from {strike_js_path}...")

with open(strike_js_path, "r") as f:
    content = f.read()

# Find the base64 string
# It looks like: strike.src = "data:image/png;base64,"+ "iVBORw0..."
# We want to extract all the quoted strings after "data:image/png;base64,"
match = re.search(r'data:image/png;base64,\"\+\s*(.*);', content, re.DOTALL)
if not match:
    # Try another regex if formatting differs
    match = re.search(r'\"data:image/png;base64,\"\s*\+\s*(.*);', content, re.DOTALL)

if match:
    base64_part = match.group(1)
    # Clean up quotes, pluses, newlines, and spaces
    base64_str = "".join(re.findall(r'\"([^\"]*)\"', base64_part))
else:
    # Fallback: just find the long base64-looking block
    # strike.src = "data:image/png;base64," + ...
    # Let's extract everything between the first double quote after base64, and the ending semicolon
    base64_start = content.find("data:image/png;base64,")
    if base64_start != -1:
        base64_data_str = content[base64_start:]
        # Extract all quoted substrings
        quotes = re.findall(r'"([^"]*)"', base64_data_str)
        # The first quote has "data:image/png;base64,", the rest are the base64 chunks
        base64_str = "".join(quotes[1:])
    else:
        raise ValueError("Could not find base64 image data in strike.js")

print(f"Decoding base64 string (length: {len(base64_str)})...")
image_data = base64.b64decode(base64_str)

print(f"Saving original spritesheet to {output_png_path}...")
with open(output_png_path, "wb") as f:
    f.write(image_data)

print("Extraction complete!")
