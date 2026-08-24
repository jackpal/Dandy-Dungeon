import sys
import os

# Add dandy-gb/tests to path so we can import dandy_env
sys.path.insert(0, "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests")

from dandy_env import DandyEnv

def run_diagnostic():
    print("Starting rotor diagnostics...")
    for run in range(5):
        print(f"\n--- Run {run} ---")
        env = DandyEnv()
        env.init()
        
        # Setup a clean map with player at 10,10
        custom_map = [env.TILE_SPACE] * env.MAP_SIZE
        custom_map[10 * 60 + 10] = env.TILE_PLAYER1
        env.dandy_map = custom_map
        env.set_player_position(0, 10, 10)
        env.set_player_joined(0, True)
        env.set_player_health(0, 100)
        
        # Place Monster 1 at (9, 10)
        m = env.dandy_map
        m[10 * 60 + 9] = env.TILE_MONSTER1
        env.dandy_map = m
        
        print("Initial monster_rotor:", env.monster_rotor)
        
        for step in range(1, 11):
            env.step([0, 0, 0, 0])
            p_hp = env.get_player_health(0)
            monster_tile = env.dandy_map[10 * 60 + 9]
            print(f"Step {step}: rotor={env.monster_rotor}, player_hp={p_hp}, tile_at_9_10={monster_tile}")
            
if __name__ == "__main__":
    run_diagnostic()
