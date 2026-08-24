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
print(f"Total base64 length: {len(base64_str)}")
print(f"Ends with: {base64_str[-20:]}")

img_data = base64.b64decode(base64_str)
width, height = struct.unpack('>II', img_data[16:24])
print(f"PNG Dimensions: {width}x{height}")
