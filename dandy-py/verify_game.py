import os
import sys

# Force dummy video driver for headless run
os.environ["SDL_VIDEODRIVER"] = "dummy"

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

import pygame
import main
import constants

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


# Test 3: Player 2 Hot-Join Spawning & Heart bug check
print("\nStarting Test 3: Player 2 Hot-Join & Spawning validation...")

# Restore original Game.__init__
Game.__init__ = original_init

# Reset state
pygame.init()
frame_count = 0
quit_sent = False
joined_detected = False

# We will capture the game instance
captured_game = None
def mock_game_init_3(self):
    original_init(self)
    global captured_game
    captured_game = self

Game.__init__ = mock_game_init_3

# Mock keystate dictionary to prevent Pygame's large key constants IndexError
class MockKeystate:
    def __init__(self, pressed_keys=None):
        self.pressed_keys = pressed_keys or set()
    def __getitem__(self, key):
        return 1 if key in self.pressed_keys else 0

original_get_pressed = pygame.key.get_pressed

def mock_get_pressed():
    global frame_count
    pressed = set()
    if frame_count == 5:
        print("Simulating Player 2 pressing 'W' to join...")
        pressed.add(pygame.K_w)
    return MockKeystate(pressed)

pygame.key.get_pressed = mock_get_pressed

def mock_get_3():
    global frame_count, quit_sent, joined_detected
    frame_count += 1
    
    if captured_game:
        p1 = captured_game.players[0]
        p2 = captured_game.players[1]
        
        # HEART bug assertion check: dead_players() must be empty before P2 joins
        if p2.state == main.STATE_INACTIVE:
            dead = list(captured_game.dead_players())
            if len(dead) > 0:
                print(f"Error: dead_players() yielded inactive player: {dead[0].index}")
                sys.exit(1)
        
        if p2.state == main.STATE_ACTIVE:
            if not joined_detected:
                print("Player 2 joined successfully! (STATE_ACTIVE detected)")
                joined_detected = True
                
                # Check P2 spawning coordinates relative to UP stairs
                try:
                    up_x, up_y = captured_game.map.find(constants.UP)
                except Exception:
                    up_x, up_y = 2, 2
                
                print(f"UP stairs position: ({up_x}, {up_y})")
                print(f"Player 2 position: ({p2.x}, {p2.y})")
                
                if p2.x == up_x + 1 and p2.y == up_y:
                    print("Player 2 spawned exactly 1 tile East of UP stairs successfully!")
                else:
                    print(f"Error: Player 2 spawned at ({p2.x}, {p2.y}) instead of ({up_x + 1}, {up_y})!")
                    sys.exit(1)
                
                # Check if P2 is correctly registered on the map
                tile = captured_game.map.get(p2.x, p2.y)
                print(f"Tile at P2 position: {tile}")
                if tile == main.PLAYER + 1:
                    print("Player 2 sprite registered on map correctly.")
                else:
                    print(f"Error: Player 2 sprite NOT on map! Expected {main.PLAYER + 1}, got {tile}")
                    sys.exit(1)
                
    if frame_count >= 15 and not quit_sent:
        print("Sending QUIT event to exit Test 3")
        quit_sent = True
        return [pygame.event.Event(pygame.QUIT)]
    return []

pygame.event.get = mock_get_3

try:
    main.main()
    if joined_detected:
        print("Test 3 passed! Player 2 hot-join and spawning verified.")
    else:
        print("Test 3 failed: Player 2 did not join.")
        sys.exit(1)
except Exception as e:
    print(f"Test 3 failed with exception: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Graphics Architecture Validation (game_surface & scaling)
print("\nStarting Test 4: Graphics Architecture validation...")

# Reset state
pygame.init()

game = Game()

# Verify offscreen surface
assert hasattr(game, "game_surface"), "Game is missing \"game_surface\" attribute"
assert game.game_surface is not None, "game_surface is None"
assert game.game_surface.get_size() == (320, 240), f"game_surface size is {game.game_surface.get_size()}, expected (320, 240)"

# Verify font cache initialization
assert hasattr(game, "hud_fonts"), "Game is missing \"hud_fonts\" attribute"
assert isinstance(game.hud_fonts, dict), "hud_fonts is not a dictionary"
assert len(game.hud_fonts) == 0, "hud_fonts should be empty initially"

# Verify draw method works with screen
mock_screen = pygame.Surface((640, 560))
try:
    game.draw(mock_screen)
    print("game.draw() executed successfully on 640x560 surface.")
    # 560 height should trigger font size 16
    assert 16 in game.hud_fonts, "Font size 16 was not cached for 560px height"
    assert isinstance(game.hud_fonts[16], pygame.font.Font), "Cached item is not a pygame Font"
except Exception as e:
    print(f"game.draw() failed on 640x560 surface: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test resize scaling
mock_screen_resized = pygame.Surface((1280, 1120))
try:
    game.draw(mock_screen_resized)
    print("game.draw() executed successfully on 1280x1120 resized surface.")
    # 1120 height should trigger font size 32
    assert 32 in game.hud_fonts, "Font size 32 was not cached for 1120px height"
    assert isinstance(game.hud_fonts[32], pygame.font.Font), "Cached item is not a pygame Font"
    assert len(game.hud_fonts) == 2, f"Expected 2 cached fonts, got {len(game.hud_fonts)}"
except Exception as e:
    print(f"game.draw() failed on 1280x1120 resized surface: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Test 4 passed! Graphics architecture verified.")


# Test 5: Hardened Sleep Loop & Insignificant Events
print("\nStarting Test 5: Hardened Sleep Loop & Insignificant Events validation...")

# Reset state
pygame.init()
wait_calls = []
draw_count = 0
draw_checks = []

# Force sleep mode immediately by blocking ghosts
Game.__init__ = mock_game_init

# Mock Game.draw to check if it gets called during sleep
original_draw = Game.draw
def mock_game_draw(self, screen):
    global draw_count
    draw_count += 1
    original_draw(self, screen)
Game.draw = mock_game_draw

# List of events that pygame.event.wait() will return sequentially
mock_events_sequence = [
    # Insignificant: Mouse motion (should be blocked by OS, but if it gets here, it should be ignored by is_significant_event)
    pygame.event.Event(pygame.MOUSEMOTION),
    # Insignificant: Joystick motion with small value
    pygame.event.Event(pygame.JOYAXISMOTION, axis=0, value=0.10),
    # Insignificant: Joystick motion with negative small value
    pygame.event.Event(pygame.JOYAXISMOTION, axis=1, value=-0.05),
    # Significant: Joystick motion with large value -> Should wake up!
    pygame.event.Event(pygame.JOYAXISMOTION, axis=0, value=0.20),
]

event_index = 0

def mock_wait_5():
    global event_index, wait_calls, draw_count
    # Record whether draw was called BEFORE we return the NEXT event.
    draw_checks.append(draw_count)
    
    if event_index < len(mock_events_sequence):
        ev = mock_events_sequence[event_index]
        event_index += 1
        print(f"pygame.event.wait() returning simulated event: {ev}")
        wait_calls.append(ev)
        return ev
    else:
        # Fallback to QUIT to avoid infinite loop
        print("pygame.event.wait() fallback to QUIT")
        return pygame.event.Event(pygame.QUIT)

def mock_get_5():
    return []

def mock_get_pressed_clean():
    return MockKeystate()

pygame.event.get = mock_get_5
pygame.event.wait = mock_wait_5
pygame.key.get_pressed = mock_get_pressed_clean

try:
    main.main()
    
    print(f"Wait calls recorded: {len(wait_calls)}")
    print(f"Draw checks recorded: {draw_checks}")
    
    assert len(wait_calls) >= 4, f"Expected at least 4 wait calls, got {len(wait_calls)}"
    
    expected_draw_checks = [1, 1, 1, 1, 2]
    assert draw_checks[:5] == expected_draw_checks, f"Expected draw checks {expected_draw_checks}, got {draw_checks[:5]}"
    
    print("Test 5 passed! Hardened sleep loop verified.")
    
except Exception as e:
    print(f"Test 5 failed with exception: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    # Restore original Game.draw
    Game.draw = original_draw
    # Restore original Game.__init__
    Game.__init__ = original_init


print("\nAll verifications successful!")


