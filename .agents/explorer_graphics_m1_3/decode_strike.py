import struct

# Path to the existing strike_original.png
png_path = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/web/strike_original.png"

with open(png_path, "rb") as f:
    img_bytes = f.read()

# PNG header is 8 bytes.
# Next is IHDR chunk length (4 bytes) and then 'IHDR' chunk type (4 bytes).
# Total offset to IHDR chunk data = 16.
width, height = struct.unpack(">II", img_bytes[16:24])
print(f"File: {png_path}")
print(f"Dimensions: {width}x{height}")
