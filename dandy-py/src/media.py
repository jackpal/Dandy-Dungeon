from pathlib import Path
import pygame

MEDIA_DIR = (Path(__file__).parent / "../Media").resolve()


def get_media_path(path: str) -> Path:
    return MEDIA_DIR / path


def load_image(file: str) -> pygame.Surface:
    "loads an image, prepares it for play"
    path = get_media_path(file)
    try:
        surface = pygame.image.load(path)
    except pygame.error:
        raise SystemExit(f'Could not load image "{path}" {pygame.get_error()}')
    return surface
