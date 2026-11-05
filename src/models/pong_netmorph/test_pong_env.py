import random
from pong_env import PongEnv, random_policy, oracle_policy, run_policy


def trace(seed, n=300):
    env = PongEnv(seed)
    rng = random.Random(5)
    out = []
    for _ in range(n):
        r = env.step(rng.choice((-1, 0, 1)))
        out.append((round(env.x, 9), round(env.y, 9), round(env.paddle_y, 9), r))
    return out


def test_determinism():
    assert trace(3) == trace(3)
    assert trace(3) != trace(4)


def test_wall_bounces():
    env = PongEnv(0)
    env.x, env.y, env.vx, env.vy = 0.5, 0.98, 0.0, 0.05
    env.step(0)
    assert env.vy < 0 and 0 <= env.y <= 1
    env.x, env.y, env.vx, env.vy = 0.5, 0.02, 0.0, -0.05
    env.step(0)
    assert env.vy > 0 and 0 <= env.y <= 1
    env.x, env.y, env.vx, env.vy = 0.02, 0.5, -0.05, 0.0
    env.step(0)
    assert env.vx > 0 and env.x >= 0


def test_hit_miss_accounting():
    env = PongEnv(0)
    env.paddle_y = 0.5
    env.x, env.y, env.vx, env.vy = 0.98, 0.5, 0.05, 0.0
    assert env.step(0) == 'hit' and env.hits == 1 and env.misses == 0
    env.paddle_y = 0.5
    env.x, env.y, env.vx, env.vy = 0.98, 0.9, 0.05, 0.0
    assert env.step(0) == 'miss' and env.hits == 1 and env.misses == 1
    assert env.x < 1  # ball reset


def test_bins():
    env = PongEnv(0)
    env.y = 0.0; assert env.ball_bin(8) == 0
    env.y = 0.999; assert env.ball_bin(8) == 7
    env.paddle_y = 0.5; assert env.paddle_bin(8) == 4


def test_oracle_high_random_low():
    o = run_policy(oracle_policy, 3000, 1)
    r = run_policy(random_policy, 3000, 1)
    assert o.hits + o.misses > 50
    assert o.hit_rate() > 0.9
    assert r.hit_rate() < 0.5
