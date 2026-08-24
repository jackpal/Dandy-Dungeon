#!/usr/bin/env python3
import sys
import os
from PIL import Image

# Add the tools directory to the path so we can import verify_graphics
sys.path.append("/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools")
import verify_graphics

def test_resource_leaks():
    print("Checking for unclosed file descriptors in verify_graphics...")
    
    # Let's count open file descriptors before
    fds_before = set(os.listdir('/proc/self/fd'))
    
    # Run the main function
    # We want to run it on the actual repository files to see if it works cleanly.
    # verify_graphics.main() will write to dandy-gb/teamwork_graphics/
    verify_graphics.main()
    
    # Let's count open file descriptors after
    fds_after = set(os.listdir('/proc/self/fd'))
    
    leaked_fds = fds_after - fds_before
    print(f"File descriptors before: {len(fds_before)}, after: {len(fds_after)}")
    
    # Note: Some file descriptors might be opened by Python/Pillow internals (like shared libraries or font caches).
    # Let's inspect the targets of any new file descriptors in /proc/self/fd.
    leaked_files = []
    for fd in leaked_fds:
        try:
            target = os.readlink(f'/proc/self/fd/{fd}')
            leaked_files.append(target)
        except OSError:
            pass
            
    print(f"Newly opened paths: {leaked_files}")
    
    # Specifically check if strike_original.png is still open
    ref_image_open = False
    for path in leaked_files:
        if "strike_original.png" in path:
            ref_image_open = True
            
    if ref_image_open:
        print("FAIL: Reference image 'strike_original.png' file descriptor was left open/unclosed!")
        return False
        
    print("PASS: No significant file descriptor leaks detected for input/output graphics files.")
    return True

if __name__ == "__main__":
    success = test_resource_leaks()
    sys.exit(0 if success else 1)
