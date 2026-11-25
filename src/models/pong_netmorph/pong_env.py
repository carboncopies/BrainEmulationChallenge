"""pong_env.py: minimal deterministic Pong, pure Python (no NES import).

Field is the unit square [0,1] x [0,1], y increasing UPWARD. The ball bounces
off the top, bottom and left walls. The paddle sits at the right edge (x=1)
and moves vertically. When the ball reaches x>=1 the step reports a hit
(|ball_y - paddle_y| <= paddle_h/2) or a miss, and the ball is reset.
"""
import random


class PongEnv:
    def __init__(self, seed=0, paddle_h=0.25, paddle_speed=0.08,
                 vx_range=(0.04, 0.06), vy_max=0.05, start_x=0.2):
        self.rng = random.Random(seed)
        self.h = paddle_h
        self.speed = paddle_speed
        self.vx_range = vx_range
        self.vy_max = vy_max
        self.start_x = start_x
        self.hits = 0
        self.misses = 0
        self.paddle_y = 0.5
        self._reset_ball()

    def _reset_ball(self):
        self.x = self.start_x
        self.y = self.rng.uniform(0.05, 0.95)
        self.vx = self.rng.uniform(*self.vx_range)
        self.vy = self.rng.uniform(-self.vy_max, self.vy_max)

    @staticmethod
    def _bin(v, n):
        return min(n - 1, max(0, int(v * n)))

    def ball_bin(self, n):
        return self._bin(self.y, n)

    def paddle_bin(self, n):
        return self._bin(self.paddle_y, n)

    def step(self, action):
        """action in {-1 (down), 0, +1 (up)}. Returns 'hit', 'miss' or None."""
        assert action in (-1, 0, 1)
        half = self.h / 2
        self.paddle_y = min(1 - half, max(half, self.paddle_y + action * self.speed))
        self.x += self.vx
        self.y += self.vy
        if self.y < 0:
            self.y, self.vy = -self.y, -self.vy
        elif self.y > 1:
            self.y, self.vy = 2 - self.y, -self.vy
        if self.x < 0:
            self.x, self.vx = -self.x, -self.vx
        if self.x >= 1:
            result = 'hit' if abs(self.y - self.paddle_y) <= half else 'miss'
            if result == 'hit':
                self.hits += 1
            else:
                self.misses += 1
            self._reset_ball()
            return result
        return None

    def hit_rate(self):
        t = self.hits + self.misses
        return self.hits / t if t else float('nan')


def random_policy(env, rng):
    return rng.choice((-1, 0, 1))


def oracle_policy(env, rng=None):
    d = env.y - env.paddle_y
    if abs(d) <= env.speed / 2:
        return 0
    return 1 if d > 0 else -1


def run_policy(policy, ticks, seed):
    env = PongEnv(seed)
    rng = random.Random(seed + 1)
    for _ in range(ticks):
        env.step(policy(env, rng))
    return env
