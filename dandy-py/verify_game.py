import os
import sys

# Force dummy video driver for headless run
os.environ["SDL_VIDEODRIVER"] = "dummy"

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

import pygame
import main

# Test 1: Normal Run (should not sleep immediately because Level A has active ghosts)
frame_count = 0
max_frames = 10
quit_sent = False

def mock_get_1():
    global frame_count, quit_sent
    frame_count += 1
    if frame_count >= max_frames and not quit_sent:
        print("Sending QUIT event to exit Test 1")
        quit_sent = True
        return [pygame.event.Event(pygame.QUIT)]
    return []

pygame.event.get = mock_get_1

print("Starting Test 1: Normal active loop...")
try:
    main.main()
    print("Test 1 passed!")
except Exception as e:
    print(f"Test 1 failed: {e}")
    sys.exit(1)


# Test 2: Sleep Mode Run (we force ghosts to be blocked, should sleep immediately)
print("\nStarting Test 2: Sleep mode validation...")

# Reset state
pygame.init() # re-init just in case
frame_count = 0
quit_sent = False
wait_called = False

# We monkeypatch Game.is_ghost_blocked to always return True
# This should satisfy can_sleep immediately
from main import Game
original_init = Game.__init__
def mock_game_init(self):
    original_init(self)
    # Force is_ghost_blocked to True
    self.is_ghost_blocked = lambda x, y: True

Game.__init__ = mock_game_init

def mock_get_2():
    # In sleep mode, event.get might be called after waking up.
    # We don't expect it to be called in active loop if we sleep immediately.
    # But if we wake up, we will send QUIT.
    return []

def mock_wait():
    global wait_called
    print("pygame.event.wait() called successfully! (Game went to sleep)")
    wait_called = True
    # Send QUIT to exit the game
    return pygame.event.Event(pygame.QUIT)

pygame.event.get = mock_get_2
pygame.event.wait = mock_wait

try:
    main.main()
    if wait_called:
        print("Test 2 passed! Sleep mode verified.")
    else:
        print("Test 2 failed: Game did not enter sleep mode.")
        sys.exit(1)
except Exception as e:
    print(f"Test 2 failed with exception: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nAll verifications successful!")
