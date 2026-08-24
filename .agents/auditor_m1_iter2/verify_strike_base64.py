import re
import base64
import sys
import os

def main():
    strike_js_path = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js/strike.js"
    strike_png_path = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/strike_original.png"

    if not os.path.exists(strike_js_path):
        print(f"Error: {strike_js_path} does not exist", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(strike_png_path):
        print(f"Error: {strike_png_path} does not exist", file=sys.stderr)
        sys.exit(1)

    with open(strike_js_path, "r") as f:
        content = f.read()

    # Find all string literals in the strike.src assignment
    # e.g., strike.src = "data:image/png;base64,"+
    # "..." +
    # "..."
    # Let's extract everything inside the double quotes.
    matches = re.findall(r'"([^"]*)"', content)
    if not matches:
        print("Error: No double-quoted strings found in strike.js", file=sys.stderr)
        sys.exit(1)

    # Reconstruct the full string
    full_str = "".join(matches)
    prefix = "data:image/png;base64,"
    if not full_str.startswith(prefix):
        print(f"Error: Reconstructed string does not start with {prefix}", file=sys.stderr)
        sys.exit(1)

    b64_data = full_str[len(prefix):]
    try:
        decoded_bytes = base64.b64decode(b64_data)
    except Exception as e:
        print(f"Error decoding base64: {e}", file=sys.stderr)
        sys.exit(1)

    with open(strike_png_path, "rb") as f:
        original_bytes = f.read()

    print(f"Decoded base64 length: {len(decoded_bytes)} bytes")
    print(f"Original PNG length: {len(original_bytes)} bytes")

    if decoded_bytes == original_bytes:
        print("SUCCESS: The decoded base64 string matches strike_original.png byte-for-byte!")
        sys.exit(0)
    else:
        print("FAILURE: The decoded base64 string does NOT match strike_original.png!")
        # Print differences if any
        min_len = min(len(decoded_bytes), len(original_bytes))
        for i in range(min_len):
            if decoded_bytes[i] != original_bytes[i]:
                print(f"First mismatch at byte {i}: decoded={decoded_bytes[i]}, original={original_bytes[i]}")
                break
        sys.exit(1)

if __name__ == "__main__":
    main()
