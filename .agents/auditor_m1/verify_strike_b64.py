import os
import re
import base64
import hashlib

JS_STRIKE_PATH = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js/strike.js"
REFERENCE_PNG_PATH = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/strike_original.png"

def main():
    print("Extracting base64 string from strike.js...")
    with open(JS_STRIKE_PATH, 'r') as f:
        content = f.read()

    # Find all double-quoted strings
    matches = re.findall(r'"([^"]*)"', content)
    base64_parts = []
    for m in matches:
        if m.startswith('data:image/png;base64,'):
            base64_parts.append(m.replace('data:image/png;base64,', ''))
        else:
            base64_parts.append(m)

    base64_str = "".join(base64_parts)
    # Remove any stray newlines or whitespaces
    base64_str = re.sub(r'\s+', '', base64_str)
    decoded_bytes = base64.b64decode(base64_str)

    print(f"Decoded bytes length: {len(decoded_bytes)}")
    decoded_hash = hashlib.sha256(decoded_bytes).hexdigest()
    print(f"Decoded bytes SHA-256: {decoded_hash}")

    if not os.path.exists(REFERENCE_PNG_PATH):
        print(f"Reference image {REFERENCE_PNG_PATH} does not exist!")
        return

    with open(REFERENCE_PNG_PATH, 'rb') as f:
        ref_bytes = f.read()

    print(f"Reference bytes length: {len(ref_bytes)}")
    ref_hash = hashlib.sha256(ref_bytes).hexdigest()
    print(f"Reference bytes SHA-256: {ref_hash}")

    if decoded_bytes == ref_bytes:
        print("MATCH: The decoded base64 bytes match strike_original.png byte-for-byte!")
    else:
        print("MISMATCH: The decoded base64 bytes DO NOT match strike_original.png!")

if __name__ == "__main__":
    main()
