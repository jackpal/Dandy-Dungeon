/* Generated automatically from dandy-js/levels.js. Do not edit. */
#ifndef DANDY_LEVELS_H
#define DANDY_LEVELS_H

#include <stdint.h>

#define DANDY_LEVEL_WIDTH  60
#define DANDY_LEVEL_HEIGHT 30
#define DANDY_NUM_LEVELS   26

/* Extern declaration of pointer array to all compressed levels in ROM */
extern const uint8_t* const dandy_levels[DANDY_NUM_LEVELS];
extern const uint16_t dandy_level_sizes[DANDY_NUM_LEVELS];

#endif /* DANDY_LEVELS_H */