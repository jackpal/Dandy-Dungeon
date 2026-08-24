import base64
import re
import struct

with open('/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js/strike.js', 'r') as f:
    content = f.read()

# Extract all double-quoted strings
matches = re.findall(r'"([^"]*)"', content)
base64_parts = []
for m in matches:
    if m.startswith('data:image/png;base64,'):
        base64_parts.append(m.replace('data:image/png;base64,', ''))
    else:
        base64_parts.append(m)

base64_str = "".join(base64_parts)
img_data = base64.b64decode(base64_str)

# Parse PNG palette or image data to find unique colors.
# Since we don't have PIL, we can write the PNG to a temporary file
# and read it using standard library if possible, or we can just write the bytes
# to strike_original_test.png and inspect it.
# Wait, we can write a simple PNG parser in Python to read the PLTE chunk if it has one!
# Let's do that or just write the file to disk and look at it.
# Actually, let's write it to disk first in our folder.
with open('/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_m1_1/strike_original_test.png', 'wb') as out_f:
    out_f.write(img_data)

# Let's read the PLTE chunk if present
offset = 8 # Skip signature
while offset < len(img_data):
    length, chunk_type = struct.unpack('>I4s', img_data[offset:offset+8])
    chunk_type = chunk_type.decode('ascii')
    if chunk_type == 'PLTE':
        palette_data = img_data[offset+8 : offset+8+length]
        colors = [palette_data[i:i+3] for i in range(0, len(palette_data), 3)]
        print("Palette colors:")
        for idx, col in enumerate(colors):
            print(f"Color {idx}: #{col.hex()}")
        break
    elif chunk_type == 'IEND':
        break
    offset += 12 + length # length (4) + type (4) + data (length) + crc (4)
else:
    print("No PLTE chunk found (image is not indexed/palette-based).")
