import pygame

# 1. Re-export all names for backward compatibility with verify_game.py and external clients
from constants import *
from media import *
from strike import *
from map import *
from entities import *
from controls import *
from game import Game

# Dynamically compile WINDOW_EVENTS from dir(pygame)
num_events = getattr(pygame, "NUMEVENTS", 65535)
WINDOW_EVENTS = [
    getattr(pygame, name)
    for name in dir(pygame)
    if name.startswith("WINDOW")
    and not name.startswith("WINDOWPOS")
    and isinstance(getattr(pygame, name), int)
    and 0 <= getattr(pygame, name) < num_events
]
if hasattr(pygame, "ACTIVEEVENT"):
    WINDOW_EVENTS.append(pygame.ACTIVEEVENT)


def is_significant_event(event):
    if event.type in (
        pygame.QUIT,
        pygame.KEYDOWN,
        pygame.KEYUP,
        pygame.VIDEORESIZE,
        pygame.VIDEOEXPOSE,
    ):
        return True

    if hasattr(pygame, "JOYAXISMOTION") and event.type == pygame.JOYAXISMOTION:
        return abs(event.value) > 0.15

    # All other joystick events (buttons, hats, device updates, etc.) are significant
    joy_types = []
    for name in (
        "JOYBUTTONDOWN",
        "JOYBUTTONUP",
        "JOYHATMOTION",
        "JOYBALLMOTION",
        "JOYDEVICEADDED",
        "JOYDEVICEREMOVED",
    ):
        if hasattr(pygame, name):
            joy_types.append(getattr(pygame, name))
    if event.type in joy_types:
        return True

    if event.type in WINDOW_EVENTS:
        return True

    return False


def main():
    # Initialize pygame
    pygame.init()

    # Layer 1: OS/SDL Event Whitelisting
    pygame.event.set_blocked(None)
    allowed_events = [
        pygame.QUIT,
        pygame.KEYDOWN,
        pygame.KEYUP,
        pygame.VIDEORESIZE,
        pygame.VIDEOEXPOSE,
    ]
    # Dynamically add all joystick events
    for name in (
        "JOYAXISMOTION",
        "JOYBALLMOTION",
        "JOYHATMOTION",
        "JOYBUTTONDOWN",
        "JOYBUTTONUP",
        "JOYDEVICEADDED",
        "JOYDEVICEREMOVED",
    ):
        if hasattr(pygame, name):
            allowed_events.append(getattr(pygame, name))
    allowed_events.extend(WINDOW_EVENTS)
    pygame.event.set_allowed(allowed_events)

    if pygame.mixer and not pygame.mixer.get_init():
        print("Warning, no sound")
        pygame.mixer = None

    # Set the display mode
    screen = pygame.display.set_mode((640, 560), pygame.RESIZABLE)

    pygame.display.set_caption("Dandy Dungeon")
    pygame.mouse.set_visible(0)

    game = Game()
    clock = pygame.time.Clock()
    sleeping = False

    while True:
        if sleeping:
            # Layer 3: Hardened Sleep Loop
            while True:
                event = pygame.event.wait()
                if is_significant_event(event):
                    sleeping = False
                    events = [event] + pygame.event.get()
                    break
        else:
            events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                return

        keystate = pygame.key.get_pressed()
        game.step(keystate)
        game.draw(screen)
        pygame.display.flip()

        if game.can_sleep(keystate):
            sleeping = True
        else:
            clock.tick(60)


if __name__ == "__main__":
    main()
