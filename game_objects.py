import pygame
import random
import math

pygame.font.init()
POWERUP_FONT = pygame.font.Font(None, 20)

class Paddle:
    def __init__(self, screen_width, screen_height, color=(0, 255, 255)):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.original_width = 100
        self.height = 12
        self.speed = 8
        self.color = color

        self.width = self.original_width
        self.power_up_timers = {'grow': 0, 'laser': 0, 'glue': 0}
        self.has_laser = False
        self.has_glue = False

        self.rect = pygame.Rect(
            self.screen_width // 2 - self.width // 2,
            self.screen_height - 40,
            self.width,
            self.height
        )

    def reset(self):
        self.rect.x = self.screen_width // 2 - self.original_width // 2
        self.width = self.original_width
        self.rect.width = self.width
        self.has_laser = False
        self.has_glue = False
        for power_up in self.power_up_timers:
            self.power_up_timers[power_up] = 0

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > self.screen_width:
            self.rect.right = self.screen_width

        self._update_power_ups()

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=6)

    def activate_power_up(self, type):
        duration = 600
        if type == 'grow':
            if self.power_up_timers['grow'] <= 0:
                current_center = self.rect.centerx
                self.width = 150
                self.rect.width = self.width
                self.rect.centerx = current_center
            self.power_up_timers['grow'] = duration
        elif type == 'laser':
            self.has_laser = True
            self.power_up_timers['laser'] = duration
        elif type == 'glue':
            self.has_glue = True
            self.power_up_timers['glue'] = duration

    def _update_power_ups(self):
        if self.power_up_timers['grow'] > 0:
            self.power_up_timers['grow'] -= 1
            if self.power_up_timers['grow'] <= 0:
                current_center = self.rect.centerx
                self.width = self.original_width
                self.rect.width = self.width
                self.rect.centerx = current_center
        if self.power_up_timers['laser'] > 0:
            self.power_up_timers['laser'] -= 1
            if self.power_up_timers['laser'] <= 0:
                self.has_laser = False
        if self.power_up_timers['glue'] > 0:
            self.power_up_timers['glue'] -= 1
            if self.power_up_timers['glue'] <= 0:
                self.has_glue = False


class Ball:
    def __init__(self, screen_width, screen_height, color=(255, 255, 255)):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.radius = 10
        self.color = color
        self.rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)

        self.is_glued = False
        self.is_slowed = False
        self.slow_timer = 0
        self.base_speed = 6

        self.reset()

    def reset(self):
        self.rect.center = (self.screen_width // 2, self.screen_height // 2)
        self.speed_x = self.base_speed * random.choice((1, -1))
        self.speed_y = -self.base_speed
        self.is_glued = False
        self.is_slowed = False
        self.slow_timer = 0

    def update(self, paddle, launch_ball=False):
        collision_object = None

        if self.is_glued:
            self.rect.centerx = paddle.rect.centerx
            self.rect.bottom = paddle.rect.top
            if launch_ball:
                self.is_glued = False
                self.speed_x = self.base_speed * random.choice((1, -1))
                self.speed_y = -self.base_speed
            return 'playing', None

        if self.is_slowed:
            self.slow_timer -= 1
            if self.slow_timer <= 0:
                self.speed_x *= 2
                self.speed_y *= 2
                self.is_slowed = False

        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        if self.rect.top <= 0:
            self.speed_y *= -1
            collision_object = 'wall'
        if self.rect.left <= 0 or self.rect.right >= self.screen_width:
            self.speed_x *= -1
            collision_object = 'wall'

        if self.rect.colliderect(paddle.rect) and self.speed_y > 0:
            if paddle.has_glue:
                self.is_glued = True
            self.speed_y *= -1
            collision_object = 'paddle'

        if self.rect.top > self.screen_height:
            return 'lost', None

        return 'playing', collision_object

    def draw(self, screen):
        pygame.draw.ellipse(screen, self.color, self.rect)

    def activate_power_up(self, type):
        if type == 'slow' and not self.is_slowed:
            self.speed_x /= 2
            self.speed_y /= 2
            self.is_slowed = True
            self.slow_timer = 600


class Brick:
    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=4)


class PowerUp:
    PROPERTIES = {
        'grow':       {'color': (0, 191, 255),   'char': 'G', 'message': 'PADDLE GROW'},
        'laser':      {'color': (255, 69, 0),    'char': 'L', 'message': 'LASER CANNONS'},
        'glue':       {'color': (34, 139, 34),   'char': 'C', 'message': 'CATCH PADDLE'},
        'slow':       {'color': (255, 215, 0),   'char': 'S', 'message': 'SLOW BALL'},
        'shrink':     {'color': (148, 0, 211),   'char': 'H', 'message': 'PADDLE SHRINK'},
        'fast':       {'color': (255, 140, 0),   'char': 'F', 'message': 'SPEED UP'},
        'extra_life': {'color': (255, 255, 255), 'char': '+', 'message': 'EXTRA LIFE!'}
    }

    def __init__(self, x, y, type):
        self.width = 30
        self.height = 15
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.speed_y = 3
        self.type = type
        self.color = self.PROPERTIES[type]['color']
        self.char = self.PROPERTIES[type]['char']

    def update(self):
        self.rect.y += self.speed_y

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=5)
        font = pygame.font.Font(None, 24)
        char_surface = font.render(self.char, True, (0, 0, 0))
        char_rect = char_surface.get_rect(center=self.rect.center)
        screen.blit(char_surface, char_rect)


class Laser:
    def __init__(self, x, y, color=(255, 0, 0)):
        self.width = 4
        self.height = 15
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = color
        self.speed_y = -8

    def update(self):
        self.rect.y += self.speed_y

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)


class Particle:
    def __init__(self, x, y, color, min_size, max_size, min_speed, max_speed, gravity):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(min_size, max_size)
        self.gravity = gravity
        angle = random.uniform(0, 360)
        speed = random.uniform(min_speed, max_speed)
        self.vx = speed * math.cos(math.radians(angle))
        self.vy = speed * math.sin(math.radians(angle))

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.size -= 0.1

    def draw(self, screen):
        if self.size > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))


class Firework:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.x = random.randint(0, screen_width)
        self.y = screen_height
        self.vy = -random.uniform(8, 12)
        self.color = (255, 255, 255)
        self.exploded = False
        self.particles = []
        self.explosion_y = random.uniform(screen_height * 0.2, screen_height * 0.5)

    def update(self):
        if not self.exploded:
            self.y += self.vy
            if self.y <= self.explosion_y:
                self.exploded = True
                explosion_color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                for _ in range(50):
                    self.particles.append(Particle(self.x, self.y, explosion_color, 2, 4, 1, 4, 0.1))
        else:
            for particle in self.particles[:]:
                particle.update()
                if particle.size <= 0:
                    self.particles.remove(particle)

    def draw(self, screen):
        if not self.exploded:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 3)
        else:
            for particle in self.particles:
                particle.draw(screen)

    def is_dead(self):
        return self.exploded and not self.particles

