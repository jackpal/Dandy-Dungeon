#!/usr/bin/env python3
"""
test_leaks.py
Tests for resource leaks (specifically unclosed image files) in verify_graphics.py logic.
"""

import os
import sys
from PIL import Image

def check_file_leak():
    print("Checking for file descriptor leaks in Image.open...")
    
    # 1. Path to strike_original.png
    ref_path = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/strike_original.png"
    if not os.path.exists(ref_path):
        print(f"Error: {ref_path} does not exist. Run verify_graphics.py first.")
        return False
        
    # 2. Get initial open files
    # We can inspect /proc/self/fd on Linux
    fd_dir = "/proc/self/fd"
    initial_fds = set(os.listdir(fd_dir))
    
    # 3. Open the image
    ref_img = Image.open(ref_path)
    
    # 4. Check open files again
    post_open_fds = set(os.listdir(fd_dir))
    new_fds = post_open_fds - initial_fds
    
    leak_detected = False
    opened_file_path = None
    
    # Let's resolve the links in /proc/self/fd to see if the image path is there
    for fd in new_fds:
        try:
            link = os.readlink(os.path.join(fd_dir, fd))
            if "strike_original.png" in link:
                leak_detected = True
                opened_file_path = link
                print(f"Found open file descriptor for: {link}")
        except FileNotFoundError:
            pass
            
    if leak_detected:
        print("Verification: Image.open() keeps the file descriptor open.")
        
        # Now let's close the image and check if it gets closed
        ref_img.close()
        post_close_fds = set(os.listdir(fd_dir))
        
        # Resolve again
        closed_properly = True
        for fd in post_close_fds:
            try:
                link = os.readlink(os.path.join(fd_dir, fd))
                if "strike_original.png" in link:
                    closed_properly = False
            except FileNotFoundError:
                pass
                
        if closed_properly:
            print("Calling ref_img.close() successfully closed the file descriptor.")
        else:
            print("Error: Calling ref_img.close() did NOT close the file descriptor!")
            
        return True # We detected that it does leak if not closed
    else:
        print("No open file descriptor found for strike_original.png after Image.open().")
        # Note: some PIL versions load the image fully into memory and close it immediately,
        # but others (especially for larger files or lazy loading) keep it open.
        ref_img.close()
        return False

if __name__ == "__main__":
    check_file_leak()
