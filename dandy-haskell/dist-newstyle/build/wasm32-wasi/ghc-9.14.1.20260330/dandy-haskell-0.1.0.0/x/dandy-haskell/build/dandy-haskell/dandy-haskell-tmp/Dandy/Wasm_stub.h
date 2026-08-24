#include <HsFFI.h>
#if defined(__cplusplus)
extern "C" {
#endif
extern HsStablePtr hs_init_game(void);
extern void hs_game_tick(HsStablePtr a1);
extern void hs_set_action(HsStablePtr a1, HsInt a2, HsInt a3, HsBool a4);
extern HsBool hs_can_sleep(HsStablePtr a1);
extern HsPtr hs_get_framebuffer_ptr(HsStablePtr a1);
extern HsInt hs_get_framebuffer_size(HsStablePtr a1);
extern HsPtr hs_get_stats_ptr(HsStablePtr a1);
extern HsInt hs_get_stats_len(HsStablePtr a1);
extern HsInt hs_get_level(HsStablePtr a1);
extern void hs_free_game(HsStablePtr a1);
#if defined(__cplusplus)
}
#endif

