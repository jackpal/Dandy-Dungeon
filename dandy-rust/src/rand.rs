// Pseudo-random number generator logic

pub struct LcgRng {
    state: u32,
}

impl LcgRng {
    pub fn new(seed: u32) -> Self {
        Self { state: seed }
    }

    pub fn next(&mut self) -> f64 {
        self.state = self.state.wrapping_mul(1103515245).wrapping_add(12345);
        let val = (self.state >> 16) & 0x7fff;
        (val as f64) / 32768.0
    }

    pub fn rand_byte(&mut self) -> u8 {
        self.state = self.state.wrapping_mul(1103515245).wrapping_add(12345);
        ((self.state >> 16) & 0xff) as u8
    }

    pub fn next_u32(&mut self) -> u32 {
        self.state = self.state.wrapping_mul(1103515245).wrapping_add(12345);
        self.state
    }

    pub fn state(&self) -> u32 {
        self.state
    }

    pub fn set_state(&mut self, state: u32) {
        self.state = state;
    }
}
