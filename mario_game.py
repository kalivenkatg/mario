import pygame
import sys

pygame.init()

WIDTH, HEIGHT = 480, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("trying to make a mario game!")
clock = pygame.time.Clock()
FPS = 60

# ── Colors ──────────────────────────────────────────────
SKY        = (133, 210, 245)
GROUND_COL = (100, 200, 60)
DIRT_COL   = (139, 100, 60)
BROWN      = (160,  82,  45)
RED        = (220,  30,  30)
YELLOW     = (240, 220,   0)
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
DARK_GRAY  = (100, 100, 100)
BTN_COL    = (200, 200, 200)
BTN_HOVER  = (160, 160, 160)

GROUND_Y   = HEIGHT - 60
GROUND_H   = 20
DIRT_H     = 40

font_big   = pygame.font.SysFont("Arial", 48, bold=True)
font_med   = pygame.font.SysFont("Arial", 28, bold=True)
font_small = pygame.font.SysFont("Arial", 20)
font_tiny  = pygame.font.SysFont("Arial", 16)

MARIO_W = 32
MARIO_H = 50

# ── Draw pixel Mario ────────────────────────────────────
def draw_mario(surf, cx, cy):
    x = cx - 16
    y = cy - 24
    pygame.draw.rect(surf, (200, 30, 30),   (x+4,  y,    24, 6))
    pygame.draw.rect(surf, (200, 30, 30),   (x+2,  y+6,  28, 6))
    pygame.draw.rect(surf, (255,200,140),   (x+4,  y+12, 24,10))
    pygame.draw.rect(surf, BLACK,           (x+8,  y+14,  4, 4))
    pygame.draw.rect(surf, BLACK,           (x+20, y+14,  4, 4))
    pygame.draw.rect(surf, (100, 60, 20),   (x+6,  y+20, 20, 3))
    pygame.draw.rect(surf, (30,  80,180),   (x+4,  y+22, 24,14))
    pygame.draw.rect(surf, YELLOW,          (x+12, y+24,  4, 4))
    pygame.draw.rect(surf, YELLOW,          (x+20, y+24,  4, 4))
    pygame.draw.rect(surf, (200, 30, 30),   (x,    y+22,  6,10))
    pygame.draw.rect(surf, (200, 30, 30),   (x+26, y+22,  6,10))
    pygame.draw.rect(surf, (30,  80,180),   (x+4,  y+36, 10,10))
    pygame.draw.rect(surf, (30,  80,180),   (x+18, y+36, 10,10))
    pygame.draw.rect(surf, (100, 60, 20),   (x+2,  y+44, 14, 6))
    pygame.draw.rect(surf, (100, 60, 20),   (x+16, y+44, 14, 6))

# ── Level layouts (world coords) ────────────────────────
BLOCK_WX = 300
BLOCK_W  = 32   # as thin as Mario
BLOCK_H  = 120

FLAG_WX = 1100
FLAG_W  = 10
FLAG_H  = 280

# Pit exactly centered between block and flag
PIT_CENTER = (BLOCK_WX + BLOCK_W + FLAG_WX) // 2
PIT_START  = PIT_CENTER - 60
PIT_END    = PIT_CENTER + 60

# Invisible laser — horizontal, same size as red laser
# Sits one laser-length gap to the RIGHT of the block
# So when Mario stands on block and scrolls right, they see it
LASER_W   = 90
LASER_H   = 8
LASER_OFF = 30   # height above ground

INVIS_LASER_WX = BLOCK_WX + BLOCK_W + LASER_W  # one laser-width gap after the block

WORLD_WIDTH = FLAG_WX + 400

GROUND_SEGMENTS = [
    (0,       PIT_START),
    (PIT_END, WORLD_WIDTH - PIT_END),
]

PLATFORMS = [
    (BLOCK_WX, GROUND_Y - BLOCK_H, BLOCK_W, BLOCK_H),
]

# ── Button ───────────────────────────────────────────────
class Button:
    def __init__(self, rect, label, font=None):
        self.rect  = pygame.Rect(rect)
        self.label = label
        self.font  = font or font_med

    def draw(self, surf):
        mx, my = pygame.mouse.get_pos()
        col = BTN_HOVER if self.rect.collidepoint(mx, my) else BTN_COL
        pygame.draw.rect(surf, col,       self.rect, border_radius=6)
        pygame.draw.rect(surf, DARK_GRAY, self.rect, 2, border_radius=6)
        txt = self.font.render(self.label, True, BLACK)
        surf.blit(txt, (self.rect.centerx - txt.get_width()//2,
                        self.rect.centery - txt.get_height()//2))

    def clicked(self, pos):
        return self.rect.collidepoint(pos)

# ── Game ─────────────────────────────────────────────────
class Game:
    def __init__(self):
        self.state = "menu"
        self.level = 1

        bw, bh = 52, 42
        by = HEIGHT - bh - 8
        self.btn_left    = Button((8,        by, bw, bh), "◀")
        self.btn_right   = Button((8+bw+6,   by, bw, bh), "▶")
        self.btn_up      = Button((WIDTH - bw - 8, by, bw, bh), "▲")
        self.btn_lvl     = [
            Button((100, 165, 80, 70), "1", font_big),
            Button((200, 165, 80, 70), "2", font_big),
            Button((300, 165, 80, 70), "3", font_big),
        ]
        self.btn_restart = Button((WIDTH//2-75, HEIGHT//2+55,  150, 40), "Play Again")
        self.btn_menu    = Button((WIDTH//2-75, HEIGHT//2+105, 150, 40), "Main Menu")

        self.moving_left  = False
        self.moving_right = False
        self._init_level()

    def _init_level(self):
        self.world_x   = 0
        self.mario_sx  = 80
        self.mario_y   = float(GROUND_Y - MARIO_H)
        self.vel_y     = 0.0
        self.on_ground = True
        self.jumps_used = 0
        self.death_msg  = ""
        self.moving_left  = False
        self.moving_right = False
        # Moving red laser: starts at flag, travels left toward block
        self.laser_wx  = float(FLAG_WX + 80)
        self.laser_spd = 3
        self.laser_w   = LASER_W
        self.laser_h   = LASER_H
        self.laser_off = LASER_OFF
        self.jump_held   = False   # is jump key/button being held
        self.invis_wx    = float(FLAG_WX + 80 + LASER_W + LASER_W * 2)

    def start_level(self, lvl):
        self.level = lvl
        self._init_level()
        self.state = "playing"

    @property
    def jumps_allowed(self):
        return 2 if self.level == 2 else 999

    def jump(self):
        if self.state != "playing":
            return
        if self.on_ground and self.jumps_used < self.jumps_allowed:
            self.vel_y      = -13
            self.on_ground  = False
            self.jumps_used += 1

    def get_mario_rect(self):
        return pygame.Rect(self.mario_sx - MARIO_W//2,
                           int(self.mario_y), MARIO_W, MARIO_H)

    def update(self):
        if self.state != "playing":
            return

        # Mouse held on buttons
        if pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            if self.btn_left.rect.collidepoint(mx, my):
                self.moving_left = True
            elif self.btn_right.rect.collidepoint(mx, my):
                self.moving_right = True
            elif self.btn_up.rect.collidepoint(mx, my):
                self.jump_held = True
        else:
            # Release jump_held when mouse not pressed
            if not any(pygame.key.get_pressed()[k] for k in (pygame.K_UP, pygame.K_w, pygame.K_SPACE)):
                self.jump_held = False

        scroll = 5
        if self.moving_left:
            self.world_x = max(0, self.world_x - scroll)
        if self.moving_right:
            # No cap — let player scroll as far right as the world goes
            self.world_x += scroll

        # Gravity
        self.vel_y   += 0.6
        self.vel_y    = min(self.vel_y, 14)
        self.mario_y += self.vel_y

        mario_world_x = self.mario_sx + self.world_x

        # Assume not on ground until proven otherwise each frame
        self.on_ground = False

        # Land on ground segments
        on_solid = any(gx <= mario_world_x <= gx + gw for (gx, gw) in GROUND_SEGMENTS)
        if on_solid and self.mario_y >= GROUND_Y - MARIO_H:
            self.mario_y   = float(GROUND_Y - MARIO_H)
            self.vel_y     = 0.0
            self.on_ground = True

        # Fell into pit — die
        if not on_solid and self.mario_y > HEIGHT:
            self.death_msg = "You fell into the pit!"
            self.state = "dead"
            return

        # Block collision — prevent phasing through
        mrect = self.get_mario_rect()
        for (wx, py, pw, ph) in PLATFORMS:
            sx  = wx - self.world_x
            pr  = pygame.Rect(sx, py, pw, ph)
            if not mrect.colliderect(pr):
                continue
            # Landing on top
            if self.vel_y >= 0 and mrect.bottom <= pr.top + abs(self.vel_y) + 4:
                self.mario_y   = float(pr.top - MARIO_H)
                self.vel_y     = 0.0
                self.on_ground = True
            # Hitting left side — push world right (mario moves left relative)
            elif mrect.right > pr.left and mrect.left < pr.left:
                self.world_x  -= scroll
            # Hitting right side — push world left
            elif mrect.left < pr.right and mrect.right > pr.right:
                self.world_x  += scroll

        # Move red laser leftward; respawn at flag the instant it touches the block
        self.laser_wx -= self.laser_spd
        if self.laser_wx <= BLOCK_WX + BLOCK_W:
            self.laser_wx = float(FLAG_WX + 80)

        # Invisible laser moves independently — full cycle from spawn to block
        self.invis_wx -= self.laser_spd
        if self.invis_wx <= BLOCK_WX + BLOCK_W:
            self.invis_wx = float(FLAG_WX + 80 + self.laser_w + self.laser_w * 2)

        # Moving laser collision
        mrect   = self.get_mario_rect()
        lsx     = self.laser_wx - self.world_x
        laser_y = GROUND_Y - self.laser_h - self.laser_off
        if mrect.colliderect(pygame.Rect(lsx, laser_y, self.laser_w, self.laser_h)):
            self.death_msg = "You got hit by the laser!"
            self.state = "dead"
            return

        # Level 3 — invisible laser, independent cycle
        if self.level == 3:
            isx = self.invis_wx - self.world_x
            isy = GROUND_Y - LASER_H - LASER_OFF
            if mrect.colliderect(pygame.Rect(isx, isy, LASER_W, LASER_H)):
                self.death_msg = "Ha ha ha there was an invisible laser!"
                self.state = "dead"
                return

        # Continuous jump — if jump held and just landed, jump again
        if self.jump_held and self.on_ground:
            self.jump()
        fsx = FLAG_WX - self.world_x
        if mrect.colliderect(pygame.Rect(fsx, GROUND_Y - FLAG_H, FLAG_W, FLAG_H)):
            self.state = "win"

    # ── Drawing ─────────────────────────────────────────
    def draw_world(self, surf):
        surf.fill(SKY)

        # Ground segments (with pit gap between them)
        for (gx, gw) in GROUND_SEGMENTS:
            sx = gx - self.world_x
            pygame.draw.rect(surf, GROUND_COL, (sx, GROUND_Y, gw, GROUND_H))
            pygame.draw.rect(surf, DIRT_COL,   (sx, GROUND_Y + GROUND_H, gw, DIRT_H))

        # Brown block
        for (wx, py, pw, ph) in PLATFORMS:
            sx = wx - self.world_x
            if -pw < sx < WIDTH + pw:
                pygame.draw.rect(surf, BROWN, (sx, py, pw, ph))
                pygame.draw.rect(surf, (120, 60, 30), (sx, py, pw, ph), 2)

        # Moving red laser
        lsx = int(self.laser_wx - self.world_x)
        laser_y = GROUND_Y - self.laser_h - self.laser_off
        if -self.laser_w < lsx < WIDTH + self.laser_w:
            pygame.draw.rect(surf, RED, (lsx, laser_y, self.laser_w, self.laser_h))
            pygame.draw.rect(surf, (255, 100, 100), (lsx, laser_y, self.laser_w, 2))

        # Invisible laser — shown only when Mario is on top of the block (level 3)
        if self.level == 3:
            mario_world_x = self.mario_sx + self.world_x
            on_block = (
                BLOCK_WX - 10 <= mario_world_x <= BLOCK_WX + BLOCK_W + 10 and
                self.mario_y <= GROUND_Y - BLOCK_H + 5 and
                self.on_ground
            )
            if on_block:
                isx = int(self.invis_wx - self.world_x)
                isy = GROUND_Y - LASER_H - LASER_OFF
                pygame.draw.rect(surf, (255, 80, 80),   (isx, isy, LASER_W, LASER_H))
                pygame.draw.rect(surf, (255, 150, 150), (isx, isy, LASER_W, 2))

        # Flag pole
        fsx = FLAG_WX - self.world_x
        if -FLAG_W < fsx < WIDTH + FLAG_W:
            pygame.draw.rect(surf, YELLOW, (fsx, GROUND_Y - FLAG_H, FLAG_W, FLAG_H))
            pygame.draw.rect(surf, (180, 160, 0), (fsx, GROUND_Y - FLAG_H, FLAG_W, FLAG_H), 2)
            pygame.draw.polygon(surf, (220, 30, 30), [
                (fsx + FLAG_W, GROUND_Y - FLAG_H),
                (fsx + FLAG_W + 30, GROUND_Y - FLAG_H + 15),
                (fsx + FLAG_W, GROUND_Y - FLAG_H + 30),
            ])
            pygame.draw.circle(surf, WHITE, (fsx + FLAG_W // 2, GROUND_Y - FLAG_H - 6), 7)
            pygame.draw.circle(surf, DARK_GRAY, (fsx + FLAG_W // 2, GROUND_Y - FLAG_H - 6), 7, 2)

        draw_mario(surf, self.mario_sx, int(self.mario_y) + MARIO_H // 2)

        if self.level == 2:
            rem = self.jumps_allowed - self.jumps_used
            t   = font_med.render(f"Jumps: {rem}", True, BLACK)
            surf.blit(t, (10, 10))

        self.btn_left.draw(surf)
        self.btn_right.draw(surf)
        self.btn_up.draw(surf)

    def draw_menu(self, surf):
        surf.fill(SKY)
        pygame.draw.rect(surf, GROUND_COL, (0, GROUND_Y,            WIDTH, GROUND_H))
        pygame.draw.rect(surf, DIRT_COL,   (0, GROUND_Y + GROUND_H, WIDTH, DIRT_H))
        draw_mario(surf, 60, GROUND_Y - MARIO_H // 2)

        title = font_big.render("TYPE 1 OR 2 OR 3", True, BLACK)
        surf.blit(title, (WIDTH//2 - title.get_width()//2, 85))

        hint = font_tiny.render("click a box or press 1 / 2 / 3", True, DARK_GRAY)
        surf.blit(hint, (WIDTH//2 - hint.get_width()//2, 148))

        for btn in self.btn_lvl:
            btn.draw(surf)

    def draw_dead(self, surf):
        self.draw_world(surf)
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        surf.blit(ov, (0, 0))

        dead_t = font_big.render("YOU DIED", True, RED)
        surf.blit(dead_t, (WIDTH//2 - dead_t.get_width()//2, HEIGHT//2 - 100))

        # wrap long death message
        words = self.death_msg.split()
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if font_small.size(test)[0] < WIDTH - 40:
                cur = test
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)

        y = HEIGHT//2 - 45
        for line in lines:
            t = font_small.render(line, True, WHITE)
            surf.blit(t, (WIDTH//2 - t.get_width()//2, y))
            y += 26

        self.btn_restart.draw(surf)
        self.btn_menu.draw(surf)

    def draw_win(self, surf):
        self.draw_world(surf)
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 130))
        surf.blit(ov, (0, 0))

        t1 = font_big.render("YOU WIN!", True, YELLOW)
        t2 = font_med.render(f"Level {self.level} Complete!", True, WHITE)
        surf.blit(t1, (WIDTH//2 - t1.get_width()//2, HEIGHT//2 - 90))
        surf.blit(t2, (WIDTH//2 - t2.get_width()//2, HEIGHT//2 - 30))

        self.btn_restart.draw(surf)
        self.btn_menu.draw(surf)

    def handle_mousedown(self, pos):
        if self.state == "menu":
            for i, btn in enumerate(self.btn_lvl):
                if btn.clicked(pos):
                    self.start_level(i + 1)
        elif self.state == "playing":
            if self.btn_left.clicked(pos):
                self.moving_left = True
            elif self.btn_right.clicked(pos):
                self.moving_right = True
            elif self.btn_up.clicked(pos):
                self.jump()
        elif self.state in ("dead", "win"):
            if self.btn_restart.clicked(pos):
                self.start_level(self.level)
            elif self.btn_menu.clicked(pos):
                self.state = "menu"

    def handle_mouseup(self, pos):
        if self.btn_left.rect.collidepoint(pos):
            self.moving_left = False
        if self.btn_right.rect.collidepoint(pos):
            self.moving_right = False

# ── Main loop ────────────────────────────────────────────
game = Game()

while True:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if game.state == "menu":
                if event.key == pygame.K_1: game.start_level(1)
                if event.key == pygame.K_2: game.start_level(2)
                if event.key == pygame.K_3: game.start_level(3)
            elif game.state == "playing":
                if event.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
                    game.jump_held = True
                    game.jump()
                if event.key in (pygame.K_LEFT,  pygame.K_a):
                    game.moving_left  = True
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    game.moving_right = True
            elif game.state in ("dead", "win"):
                if event.key == pygame.K_r: game.start_level(game.level)
                if event.key == pygame.K_m: game.state = "menu"

        if event.type == pygame.KEYUP:
            if event.key in (pygame.K_LEFT,  pygame.K_a):
                game.moving_left  = False
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                game.moving_right = False
            if event.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
                game.jump_held = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            game.handle_mousedown(event.pos)
        if event.type == pygame.MOUSEBUTTONUP:
            game.handle_mouseup(event.pos)

    game.update()

    if   game.state == "menu":    game.draw_menu(surf=screen)
    elif game.state == "playing": game.draw_world(surf=screen)
    elif game.state == "dead":    game.draw_dead(surf=screen)
    elif game.state == "win":     game.draw_win(surf=screen)

    pygame.display.flip()
