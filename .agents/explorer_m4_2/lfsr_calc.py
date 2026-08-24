def simulate_lfsr(steps=20):
    rand_seed = 0xACE1
    results = []
    for i in range(steps):
        lsb = rand_seed & 1
        rand_seed >>= 1
        if lsb:
            rand_seed ^= 0xB400
        
        spawn = (rand_seed & 7) < 4
        spawn_dir = (rand_seed & 3) * 2
        
        results.append({
            "step": i + 1,
            "seed_hex": hex(rand_seed),
            "spawn": spawn,
            "spawn_dir": spawn_dir
        })
    return results

if __name__ == "__main__":
    seq = simulate_lfsr(30)
    print(f"{'Index':<6} | {'Seed':<8} | {'Spawn?':<6} | {'Dir':<4}")
    print("-" * 36)
    for s in seq:
        print(f"{s['step']:<6} | {s['seed_hex']:<8} | {str(s['spawn']):<6} | {s['spawn_dir']:<4}")
