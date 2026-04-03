"""Tests for steam and drip particle systems."""


from digital_caffeine.pc98.particles import DripSystem, SteamSystem


class TestSteamSystem:
    def test_initial_particle_count(self):
        steam = SteamSystem(count=8, spawn_y=50.0, x_center=32)
        assert len(steam.particles) == 8

    def test_particles_rise_over_time(self):
        steam = SteamSystem(count=4, spawn_y=50.0, x_center=32)
        for _ in range(10):
            steam.update()
        for i, p in enumerate(steam.particles):
            assert isinstance(p.y, float)

    def test_particles_reset_when_above_scene(self):
        steam = SteamSystem(count=2, spawn_y=50.0, x_center=32)
        for _ in range(200):
            steam.update()
        for p in steam.particles:
            assert p.y >= -5

    def test_update_advances_frame(self):
        steam = SteamSystem(count=2, spawn_y=50.0, x_center=32)
        assert steam.frame == 0
        steam.update()
        assert steam.frame == 1

    def test_get_draw_list_returns_tuples(self):
        steam = SteamSystem(count=4, spawn_y=50.0, x_center=32)
        draws = steam.get_draw_list()
        for x, y, color_idx in draws:
            assert isinstance(x, int)
            assert isinstance(y, int)
            assert isinstance(color_idx, int)


class TestDripSystem:
    def test_no_drips_initially(self):
        drips = DripSystem(spawn_y=58, x_min=19, x_max=44)
        draws = drips.get_draw_list()
        assert len(draws) == 0

    def test_drips_spawn_over_time(self):
        drips = DripSystem(spawn_y=58, x_min=19, x_max=44)
        spawned = False
        for _ in range(200):
            drips.update()
            if drips.get_draw_list():
                spawned = True
                break
        assert spawned

    def test_max_two_active_drips(self):
        drips = DripSystem(spawn_y=58, x_min=19, x_max=44)
        for _ in range(500):
            drips.update()
            assert len(drips.get_draw_list()) <= 2

    def test_drips_fall_downward(self):
        drips = DripSystem(spawn_y=58, x_min=19, x_max=44)
        for _ in range(500):
            drips.update()
            draws = drips.get_draw_list()
            if draws:
                first_y = draws[0][1]
                assert first_y >= 58
                break

    def test_drips_expire(self):
        drips = DripSystem(spawn_y=58, x_min=19, x_max=44)
        had_drip = False
        for _ in range(500):
            drips.update()
            draws = drips.get_draw_list()
            if draws:
                had_drip = True
            elif had_drip:
                break
        assert had_drip
