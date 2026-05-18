import sys
import math
import random
import pygame

from player import Player
from game import Game

pygame.init()

# Palette
C_TABLE    = (8,  45,  28)
C_TABLE_DK = (4,  28,  18)
C_RING       = (210, 165,  55)
C_START_BG   = ( 95,  15,  15)
C_START_DK   = ( 42,  24,   8)
C_PANEL_BG   = (  8,  35,  22)
C_CARD_BG    = (255, 253, 247)
C_CARD_SEL   = (190, 220, 255)
C_CARD_BACK  = ( 28,  70, 160)
C_CARD_BDR   = (190, 175, 155)
C_WHITE      = (255, 255, 255)
C_GOLD       = (212, 175,  55)
C_GOLD_DK    = (140, 100,  30)
C_RED        = (190,  20,  20)
C_BLACK      = ( 20,  20,  20)
C_TXT_LIGHT  = (248, 250, 252)
C_TXT_MUTED  = (180, 230, 200)
C_BTN_GOLD   = ( 42,  24,   8)
C_BTN_GREEN  = ( 30, 110,  30)
C_BTN_GREY   = ( 55,  65,  80)
C_BTN_PURPLE = ( 90,  40, 190)
C_NOTICE_BG  = (  7,  25,  18)

RED_SUITS = {"♦", "♥"}


def _load_fonts(scale=1.0):
    SF = pygame.font.SysFont

    def size(n):
        return max(8, int(n * scale))

    return {
        "title"  : SF("Cooper black", size(104), bold=False),
        "title2" : SF("Cooper black", size(64), bold=False),
        "start"  : SF("Cooper black", size(28), bold=False),
        "hint"   : SF("Cooper black", size(13), bold=False),
        "hint1"   : SF("Cooper black", size(20), bold=False),
        "h1"     : SF("Cooper black", size(38), bold=False),
        "h2"     : SF("Cooper black", size(32), bold=False),
        "h3"     : SF("Cooper black", size(20), bold=False),
        "body"   : SF("Cooper black", size(16), bold=False),
        "bodyb"  : SF("Cooper black", size(16), bold=False),
        "sm"     : SF("Cooper black", size(13), bold=False),
        "smb"    : SF("Cooper black", size(13), bold=False),
        "crank"  : SF("Cooper black", size(22), bold=False),
        "csuit"  : SF("Times New Roman", size(22), bold=False),
        "cbig"   : SF("Times New Roman", size(72), bold=False),
        "crbig"  : SF("Times New Roman", size(24), bold=False),
        "icon"   : SF("Segoe UI Emoji", size(28), bold=False),
        "iconlbl": SF("Cooper black", size(12), bold=False),
        "msg" : SF("Times New Roman", size(15), bold=True),
    }


def blit_text(surf, text, font, color, x, y, anchor="topleft"):
    img = font.render(str(text), True, color)
    r = img.get_rect(**{anchor: (int(x), int(y))})
    surf.blit(img, r)
    return r


def draw_game_logo(surf, font, text, cx, cy, scale=1.0, angle=-8):
    """
    Draws a game-style title:
    - tilted
    - thick shadow
    - fake outline
    - soft glow
    """
    cx, cy = int(cx), int(cy)
    outline = max(2, int(4 * scale))
    shadow_offset = max(3, int(6 * scale))

    # Soft glow behind the title
    glow = font.render(text, True, (255, 220, 120))
    glow = pygame.transform.rotozoom(glow, angle, 1.06)
    glow_rect = glow.get_rect(center=(cx, cy))

    glow_layer = pygame.Surface((glow_rect.w + 40, glow_rect.h + 40), pygame.SRCALPHA)
    for radius_alpha in [(18, 30), (11, 45), (6, 60)]:
        pad, alpha = radius_alpha
        temp = glow.copy()
        temp.set_alpha(alpha)
        glow_layer.blit(temp, (20, 20))
        glow_layer = pygame.transform.smoothscale(
            glow_layer,
            (glow_layer.get_width(), glow_layer.get_height())
        )
    surf.blit(glow_layer, (glow_rect.x - 20, glow_rect.y - 20))

    # Shadow
    shadow = font.render(text, True, (45, 14, 6))
    shadow = pygame.transform.rotozoom(shadow, angle, 1.0)
    shadow_rect = shadow.get_rect(center=(cx + shadow_offset, cy + shadow_offset))
    surf.blit(shadow, shadow_rect)

    # Fake outline by drawing text around the main position
    outline_color = (86, 42, 12)
    for ox in range(-outline, outline + 1, max(1, outline)):
        for oy in range(-outline, outline + 1, max(1, outline)):
            if ox == 0 and oy == 0:
                continue
            img = font.render(text, True, outline_color)
            img = pygame.transform.rotozoom(img, angle, 1.0)
            rect = img.get_rect(center=(cx + ox, cy + oy))
            surf.blit(img, rect)

    # Highlight layer
    hi = font.render(text, True, (255, 236, 145))
    hi = pygame.transform.rotozoom(hi, angle, 1.0)
    hi_rect = hi.get_rect(center=(cx - int(2 * scale), cy - int(3 * scale)))
    surf.blit(hi, hi_rect)

    # Main gold title
    main = font.render(text, True, C_GOLD)
    main = pygame.transform.rotozoom(main, angle, 1.0)
    main_rect = main.get_rect(center=(cx, cy))
    surf.blit(main, main_rect)


def rrect(surf, color, rect, r=12, bw=0, bc=None):
    rect = pygame.Rect(int(rect.x), int(rect.y), int(rect.w), int(rect.h))
    pygame.draw.rect(surf, color, rect, border_radius=int(r))
    if bw and bc:
        pygame.draw.rect(surf, bc, rect, int(bw), border_radius=int(r))


def suit_col(card_str):
    return C_RED if card_str[-1] in RED_SUITS else C_BLACK


def draw_face(surf, fonts, x, y, w, h, label, selected=False, show_corner_suit=True, big_suit_scale=1.0):
    x, y, w, h = int(x), int(y), int(w), int(h)
    if w <= 8 or h <= 8:
        return

    bg = C_CARD_SEL if selected else C_CARD_BG
    radius = max(6, int(min(w, h) * 0.12))

    sh = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0, 0, 0, 80), (6, 6, w, h), border_radius=radius)
    surf.blit(sh, (x - 3, y - 3))

    cs = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(cs, bg, (0, 0, w, h), border_radius=radius)

    border_w = max(2, int(w * 0.035))
    pygame.draw.rect(cs, (110, 95, 80), (0, 0, w, h), border_w, border_radius=radius)
    pygame.draw.rect(cs, (255, 255, 255), (2, 2, w - 4, h - 4), 1, border_radius=max(1, radius - 1))

    if selected:
        pygame.draw.rect(cs, (80, 140, 230), (0, 0, w, h), max(3, border_w + 1), border_radius=radius)

    col = suit_col(label)
    rank = label[:-1]
    suit = label[-1]

    ri = fonts["crank"].render(rank, True, col)

    pad = max(5, int(w * 0.14))
    cs.blit(ri, (pad, max(4, int(h * 0.06))))

    
    if show_corner_suit:
        si = fonts["csuit"].render(suit, True, col)
        cs.blit(si, (pad, max(18, int(h * 0.06) + ri.get_height())))

   
    # Big suit size can now be controlled per card area.
    # Cover cards keep their original behaviour.
    # Game cards without corner suit can use different sizes for centre cards and hand cards.
    if show_corner_suit:
        big_font = fonts["cbig"] if h >= 100 else fonts["crbig"]
    else:
        suit_size = max(10, int(24 * big_suit_scale * (h / 68)))
        big_font = pygame.font.SysFont("Times New Roman", suit_size, bold=False)

    bi = big_font.render(suit, True, col)
    cs.blit(bi, (w // 2 - bi.get_width() // 2, h // 2 - bi.get_height() // 2))

    surf.blit(cs, (x, y))


def draw_rotated_face(surf, fonts, x, y, w, h, label, angle=0, selected=False):
    w = int(w)
    h = int(h)
    card_surf = pygame.Surface((w + 12, h + 12), pygame.SRCALPHA)
    draw_face(card_surf, fonts, 6, 6, w, h, label, selected=selected)

    rotated = pygame.transform.rotate(card_surf, angle)
    rect = rotated.get_rect(center=(int(x + w // 2), int(y + h // 2)))
    surf.blit(rotated, rect.topleft)


def draw_back(surf, x, y, w, h):
    x, y, w, h = int(x), int(y), int(w), int(h)
    if w <= 8 or h <= 8:
        return

    radius = max(5, int(min(w, h) * 0.12))

    sh = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0, 0, 0, 50), (4, 4, w, h), border_radius=radius)
    surf.blit(sh, (x - 2, y - 2))

    cs = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(cs, C_CARD_BACK, (0, 0, w, h), border_radius=radius)
    pygame.draw.rect(cs, (120, 170, 235), (0, 0, w, h), max(1, int(w * 0.04)), border_radius=radius)
    margin = max(4, int(w * 0.12))
    pygame.draw.rect(cs, (18, 52, 125), (margin, margin, w - margin * 2, h - margin * 2), border_radius=max(3, radius - 3))
    surf.blit(cs, (x, y))


def draw_rotated_back_center(surf, cx, cy, w, h, angle=90):
    w = int(w)
    h = int(h)
    card_surf = pygame.Surface((w + 12, h + 12), pygame.SRCALPHA)
    draw_back(card_surf, 6, 6, w, h)
    rotated = pygame.transform.rotate(card_surf, angle)
    rect = rotated.get_rect(center=(int(cx), int(cy)))
    surf.blit(rotated, rect.topleft)


def draw_rotated_stack_backs_vert(surf, cx, cy, count, cw=40, ch=58, spread_scale=0.42, angle=90):
    show = min(count, 13)
    if show == 0:
        return

    spread = int(ch * spread_scale)
    total = spread * (show - 1)
    sy = cy - total // 2

    for i in range(show):
        draw_rotated_back_center(surf, cx, sy + i * spread, cw, ch, angle=angle)


def draw_fan_backs_horiz(surf, cx, y, count, cw=50, ch=72, spread_scale=0.75):
    show = min(count, 13)
    if show == 0:
        return

    spread = int(cw * spread_scale)
    total = spread * (show - 1)
    sx = cx - total // 2

    for i in range(show):
        draw_back(surf, sx + i * spread, y, cw, ch)


def draw_stack_backs_vert(surf, x, cy, count, cw=44, ch=62):
    show = min(count, 12)
    if show == 0:
        return
    spread = min(int(ch * 0.22), 160 // max(show, 1))
    total = spread * (show - 1)
    sy = cy - total // 2
    for i in range(show):
        draw_back(surf, x, sy + i * spread, cw, ch)


def draw_slanted_stack_backs(surf, start_x, start_y, count, cw=34, ch=48, dx=8, dy=10):
    """
    Draw upright card backs along a diagonal line.

    Cards remain vertical (not rotated). Only the stack layout is slanted.
    Positive dx makes the stack lean to the right.
    Negative dx makes the stack lean to the left.
    """
    show = min(count, 13)
    if show == 0:
        return

    for i in range(show):
        x = int(start_x + i * dx)
        y = int(start_y + i * dy)
        draw_back(surf, x, y, cw, ch)


def draw_avatar(surf, fonts, cx, cy, r, label, active=False):
    cx, cy, r = int(cx), int(cy), int(r)
    oc = C_GOLD if active else C_GOLD_DK
    pygame.draw.circle(surf, (30, 65, 38), (cx, cy), r)
    pygame.draw.circle(surf, oc, (cx, cy), r, max(2, int(r * 0.16)))

    text = str(label).upper()
    if len(text) > 2:
        text = text[0]

    font = fonts["sm"] if len(text) == 2 else fonts["h3"]
    blit_text(surf, text, font, C_GOLD, cx, cy, anchor="center")


class Btn:
    def __init__(self, x, y, w, h, text, bg, fg=C_WHITE, fk="h3", r=12, icon=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.bg = bg
        self.fg = fg
        self.fk = fk
        self.r = r
        self.icon = icon
        self.disabled = False
        self.hovered = False
        self.press_anim = 0

    def move(self, x, y, w=None, h=None):
        self.rect.x = int(x)
        self.rect.y = int(y)
        if w is not None:
            self.rect.width = int(w)
        if h is not None:
            self.rect.height = int(h)

    def draw(self, surf, fonts, glow=False, scale=1.0):
        a = 80 if self.disabled else 255

        # Keep the old clean gold feeling.
        # No brown / coffee shadow layers.
        col = tuple(min(255, c + 10) for c in self.bg) if (self.hovered and not self.disabled) else self.bg

        pulse = 0
        if self.hovered and not self.disabled:
            pulse = int(3 * scale)

        press_offset = 0
        if self.press_anim > 0:
            press_offset = int(2 * scale)
            self.press_anim -= 1

        draw_rect = self.rect.copy()
        draw_rect.y += press_offset
        draw_rect.inflate_ip(pulse, pulse)

        if glow and not self.disabled:
            pad = int((12 + pulse) * scale)
            glow_alpha = 50 if self.hovered else 25
            gs = pygame.Surface((draw_rect.w + pad * 2, draw_rect.h + pad * 2), pygame.SRCALPHA)
            pygame.draw.rect(
                gs,
                (255, 205, 70, glow_alpha),
                (pad, pad, draw_rect.w, draw_rect.h),
                border_radius=int(self.r + 10 * scale)
            )
            surf.blit(gs, (draw_rect.x - pad, draw_rect.y - pad))

        s = pygame.Surface((draw_rect.w, draw_rect.h), pygame.SRCALPHA)
        rr = pygame.Rect(0, 0, draw_rect.w, draw_rect.h)

        # Main clean gold body
        pygame.draw.rect(s, (*col, a), rr, border_radius=int(self.r))

     
       

        # Clean gold border, no brown
        pygame.draw.rect(
            s,
            (*C_GOLD, a),
            rr,
            max(1, int(2 * scale)),
            border_radius=int(self.r)
        )

        pygame.draw.rect(
            s,
            (255, 220, 120, int(100 * a / 255)),
            rr.inflate(-int(5 * scale), -int(5 * scale)),
            max(1, int(1 * scale)),
            border_radius=int(self.r * 0.8)
        )

        surf.blit(s, draw_rect.topleft)

        label = ((self.icon + " ") if self.icon else "") + self.text
        fc = tuple(c * a // 255 for c in self.fg)

        blit_text(surf, label, fonts[self.fk], fc, draw_rect.centerx, draw_rect.centery, anchor="center")

    def clicked(self, ev):
        hit = (
            not self.disabled
            and ev.type == pygame.MOUSEBUTTONDOWN
            and ev.button == 1
            and self.rect.collidepoint(ev.pos)
        )
        if hit:
            self.press_anim = 12
        return hit

    def hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)


class Big2GUI:
    BASE_W = 960
    BASE_H = 600
    MIN_W = 900
    MIN_H = 400

    def __init__(self):
        self.W = self.BASE_W
        self.H = self.BASE_H
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.scale = 1.0
        self.layout_x = 0
        self.layout_y = 0

        self.screen = pygame.display.set_mode((self.W, self.H), pygame.RESIZABLE)
        pygame.display.set_caption("Big 2")
        self.clock = pygame.time.Clock()
        self.fonts = _load_fonts(self.scale)

        self.state = "start"
        self.player_count = 3
        self.players = []
        self.game = None
        self.selected = []
        self.messages = []
        self.fly_cards = []
        self.action_msg = ""
        self.action_msg_owner = ""
        self.action_msg_ms = 0
        self.action_msg_duration = 999999
        self.result_banner_text = ""
        self.result_banner_kind = ""
        self.result_banner_ms = 0
        self.result_banner_duration = 2600
        self.round_result = None
        self.round_result_ms = 0
        self.round_result_countdown_ms = 3000
        self.round_result_explosion_ms = 700
        self.round_result_teaser_ms = 2000
        self.round_result_duration = self.round_result_countdown_ms + self.round_result_explosion_ms + self.round_result_teaser_ms
        self.round_result_countdown_active = False
        self.game_result = None
        self.game_result_ready = False
        self.game_result_delay_ms = 0
        self.ai_turn_delay_ms = 1500
        self.ai_turn_delay_min_ms = 1000
        self.ai_turn_delay_max_ms = 2000
        self.ai_wait_ms = 0
        self.notice_txt = ""
        self.notice_ms = 0
        self.hand_rects = []
        self.start_anim_ms = pygame.time.get_ticks()
        self.dealing_locked = False
        self.deal_finish_ms = 0
        self.deal_banner_text = ""
        self.deal_banner_ms = 0
        self.deal_deck_remaining = 0
        self.deal_total_ms = 0
        self.pending_opening_msg = ""
        self.pending_opening_owner = ""
        self.pending_action_msg = ""
        self.pending_action_owner = ""
        self.pending_action_ms = 0
        self.bottom_icon_rects = {}
        self.bottom_icon_press = {"achievements": 0, "settings": 0, "how_to_play": 0}
        self.bottom_icon_hover = {"achievements": False, "settings": False, "how_to_play": False}
        self.pending_menu_state = None
        self.pending_menu_ms = 0

        self._mk_start_btns()
        self._mk_select_btns()
        self._mk_game_btns()
        self._refresh_scale()

    def S(self, val):
        return int(val * self.scale)

    def SX(self, val):
        # Scaled x value only. Do not add layout offsets here, because SX is
        # also used for relative spacing between UI elements.
        return int(val * self.scale)

    def SY(self, val):
        # Scaled y value only. Do not add layout offsets here.
        return int(val * self.scale)

    def _refresh_scale(self):
        # Uniform scale keeps the UI proportional without breaking relative
        # spacing. Window-edge elements still use W / H directly where needed.
        self.scale = min(self.W / self.BASE_W, self.H / self.BASE_H)
        self.scale = max(0.65, min(1.8, self.scale))
        self.scale_x = self.scale
        self.scale_y = self.scale
        self.layout_x = 0
        self.layout_y = 0
        self.fonts = _load_fonts(self.scale)

    def _mk_start_btns(self):
        self.b_start = Btn(0, 0, 280, 56, "START GAME", C_BTN_GOLD, C_GOLD, "start", r=28)

    def _mk_select_btns(self):
        self.b_back_sel = Btn(30, 20, 56, 42, "<", C_START_DK, C_GOLD, "h2", r=8)
        self.b_2p = Btn(0, 0, 180, 150, "", (130, 10, 10), C_WHITE, "h1", r=16)
        self.b_3p = Btn(0, 0, 180, 150, "", (130, 10, 10), C_WHITE, "h1", r=16)
        self.b_4p = Btn(0, 0, 180, 150, "", (130, 10, 10), C_WHITE, "h1", r=16)
        self.b_confirm = Btn(0, 0, 220, 52, "CONFIRM", C_BTN_GOLD, C_GOLD, "h2", r=26)

    def _mk_game_btns(self):
        self.b_back = Btn(16, 12, 52, 38, "<", C_START_DK, C_GOLD, "h2", r=8)
        self.b_play = Btn(0, 0, 120, 40, "Play", C_BTN_GOLD, C_GOLD, "h3", r=10, icon="")
        self.b_pass = Btn(0, 0, 120, 40, "Pass", C_BTN_GREEN, C_WHITE, "h3", r=10, icon="")
        self.b_clr  = Btn(0, 0, 130, 40, "Reset", C_BTN_GREY, C_WHITE, "h3", r=10, icon="")
        self.b_new  = Btn(0, 0, 108, 34, "New Game", C_BTN_PURPLE, C_WHITE, "sm", r=8)
        self.b_again = Btn(0, 0, 170, 44, "Play Again", C_BTN_GREEN, C_WHITE, "h3", r=12)
        self.b_end = Btn(0, 0, 170, 44, "End Game", C_BTN_GREY, C_WHITE, "h3", r=12)
        self.b_round_next = Btn(0, 0, 104, 52, "", (172, 58, 18), C_WHITE, "h3", r=22)

    def _all_btns(self):
        return [
            self.b_start,
            self.b_back_sel, self.b_2p, self.b_3p, self.b_4p, self.b_confirm,
            self.b_back, self.b_play, self.b_pass, self.b_clr, self.b_new,
            self.b_again, self.b_end, self.b_round_next
        ]

    def run(self):
        while True:
            dt = self.clock.tick(60)
            mouse = pygame.mouse.get_pos()
            events = pygame.event.get()

            for e in events:
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if e.type == pygame.VIDEORESIZE:
                    self.W = max(self.MIN_W, e.w)
                    self.H = max(self.MIN_H, e.h)
                    self.screen = pygame.display.set_mode((self.W, self.H), pygame.RESIZABLE)
                    self._refresh_scale()

                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self.state = "start"
                        self.start_anim_ms = pygame.time.get_ticks()
                        continue

                getattr(self, f"_ev_{self.state}")(e)

            for b in self._all_btns():
                b.hover(mouse)

            if self.state == "start":
                for name, rect in self.bottom_icon_rects.items():
                    self.bottom_icon_hover[name] = rect.collidepoint(mouse)
            else:
                for name in self.bottom_icon_hover:
                    self.bottom_icon_hover[name] = False

            for name in self.bottom_icon_press:
                if self.bottom_icon_press[name] > 0:
                    self.bottom_icon_press[name] -= 1

            if self.pending_menu_ms > 0:
                self.pending_menu_ms -= dt
                if self.pending_menu_ms <= 0 and self.pending_menu_state:
                    self.state = self.pending_menu_state
                    self.pending_menu_state = None
                    self.start_anim_ms = pygame.time.get_ticks()

            if self.notice_ms > 0:
                self.notice_ms -= dt
                if self.notice_ms <= 0:
                    self.notice_txt = ""

            for anim in self.fly_cards[:]:
                if anim.get("delay", 0) > 0:
                    anim["delay"] -= dt
                    if anim["delay"] <= 0 and anim.get("kind") == "deal" and not anim.get("started"):
                        anim["started"] = True
                        self.deal_deck_remaining = max(0, self.deal_deck_remaining - 1)
                    continue

                if anim.get("kind") == "deal" and not anim.get("started"):
                    anim["started"] = True
                    self.deal_deck_remaining = max(0, self.deal_deck_remaining - 1)

                anim["t"] += dt
                if anim["t"] >= anim["duration"]:
                    self.fly_cards.remove(anim)

            if self.deal_banner_ms > 0:
                self.deal_banner_ms -= dt
                if self.deal_banner_ms <= 0:
                    self.deal_banner_text = ""

            if self.dealing_locked and self.deal_finish_ms > 0:
                self.deal_finish_ms -= dt
                if self.deal_finish_ms <= 0 and not self.fly_cards:
                    self.dealing_locked = False
                    self.deal_finish_ms = 0
                    self._after_deal_animation()

            # Keep the latest action narration visible until another action replaces it.
            # This prevents forgetting who played the current table cards.
            if self.action_msg_ms > 0 and self.action_msg_duration < 999000:
                self.action_msg_ms -= dt
                if self.action_msg_ms <= 0:
                    self.action_msg = ""
                    self.action_msg_owner = ""

            if self.result_banner_ms > 0:
                self.result_banner_ms -= dt
                if self.result_banner_ms <= 0:
                    self.result_banner_text = ""
                    self.result_banner_kind = ""

            if self.round_result_countdown_active and self.round_result_ms > 0:
                self.round_result_ms -= dt
                if self.round_result_ms <= 0:
                    self._finish_round_result()

            if self.game_result_delay_ms > 0:
                self.game_result_delay_ms -= dt
                if self.game_result_delay_ms <= 0:
                    self.game_result_ready = True

            if self.pending_action_ms > 0:
                self.pending_action_ms -= dt
                if self.pending_action_ms <= 0:
                    if self.pending_action_msg:
                        self._set_action_message(self.pending_action_msg, self.pending_action_owner)
                        self._log(self.pending_action_msg)
                    self.pending_action_msg = ""
                    self.pending_action_owner = ""
                    self.pending_action_ms = 0

            if (
                self.state == "game"
                and self.game
                and self.ai_wait_ms > 0
                and not self.round_result
                and not self.game_result
                and not self.result_banner_text
                and not self.dealing_locked
            ):
                self.ai_wait_ms -= dt
                if self.ai_wait_ms <= 0:
                    self.ai_wait_ms = 0
                    self._process_ai_turn()

            getattr(self, f"_draw_{self.state}")()

            pygame.display.flip()

    def _draw_start_gradient(self):
        # Radial gradient: bright center, darker edges
        cx = self.W // 2
        cy = self.H // 2
        max_radius = int((cx * cx + cy * cy) ** 0.5)

        center_col = (125,  28,  28)  # middle, softer casino red
        edge_col   = ( 28,   6,   6)  # outside, deeper dark red

        for radius in range(max_radius, 0, -6):
            t = radius / max_radius

            r = int(center_col[0] * (1 - t) + edge_col[0] * t)
            g = int(center_col[1] * (1 - t) + edge_col[1] * t)
            b = int(center_col[2] * (1 - t) + edge_col[2] * t)

            pygame.draw.circle(self.screen, (r, g, b), (cx, cy), radius)

        # Extra vignette: make corners slightly darker
        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        steps = 18
        for i in range(steps):
            inset_x = int(self.W * i / (steps * 2))
            inset_y = int(self.H * i / (steps * 2))
            alpha = int(6 * i)
            rect = pygame.Rect(inset_x, inset_y, self.W - inset_x * 2, self.H - inset_y * 2)
            pygame.draw.rect(overlay, (0, 0, 0, alpha), rect, width=max(1, self.S(18)))

        self.screen.blit(overlay, (0, 0))


    def _draw_table_gradient(self):
        # Smooth radial gradient for game screen: lighter center, darker outer edge.
        cx = self.W // 2
        cy = self.H // 2
        max_radius = int((cx * cx + cy * cy) ** 0.5)

        center_col = (30, 110, 70)
        edge_col   = (4,  24,  15)

        for radius in range(max_radius, 0, -5):
            t = radius / max_radius
            r = int(center_col[0] * (1 - t) + edge_col[0] * t)
            g = int(center_col[1] * (1 - t) + edge_col[1] * t)
            b = int(center_col[2] * (1 - t) + edge_col[2] * t)
            pygame.draw.circle(self.screen, (r, g, b), (cx, cy), radius)

    def _ease_out_back(self, t):
        # Smooth fly-out effect with a tiny bounce at the end
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

    def _draw_chip(self, surf, cx, cy, r, main_col, value, angle=0):
        cx, cy, r = int(cx), int(cy), int(r)
        if r <= 4:
            return

        pad = max(8, self.S(10))
        chip = pygame.Surface((r * 2 + pad * 2, r * 2 + pad * 2), pygame.SRCALPHA)
        c = (r + pad, r + pad)

        cream = (250, 238, 205)
        dark = (28, 20, 18)

        # Main drop shadow
        pygame.draw.circle(
            chip,
            (0, 0, 0, 95),
            (c[0] + self.S(3), c[1] + self.S(4)),
            r
        )

        # Slight thickness under the chip
        pygame.draw.circle(chip, (0, 0, 0, 80), (c[0], c[1] + self.S(5)), r)
        pygame.draw.circle(chip, tuple(max(0, int(v * 0.72)) for v in main_col), (c[0], c[1] + self.S(3)), r)

        # Outer body
        pygame.draw.circle(chip, main_col, c, r)

        # Subtle highlight on upper-left
        highlight = pygame.Surface(chip.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(
            highlight,
            (255, 255, 255, 38),
            (c[0] - int(r * 0.28), c[1] - int(r * 0.32)),
            int(r * 0.55)
        )
        chip.blit(highlight, (0, 0))

        # Outer outline
        pygame.draw.circle(chip, cream, c, r, max(2, self.S(3)))
        pygame.draw.circle(chip, (0, 0, 0, 70), c, r, max(1, self.S(1)))

        # Long rectangular casino edge blocks
        block_count = 10
        block_color = dark if value == "5" else cream

        block_w = max(5, int(r * 0.26))
        block_h = max(8, int(r * 0.42))
        block_radius = max(2, int(r * 0.06))

        for i in range(block_count):
            a = angle + i * (360 / block_count)
            v = pygame.math.Vector2(1, 0).rotate(a)

            bx = c[0] + int((r * 0.82) * v.x)
            by = c[1] + int((r * 0.82) * v.y)

            block_surf = pygame.Surface((block_w + 4, block_h + 4), pygame.SRCALPHA)
            pygame.draw.rect(
                block_surf,
                block_color,
                (2, 2, block_w, block_h),
                border_radius=block_radius
            )
            pygame.draw.rect(
                block_surf,
                (255, 255, 255, 45),
                (3, 3, max(1, block_w - 2), max(1, block_h // 3)),
                border_radius=block_radius
            )

            # Tangential rectangle orientation, similar to real poker chips
            rotated = pygame.transform.rotate(block_surf, -a + 90)
            rect = rotated.get_rect(center=(bx, by))
            chip.blit(rotated, rect)

        # Small decorative dots between edge blocks
        dot_color = cream if value != "5" else dark
        for i in range(block_count):
            a = angle + i * (360 / block_count) + (180 / block_count)
            v = pygame.math.Vector2(1, 0).rotate(a)

            for offset in (-0.06, 0.06):
                dot_a = a + offset * 180
                dv = pygame.math.Vector2(1, 0).rotate(dot_a)
                dx = c[0] + int((r * 0.66) * dv.x)
                dy = c[1] + int((r * 0.66) * dv.y)
                pygame.draw.circle(chip, dot_color, (dx, dy), max(1, int(r * 0.045)))

        # Inner ring details
        pygame.draw.circle(chip, tuple(max(0, int(v * 0.68)) for v in main_col), c, int(r * 0.63))
        pygame.draw.circle(chip, cream, c, int(r * 0.63), max(1, self.S(2)))
        pygame.draw.circle(chip, (255, 255, 255, 60), c, int(r * 0.51), max(1, self.S(1)))

        # Center disk
        pygame.draw.circle(chip, main_col, c, int(r * 0.45))
        pygame.draw.circle(chip, cream, c, int(r * 0.45), max(1, self.S(2)))

        # Center number
        text_col = dark if value == "5" else cream
        blit_text(chip, value, self.fonts["h3"], text_col, c[0], c[1], anchor="center")

        # Optional whole-chip tilt. Positive angle turns left, negative angle turns right.
        if angle != 0:
            rotated = pygame.transform.rotate(chip, angle)
            rect = rotated.get_rect(center=(cx, cy))
            surf.blit(rotated, rect.topleft)
        else:
            surf.blit(chip, (cx - r - pad, cy - r - pad))

    def _draw_decor(self):
        s = self.screen

        # Chip setup:
        # (value, shooting_angle, distance, size, color, chip_static_angle, delay)
        # Angle rule: 0° goes right, 90° goes up, 180° goes left.
        chip_targets = [
            ("5",   175, self.S(300), self.S(28), (235, 228, 214), 20,   0),  # white
            ("10",  140, self.S(420), self.S(32), (190,  42,  38), 10,  70),  # red
            ("20",   60, self.S(305), self.S(40), ( 28, 145,  72), -10, 140),  # green focus
            ("50",   35, self.S(450), self.S(38), ( 42,  70, 160), -15, 210),  # blue
            ("100",  10, self.S(360), self.S(40), ( 35,  30,  26), -25, 280),  # black
        ]

        # Flying start point
        start_x = self.W // 2
        start_y = self.H // 2 + self.SY(75)

        now = pygame.time.get_ticks()
        elapsed = now - self.start_anim_ms
        duration = 900

        for value, shoot_angle, dist, r, col, rot, delay in chip_targets:
            rad = math.radians(shoot_angle)

            tx = start_x + math.cos(rad) * dist
            ty = start_y - math.sin(rad) * dist

            t = max(0, min(1, (elapsed - delay) / duration))
            p = self._ease_out_back(t)

            cx = start_x + (tx - start_x) * p
            cy = start_y + (ty - start_y) * p

            # Light trail while flying
            if t > 0:
                trail = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
                trail_alpha = int(55 * (1 - min(1, t * 0.85)))
                trail_col = (*col, max(18, trail_alpha))

                pygame.draw.line(
                    trail,
                    trail_col,
                    (int(start_x), int(start_y)),
                    (int(cx), int(cy)),
                    max(1, self.S(4))
                )

                pygame.draw.circle(
                    trail,
                    (*col, 35),
                    (int(start_x), int(start_y)),
                    max(4, self.S(8))
                )

                s.blit(trail, (0, 0))

            # Scale from tiny to full size
            rr = max(5, int(r * (0.35 + 0.65 * min(1, t))))

            # Chip pattern stays static, no spinning and no angle text
            self._draw_chip(s, cx, cy, rr, col, value, angle=rot)

    def _draw_bottom_icon(self, key, cx, cy, icon, label):
        base_r = self.S(27)
        hovered = self.bottom_icon_hover.get(key, False)
        press = self.bottom_icon_press.get(key, 0)

        scale_mul = 1.0
        if hovered:
            scale_mul += 0.08
        if press > 0:
            scale_mul += 0.05

        r = max(18, int(base_r * scale_mul))
        draw_y = cy + (self.S(2) if press > 0 else 0)

        glow = pygame.Surface((r * 5, r * 5), pygame.SRCALPHA)
        glow_alpha = 48 if hovered or press > 0 else 28
        pygame.draw.circle(glow, (255, 205, 70, glow_alpha), (glow.get_width() // 2, glow.get_height() // 2), int(r * 1.55))
        self.screen.blit(glow, (cx - glow.get_width() // 2, draw_y - glow.get_height() // 2))

        pygame.draw.circle(self.screen, (42, 24, 8), (cx, draw_y), r)
        pygame.draw.circle(self.screen, C_GOLD, (cx, draw_y), r, max(2, self.S(2)))
        pygame.draw.circle(self.screen, (255, 220, 120), (cx, draw_y), int(r * 0.72), max(1, self.S(1)))

        if icon == "gear":
            icon_txt = "⚙"
            font = self.fonts["icon"]
        elif icon == "trophy":
            icon_txt = "🏆"
            font = self.fonts["icon"]
        else:
            icon_txt = "i"
            font = self.fonts["h2"]

        blit_text(self.screen, icon_txt, font, C_GOLD, cx, draw_y, anchor="center")
        label_rect = blit_text(self.screen, label, self.fonts["iconlbl"], C_GOLD, cx, draw_y + self.S(40), anchor="center")

        hit_rect = pygame.Rect(cx - r - self.S(20), draw_y - r - self.S(10), r * 2 + self.S(40), r * 2 + self.S(65))
        hit_rect.union_ip(label_rect)
        return hit_rect

    def _queue_start_page(self, key, target_state):
        self.bottom_icon_press[key] = 12
        self.pending_menu_state = target_state
        self.pending_menu_ms = 140

    # START
    def _ev_start(self, e):
        if self.b_start.clicked(e):
            self.state = "select"
            return

        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.pending_menu_ms <= 0:
            if self.bottom_icon_rects.get("achievements", pygame.Rect(0, 0, 0, 0)).collidepoint(e.pos):
                self._queue_start_page("achievements", "achievements")
                return
            if self.bottom_icon_rects.get("settings", pygame.Rect(0, 0, 0, 0)).collidepoint(e.pos):
                self._queue_start_page("settings", "settings")
                return
            if self.bottom_icon_rects.get("how_to_play", pygame.Rect(0, 0, 0, 0)).collidepoint(e.pos):
                self._queue_start_page("how_to_play", "how_to_play")
                return

    def _draw_start(self):
        W, H = self.W, self.H
        s = self.screen

        self._draw_start_gradient()
        self._draw_decor()

        title_x = W // 2
        title_y = self.SY(115)
        draw_game_logo(s, self.fonts["title"], "BIG 2", title_x, title_y, self.scale, angle=10)

        fan = [
            ("2♦", W // 2 - self.S(195), self.SY(260), self.S(90),  self.S(135), 25),
            ("2♣", W // 2 - self.S(130), self.SY(220), self.S(112), self.S(165), 10),
            ("2♥", W // 2 - self.S(45),  self.SY(195), self.S(135), self.S(195), 1),
            ("2♠", W // 2 + self.S(55),  self.SY(195), self.S(157), self.S(225), -15),
        ]

        for label, fx, fy, w, h, angle in fan:
            draw_rotated_face(s, self.fonts, fx, fy, w, h, label, angle=angle)

        bw = self.S(280)
        bh = self.S(56)
        self.b_start.r = self.S(28)
        self.b_start.move(W // 2 - bw // 2, H - self.SY(170), bw, bh)

        if pygame.time.get_ticks() - self.start_anim_ms > 900:
            t = pygame.time.get_ticks()

            # Fade in / fade out blink
            blink = (math.sin(t * 0.005) + 1) / 2
            alpha = int(45 + 210 * blink)

            # Tiny floating motion
            y_offset = int(2 * math.sin(t * 0.003))

            txt = self.fonts["hint"].render("Tap to start", True, (220, 200, 120))
            txt.set_alpha(alpha)

            rect = txt.get_rect(center=(W // 2, H - self.SY(190) + y_offset))
            s.blit(txt, rect)

        self.b_start.draw(s, self.fonts, glow=True, scale=self.scale)

        bottom_y = H - self.SY(65)
        self.bottom_icon_rects = {
            "achievements": self._draw_bottom_icon("achievements", W // 2 - self.SX(170), bottom_y, "trophy", "ACHIEVEMENTS"),
            "settings": self._draw_bottom_icon("settings", W // 2, bottom_y, "gear", "SETTINGS"),
            "how_to_play": self._draw_bottom_icon("how_to_play", W // 2 + self.SX(170), bottom_y, "?", "HOW TO PLAY"),
        }

    # MENU PAGES
    def _ev_how_to_play(self, e):
        if self.b_back.clicked(e):
            self.state = "start"
            self.start_anim_ms = pygame.time.get_ticks()

    def _ev_settings(self, e):
        if self.b_back.clicked(e):
            self.state = "start"
            self.start_anim_ms = pygame.time.get_ticks()

    def _ev_achievements(self, e):
        if self.b_back.clicked(e):
            self.state = "start"
            self.start_anim_ms = pygame.time.get_ticks()

    def _draw_page_frame(self, title):
        W, H = self.W, self.H
        s = self.screen
        self._draw_table_gradient()

        self.b_back.r = self.S(8)
        self.b_back.move(self.SX(16), self.SY(12), self.S(52), self.S(38))
        self.b_back.draw(s, self.fonts, scale=self.scale)

        panel_w = min(self.S(760), W - self.S(120))
        panel_h = min(self.S(486), H - self.S(82))
        panel = pygame.Rect(W // 2 - panel_w // 2, H // 2 - panel_h // 2 + self.S(8), panel_w, panel_h)

        glow = pygame.Surface((panel.w + self.S(48), panel.h + self.S(48)), pygame.SRCALPHA)
        pygame.draw.rect(
            glow,
            (255, 205, 70, 38),
            (self.S(24), self.S(24), panel.w, panel.h),
            border_radius=self.S(26)
        )
        s.blit(glow, (panel.x - self.S(24), panel.y - self.S(24)))

        rrect(s, C_PANEL_BG, panel, r=self.S(20), bw=self.S(3), bc=C_RING)

        inner = panel.inflate(-self.S(16), -self.S(16))
        pygame.draw.rect(
            s,
            (255, 220, 120),
            inner,
            max(1, self.S(1)),
            border_radius=self.S(16)
        )

        blit_text(s, title, self.fonts["title2"], C_GOLD, W // 2, panel.y + self.S(48), anchor="center")
        return panel

    def _draw_section_header(self, surf, number, title, x, y, w):
        badge_r = self.S(17)
        badge_cx = x + badge_r
        badge_cy = y + badge_r

        pygame.draw.circle(surf, (42, 24, 8), (badge_cx, badge_cy), badge_r)
        pygame.draw.circle(surf, C_GOLD, (badge_cx, badge_cy), badge_r, max(2, self.S(2)))
        blit_text(surf, str(number), self.fonts["bodyb"], C_GOLD, badge_cx, badge_cy, anchor="center")

        # Start the title bar after the circle badge so they do not overlap.
        banner_x = x + badge_r * 2 + self.S(10)
        banner = pygame.Rect(banner_x, y + self.S(3), max(self.S(80), w - (banner_x - x)), self.S(28))
        rrect(surf, (10, 65, 35), banner, r=self.S(7), bw=self.S(2), bc=C_GOLD_DK)
        blit_text(surf, title, self.fonts["bodyb"], C_GOLD, banner.x + self.S(12), banner.centery, anchor="midleft")

    def _draw_small_card(self, surf, label, x, y, w=None, h=None):
        cw = w or self.S(34)
        ch = h or self.S(46)
        draw_face(
            surf,
            self.fonts,
            x,
            y,
            cw,
            ch,
            label,
            show_corner_suit=False,
            big_suit_scale=0.95
        )

    def _draw_tiny_card(self, surf, label, x, y, w=None, h=None):
        cw = int(w or self.S(20))
        ch = int(h or self.S(28))
        x = int(x)
        y = int(y)
        radius = max(3, int(min(cw, ch) * 0.14))

        shadow = pygame.Surface((cw + self.S(4), ch + self.S(4)), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 70), (self.S(2), self.S(2), cw, ch), border_radius=radius)
        surf.blit(shadow, (x - self.S(1), y - self.S(1)))

        rect = pygame.Rect(x, y, cw, ch)
        pygame.draw.rect(surf, C_CARD_BG, rect, border_radius=radius)
        pygame.draw.rect(surf, (110, 95, 80), rect, max(1, self.S(1)), border_radius=radius)

        rank = label[:-1]
        suit = label[-1]
        col = suit_col(label)

        rank_size = max(8, int(13 * self.scale))
        suit_size = max(9, int(14 * self.scale))
        rank_font = pygame.font.SysFont("Cooper black", rank_size, bold=False)
        suit_font = pygame.font.SysFont("Times New Roman", suit_size, bold=False)

        rank_img = rank_font.render(rank, True, col)
        suit_img = suit_font.render(suit, True, col)

        surf.blit(rank_img, rank_img.get_rect(center=(rect.centerx, rect.y + ch * 0.34)))
        surf.blit(suit_img, suit_img.get_rect(center=(rect.centerx, rect.y + ch * 0.68)))

    def _draw_bulb_icon(self, surf, cx, cy, size=None):
        size = int(size or self.S(16))
        glass_r = max(6, int(size * 0.44))
        top_y = cy - int(size * 0.12)

        pygame.draw.circle(surf, (255, 218, 90), (cx, top_y), glass_r)
        pygame.draw.circle(surf, C_GOLD, (cx, top_y), glass_r, max(1, self.S(2)))

        neck_w = max(6, int(size * 0.40))
        neck_h = max(4, int(size * 0.18))
        neck = pygame.Rect(cx - neck_w // 2, top_y + glass_r - self.S(1), neck_w, neck_h)
        rrect(surf, (206, 160, 54), neck, r=max(2, self.S(2)), bw=0)

        base_w = max(8, int(size * 0.52))
        base_h = max(4, int(size * 0.20))
        base = pygame.Rect(cx - base_w // 2, neck.bottom - self.S(1), base_w, base_h)
        rrect(surf, (108, 74, 24), base, r=max(2, self.S(2)), bw=0)

        ray_len = max(4, int(size * 0.22))
        for dx, dy in ((0, -1), (-1, -1), (1, -1), (-1, 0), (1, 0)):
            x1 = cx + dx * (glass_r + self.S(2))
            y1 = top_y + dy * (glass_r + self.S(2))
            x2 = cx + dx * (glass_r + ray_len)
            y2 = top_y + dy * (glass_r + ray_len)
            pygame.draw.line(surf, (255, 226, 120), (x1, y1), (x2, y2), max(1, self.S(2)))

    def _draw_trophy_icon(self, surf, cx, cy, size=None):
        size = int(size or self.S(24))
        gold = C_GOLD
        dark = (42, 24, 8)

        cup_w = max(12, int(size * 0.78))
        cup_h = max(10, int(size * 0.48))
        cup = pygame.Rect(cx - cup_w // 2, cy - int(size * 0.28), cup_w, cup_h)

        # Cup body
        pygame.draw.rect(surf, gold, cup, border_radius=max(3, self.S(4)))
        pygame.draw.rect(surf, dark, cup, max(1, self.S(2)), border_radius=max(3, self.S(4)))

        # Handles
        handle_w = max(5, int(size * 0.24))
        handle_h = max(7, int(size * 0.34))
        left_handle = pygame.Rect(cup.x - handle_w + self.S(2), cup.y + self.S(3), handle_w, handle_h)
        right_handle = pygame.Rect(cup.right - self.S(2), cup.y + self.S(3), handle_w, handle_h)
        pygame.draw.arc(surf, gold, left_handle, 1.35, 4.9, max(2, self.S(3)))
        pygame.draw.arc(surf, gold, right_handle, -1.75, 1.8, max(2, self.S(3)))

        # Stem and base
        stem_w = max(5, int(size * 0.20))
        stem_h = max(5, int(size * 0.22))
        stem = pygame.Rect(cx - stem_w // 2, cup.bottom - self.S(1), stem_w, stem_h)
        pygame.draw.rect(surf, gold, stem, border_radius=max(2, self.S(2)))

        base_w = max(12, int(size * 0.68))
        base_h = max(4, int(size * 0.18))
        base = pygame.Rect(cx - base_w // 2, stem.bottom - self.S(1), base_w, base_h)
        pygame.draw.rect(surf, gold, base, border_radius=max(2, self.S(2)))
        pygame.draw.rect(surf, dark, base, max(1, self.S(1)), border_radius=max(2, self.S(2)))

        # Highlight
        pygame.draw.line(
            surf,
            (255, 230, 140),
            (cup.x + self.S(5), cup.y + self.S(4)),
            (cup.x + self.S(5), cup.bottom - self.S(5)),
            max(1, self.S(2))
        )

    def _draw_how_to_play(self):
        W, H = self.W, self.H
        s = self.screen
        panel = self._draw_page_frame("HOW TO PLAY")

        margin_x = self.S(36)
        gap_x = self.S(24)
        gap_y = self.S(14)
        box_w = (panel.w - margin_x * 2 - gap_x) // 2
        box_h = self.S(150)

        left_x = panel.x + margin_x
        right_x = left_x + box_w + gap_x
        top_y = panel.y + self.S(96)

        basics = pygame.Rect(left_x, top_y, box_w, box_h)
        hand_types = pygame.Rect(right_x, top_y, box_w, box_h)
        controls = pygame.Rect(left_x, top_y + box_h + gap_y, box_w, box_h)
        scoring = pygame.Rect(right_x, top_y + box_h + gap_y, box_w, box_h)

        for rect in (basics, hand_types, controls, scoring):
            rrect(s, (6, 30, 20), rect, r=self.S(12), bw=self.S(2), bc=C_GOLD_DK)

        self._draw_section_header(s, 1, "BASICS", basics.x + self.S(12), basics.y + self.S(10), basics.w - self.S(24))
        self._draw_small_card(s, "3♦", basics.x + self.S(22), basics.y + self.S(65), self.S(48), self.S(66))

        bullets = [
            "3 of Diamonds starts the round.",
            "Play a higher same-type hand.",
            "Pass if you cannot play.",
            "In 2-3 players, pass = draw 1 card.",
        ]
        by = basics.y + self.S(60)
        bullet_x = basics.x + self.S(92)
        text_x = basics.x + self.S(106)
        for i, line in enumerate(bullets):
            yy = by + i * self.S(22)
            pygame.draw.circle(s, C_GOLD, (bullet_x, yy), max(2, self.S(3)))
            blit_text(s, line, self.fonts["sm"], C_TXT_LIGHT, text_x, yy, anchor="midleft")

        self._draw_section_header(s, 2, "HAND TYPES", hand_types.x + self.S(12), hand_types.y + self.S(10), hand_types.w - self.S(24))

        examples = [
            ("Single", ["7♠"]),
            ("Pair", ["Q♣", "Q♥"]),
            ("Triple", ["9♠", "9♦", "9♣"]),
            ("Straight", ["5♥", "6♣", "7♦", "8♠", "9♥"]),
            ("Flush", ["K♥", "8♥", "6♥", "4♥", "2♥"]),
            ("Full House", ["J♦", "J♣", "J♥", "5♣", "5♥"]),
            ("Four Kind", ["A♥", "A♦", "A♣", "A♠", "3♥"]),
            ("Str. Flush", ["10♣", "J♣", "Q♣", "K♣", "A♣"]),
        ]

        grid_x = hand_types.x + self.S(14)
        grid_y = hand_types.y + self.S(56)
        cell_w = (hand_types.w - self.S(28)) // 4
        cell_h = self.S(50)

        for i, (label, cards) in enumerate(examples):
            col = i % 4
            row = i // 4
            cx = grid_x + col * cell_w + cell_w // 2
            y = grid_y + row * cell_h

            blit_text(s, label, self.fonts["sm"], C_GOLD, cx, y, anchor="center")

            card_w = self.S(18)
            card_h = self.S(25)
            spread = self.S(11)
            total = spread * (len(cards) - 1) + card_w
            sx = cx - total // 2
            for j, card in enumerate(cards):
                self._draw_tiny_card(s, card, sx + j * spread, y + self.S(12), card_w, card_h)

        self._draw_section_header(s, 3, "CONTROLS", controls.x + self.S(12), controls.y + self.S(10), controls.w - self.S(24))
        control_buttons = [
            ("PLAY", C_BTN_GOLD, C_GOLD),
            ("PASS", C_BTN_GREEN, C_WHITE),
            ("RESET", C_BTN_GREY, C_WHITE),
        ]

        btn_w = self.S(78)
        btn_h = self.S(36)
        btn_gap = self.S(18)
        total_btn_w = btn_w * 3 + btn_gap * 2
        start_x = controls.centerx - total_btn_w // 2
        btn_y = controls.y + self.S(72)

        for i, (label, color, text_col) in enumerate(control_buttons):
            btn = pygame.Rect(start_x + i * (btn_w + btn_gap), btn_y, btn_w, btn_h)
            rrect(s, color, btn, r=self.S(8), bw=self.S(2), bc=C_GOLD)
            inner = btn.inflate(-self.S(6), -self.S(6))
            pygame.draw.rect(s, (255, 220, 120), inner, max(1, self.S(1)), border_radius=self.S(6))
            blit_text(s, label, self.fonts["h3"], text_col, btn.centerx, btn.centery, anchor="center")

        self._draw_section_header(s, 4, "SCORING", scoring.x + self.S(12), scoring.y + self.S(10), scoring.w - self.S(24))
        scoring_lines = [
            "3-9 = 1 point each",
            "10, J, Q, K, A = 2 points each",
            "More than 10 cards: count x2",
            "Any 2 doubles the total",
            "First to 150 points ends the game",
        ]

        sy = scoring.y + self.S(59)
        for i, line in enumerate(scoring_lines):
            yy = sy + i * self.S(18)
            pygame.draw.circle(s, C_GOLD, (scoring.x + self.S(24), yy), max(2, self.S(3)))
            blit_text(s, line, self.fonts["sm"], C_TXT_LIGHT, scoring.x + self.S(38), yy, anchor="midleft")

        tip_text = "Tip: Use your brain"
        tip_font = self.fonts["sm"]
        text_w = tip_font.size(tip_text)[0]
        tip_h = self.S(30)
        pad_x = self.S(22)
        icon_block = self.S(30)
        tip_w = text_w + pad_x * 2 + icon_block
        tip_rect = pygame.Rect(panel.centerx - tip_w // 2, panel.bottom - self.S(58), tip_w, tip_h)
        rrect(s, (6, 30, 20), tip_rect, r=self.S(12), bw=self.S(2), bc=C_GOLD_DK)

        icon_x = tip_rect.x + self.S(18)
        self._draw_bulb_icon(s, icon_x, tip_rect.centery - self.S(1), self.S(15))
        blit_text(s, tip_text, tip_font, C_GOLD, icon_x + self.S(20), tip_rect.centery, anchor="midleft")

    def _draw_settings(self):
        W, H = self.W, self.H
        s = self.screen
        panel = self._draw_page_frame("SETTINGS")

        items = [
            ("Animation Speed", "Normal"),
            ("Sound Effects", "Coming Soon"),
            ("Music", "Coming Soon"),
            ("Fullscreen", "Use the window button"),
            ("Card Size", "Default"),
        ]

        start_y = panel.y + self.S(140)
        row_w = min(self.S(520), panel.w - self.S(120))
        row_x = panel.centerx - row_w // 2

        for i, (name, value) in enumerate(items):
            row = pygame.Rect(row_x, start_y + i * self.S(50), row_w, self.S(38))
            rrect(s, (6, 30, 20), row, r=self.S(10), bw=self.S(2), bc=C_GOLD_DK)
            blit_text(s, name, self.fonts["bodyb"], C_TXT_LIGHT, row.x + self.S(18), row.centery, anchor="midleft")
            blit_text(s, value, self.fonts["sm"], C_GOLD, row.right - self.S(18), row.centery, anchor="midright")

        blit_text(s, "More settings can be connected later.", self.fonts["sm"], C_TXT_MUTED, panel.centerx, panel.bottom - self.S(42), anchor="center")

    def _draw_achievements(self):
        W, H = self.W, self.H
        s = self.screen
        panel = self._draw_page_frame("ACHIEVEMENTS")

        achievements = [
            ("First Win", "Win your first match."),
            ("Fast Finish", "Win a round with 5 or fewer cards left."),
            ("No Mercy", "Win without passing."),
            ("Diamond Start", "Start with 3♦ and win the round."),
            ("Comeback", "Win after trailing in score."),
            ("Big Two Master", "Win 10 matches."),
        ]

        start_y = panel.y + self.S(132)
        col_w = (panel.w - self.S(120)) // 2
        for i, (title, desc) in enumerate(achievements):
            col = i % 2
            row = i // 2
            x = panel.x + self.S(52) + col * (col_w + self.S(20))
            y = start_y + row * self.S(86)
            card = pygame.Rect(x, y, col_w, self.S(66))
            rrect(s, (6, 30, 20), card, r=self.S(12), bw=self.S(2), bc=C_GOLD_DK)
            pygame.draw.circle(s, (42, 24, 8), (card.x + self.S(28), card.centery), self.S(17))
            pygame.draw.circle(s, C_GOLD_DK, (card.x + self.S(28), card.centery), self.S(17), max(2, self.S(2)))
            self._draw_trophy_icon(s, card.x + self.S(28), card.centery, self.S(24))
            blit_text(s, title, self.fonts["bodyb"], C_GOLD, card.x + self.S(58), card.y + self.S(18), anchor="midleft")
            blit_text(s, desc, self.fonts["sm"], C_TXT_LIGHT, card.x + self.S(58), card.y + self.S(42), anchor="midleft")

        blit_text(s, "Achievement tracking can be saved later.", self.fonts["sm"], C_TXT_MUTED, panel.centerx, panel.bottom - self.S(38), anchor="center")

    # SELECT
    def _ev_select(self, e):
        if self.b_back_sel.clicked(e):
            self.state = "start"
            self.start_anim_ms = pygame.time.get_ticks()
        if self.b_2p.clicked(e):
            self.player_count = 2
        if self.b_3p.clicked(e):
            self.player_count = 3
        if self.b_4p.clicked(e):
            self.player_count = 4
        if self.b_confirm.clicked(e):
            self._start_game()

    def _draw_select(self):
        W, H = self.W, self.H
        s = self.screen

        # Keep the same background as cover, but only redraw this page layout
        self._draw_start_gradient()

        # Back button
        self.b_back_sel.r = self.S(8)
        self.b_back_sel.move(self.SX(20), self.SY(16), self.S(56), self.S(42))
        self.b_back_sel.draw(s, self.fonts, scale=self.scale)

        # Header
        #draw_game_logo(s, self.fonts["title2"], "BIG 2", W // 2, self.SY(80), self.scale * 0.72, angle=5)
        blit_text(s, "SELECT PLAYERS", self.fonts["h2"], C_WHITE, W // 2, self.SY(150), anchor="center")
        blit_text(s, "Pick how many players", self.fonts["hint1"], (220, 200, 120), W // 2, self.SY(190), anchor="center")

        cfgs = [(2, self.b_2p), (3, self.b_3p), (4, self.b_4p)]
        gap = self.SX(218)
        bx = W // 2 - gap
        by = self.SY(230)

        mouse = pygame.mouse.get_pos()

        for idx, (count, btn) in enumerate(cfgs):
            bw = self.S(178)
            bh = self.S(134)
            x = bx + idx * gap - bw // 2

            btn.r = self.S(18)
            btn.move(x, by, bw, bh)

            active = (self.player_count == count)
            hovered = btn.rect.collidepoint(mouse)

            # visual card rect, not changing click rect
            card_rect = btn.rect.copy()
            if active:
                card_rect.inflate_ip(self.S(8), self.S(8))
            elif hovered:
                card_rect.inflate_ip(self.S(4), self.S(4))

            bg_col = (62, 24, 18) if active else (38, 15, 12)
            bd_col = C_GOLD if active else (105, 78, 28)

            # glow
            if active or hovered:
                glow = pygame.Surface((card_rect.w + self.S(30), card_rect.h + self.S(30)), pygame.SRCALPHA)
                glow_alpha = 75 if active else 35
                pygame.draw.rect(
                    glow,
                    (255, 205, 70, glow_alpha),
                    (self.S(15), self.S(15), card_rect.w, card_rect.h),
                    border_radius=self.S(22)
                )
                s.blit(glow, (card_rect.x - self.S(15), card_rect.y - self.S(15)))

            # card body
            rrect(s, bg_col, card_rect, r=self.S(18))
            rrect(s, bg_col, card_rect, r=self.S(18), bw=self.S(3), bc=bd_col)

            # inner border
            inner = card_rect.inflate(-self.S(12), -self.S(12))
            pygame.draw.rect(
                s,
                (255, 220, 120, 60 if active else 28),
                inner,
                max(1, self.S(1)),
                border_radius=self.S(14)
            )

            mx = card_rect.centerx
            top = card_rect.top

            # big number
            blit_text(s, str(count), self.fonts["title2"], (45, 14, 6), mx + self.S(2), top + self.S(43), anchor="center")
            blit_text(s, str(count), self.fonts["title2"], C_GOLD, mx, top + self.S(40), anchor="center")

            blit_text(s, "PLAYERS", self.fonts["h3"], C_WHITE, mx, top + self.S(90), anchor="center")

            # pips
            pip_y = top + self.S(112)
            pip_gap = self.S(22)
            start_x = mx - pip_gap * (count - 1) // 2
            for i in range(count):
                px = start_x + i * pip_gap
                pygame.draw.circle(s, (42, 24, 8), (px, pip_y), self.S(7))
                pygame.draw.circle(s, C_GOLD, (px, pip_y), self.S(7), max(1, self.S(2)))

            if active:
                blit_text(s, "SELECTED", self.fonts["h3"], (220, 200, 120), mx, card_rect.bottom + self.S(18), anchor="center")

        # Confirm button
        bw = self.S(230)
        bh = self.S(50)
        self.b_confirm.r = self.S(26)
        self.b_confirm.fk = "start"
        self.b_confirm.bg = C_BTN_GOLD
        self.b_confirm.fg = C_GOLD
        self.b_confirm.move(W // 2 - bw // 2, H - self.SY(160), bw, bh)
        self.b_confirm.draw(s, self.fonts, glow=True, scale=self.scale)

    # GAME INIT
    def _start_game(self):
        self.players = [Player("You", is_human=True)]
        for i in range(1, self.player_count):
            self.players.append(Player(f"Player {i}"))

        self.game = Game(self.players)
        self.game.deal_new_round()
        self.selected = []
        self.messages = [f"Round {self.game.round_number} started"]
        self.round_result = None
        self.round_result_ms = 0
        self.game_result = None
        self.game_result_ready = False
        self.game_result_delay_ms = 0
        self.ai_wait_ms = 0
        self.fly_cards = []
        self.action_msg = ""
        self.action_msg_owner = ""
        self.action_msg_ms = 0
        self.state = "game"

        opening_msg, opening_owner = self._opening_action_message()
        self.pending_opening_msg = opening_msg
        self.pending_opening_owner = opening_owner
        self._queue_round_deal_animation(f"ROUND {self.game.round_number}")

    def _queue_round_deal_animation(self, banner_text=""):
        if not self.players:
            return

        self.fly_cards = []
        self.dealing_locked = True
        self.ai_wait_ms = 0
        self.deal_banner_text = banner_text
        self.deal_banner_ms = 1500 if banner_text else 0
        self.deal_deck_remaining = 52

        order = [p.name for p in self.players]
        cards_each = 13
        leftover_count = len(self.game.draw_pile) if self.game else max(0, 52 - len(order) * cards_each)

        start_delay = 750 if banner_text else 250
        step = 70
        duration = 430
        idx = 0

        start_x = self.W // 2 - self.S(24)
        start_y = self.H // 2 - self.S(48)

        for _ in range(cards_each):
            for name in order:
                end_x, end_y = self._seat_target_pos(name)
                self.fly_cards.append({
                    "kind": "deal",
                    "sx": start_x,
                    "sy": start_y,
                    "ex": end_x,
                    "ey": end_y,
                    "t": 0,
                    "delay": start_delay + idx * step,
                    "duration": duration,
                    "started": False,
                })
                idx += 1

        draw_x, draw_y = self._draw_pile_target_pos()
        for _ in range(leftover_count):
            self.fly_cards.append({
                "kind": "deal",
                "sx": start_x,
                "sy": start_y,
                "ex": draw_x,
                "ey": draw_y,
                "t": 0,
                "delay": start_delay + idx * step,
                "duration": duration,
                "started": False,
            })
            idx += 1

        self.deal_finish_ms = start_delay + max(0, idx - 1) * step + duration + 260
        self.deal_total_ms = self.deal_finish_ms

    def _after_deal_animation(self):
        if not self.game or self.game.game_over:
            return

        self._log(f"Round {self.game.round_number} started")

        if self.pending_opening_msg:
            self._set_action_message(self.pending_opening_msg, self.pending_opening_owner)

        self.pending_opening_msg = ""
        self.pending_opening_owner = ""
        self._run_ai()

    def _announce_table_reset(self, delay_ms=0):
        if not self.game:
            return

        # Do not show "All players passed".
        # After everyone passes, keep the last "PlayerX passed" visible briefly,
        # then show who gets to lead the next table.
        cur = self.game.get_current_player()
        if not cur:
            return

        if cur.is_human:
            msg = "Your turn"
            owner = "You"
        else:
            display = self._player_display_name(cur.name)
            msg = f"{display}'s turn"
            owner = cur.name

        self.game.status_message = msg
        if delay_ms > 0:
            self._queue_action_message(msg, owner, delay_ms)
        else:
            self._log(msg)
            self._set_action_message(msg, owner)

    # GAME EVENTS
    def _ev_game(self, e):
        if self.b_back.clicked(e):
            self.state = "select"
            return

        if self.b_new.clicked(e):
            self.state = "start"
            self.start_anim_ms = pygame.time.get_ticks()
            return

        if self.game_result:
            if self.game_result_ready and self.b_again.clicked(e):
                self._start_game()
                return
            if self.game_result_ready and self.b_end.clicked(e):
                self.state = "start"
                self.start_anim_ms = pygame.time.get_ticks()
                return
            return

        if self.round_result:
            if (not self.round_result_countdown_active) and self.b_round_next.clicked(e):
                self.round_result_countdown_active = True
                self.round_result_ms = self.round_result_duration
            return

        cur = self.game.get_current_player()
        human_turn = (
            cur.is_human
            and not self.game.game_over
            and not self.dealing_locked
            and self.ai_wait_ms <= 0
        )

        if self.b_play.clicked(e) and human_turn:
            self._do_play()
        if self.b_pass.clicked(e) and human_turn:
            self._do_pass()
        if self.b_clr.clicked(e) and human_turn:
            self.selected = []

        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and human_turn:
            for rect, card in self.hand_rects:
                if rect.collidepoint(e.pos):
                    if card in self.selected:
                        self.selected.remove(card)
                    else:
                        self.selected.append(card)
                    self.selected.sort(key=lambda c: c.sort_key())
                    break

    def _do_play(self):
        played_cards = list(self.selected)
        ok, msg = self.game.play_selected_cards(played_cards)
        if not ok:
            self._notice(f"Invalid: {msg}")
            return

        # Immediately replace the opening/start message with the actual play
        # message, so the narration always matches what is currently on the table.
        if played_cards:
            cards_txt = " ".join(str(card) for card in played_cards)
            self._set_action_message(f"You played {cards_txt}", "You")

        self._log(self.game.status_message or "Played.")
        self.selected = []

        if msg == "round_end":
            self._round_end()
            return

        self._run_ai()

    def _do_pass(self):
        before_counts = self._hand_counts()

        ok, msg = self.game.pass_current_turn()
        if not ok:
            self._notice(f"Cannot pass: {msg}")
            return

        # Always show pass narration. In 4-player mode the draw pile can be empty,
        # so count-based draw animation would not create a pass message by itself.
        self._set_action_message("You passed", "You")
        self._trigger_draw_animations_from_counts(before_counts, show_notice=True)

        status_text = self.game.status_message or "Passed."
        if "All other players passed" in status_text:
            self._announce_table_reset(delay_ms=900)
        else:
            self._log(status_text)

        self.selected = []
        self._run_ai()

    def _next_ai_delay_ms(self):
        return random.randint(self.ai_turn_delay_min_ms, self.ai_turn_delay_max_ms)

    def _run_ai(self):
        """
        Schedule AI turns one by one instead of running all AI players instantly.
        This lets 3-player and 4-player games show each AI action clearly.
        """
        if not self.game or self.game.game_over or self.game.round_winner or self.dealing_locked:
            return

        cur = self.game.get_current_player()
        if cur.is_human:
            self.ai_wait_ms = 0
            self._log("Your turn")
            return

        self.ai_wait_ms = self._next_ai_delay_ms() + max(0, self.pending_action_ms)

    def _schedule_next_ai_turn(self):
        if not self.game or self.game.game_over or self.game.round_winner or self.dealing_locked:
            self.ai_wait_ms = 0
            return

        cur = self.game.get_current_player()
        if cur.is_human:
            self.ai_wait_ms = 0
            self._log("Your turn")
        else:
            self.ai_wait_ms = self._next_ai_delay_ms() + max(0, self.pending_action_ms)

    def _process_ai_turn(self):
        if not self.game or self.game.game_over or self.game.round_winner:
            self.ai_wait_ms = 0
            return

        player = self.game.get_current_player()
        if player.is_human:
            self.ai_wait_ms = 0
            self._log("Your turn")
            return

        playable = self.game.find_playable_cards(player)

        if playable:
            player.remove_cards(playable)
            self.game.current_table = playable
            self.game.last_player_index = self.game.current_player_index
            self.game.pass_count = 0

            cards_txt = " ".join(str(card) for card in playable)
            display = self._player_display_name(player.name)
            msg = f"{display} played {cards_txt}"

            self.game.status_message = msg + "."
            self._log(self.game.status_message)
            self._set_action_message(msg, player.name)

            if player.has_no_cards():
                self.game.round_winner = player
                self.ai_wait_ms = 0
                self._round_end()
                return

            self.game.next_player()
            self._schedule_next_ai_turn()
            return

        if not self.game.current_table:
            display = self._player_display_name(player.name)
            msg = f"{display} could not make a move"
            self.game.status_message = msg + "."
            self._log(self.game.status_message)
            self._set_action_message(msg, player.name)
            self.game.next_player()
            self._schedule_next_ai_turn()
            return

        before_counts = self._hand_counts()
        drawn_card = self.game.draw_one_card(player)
        self.game.pass_count += 1

        display = self._player_display_name(player.name)
        pass_msg = f"{display} passed"
        if drawn_card:
            # Keep pass narration simple and do not reveal the hidden drawn card.
            self.game.status_message = f"{display} passed."
        else:
            self.game.status_message = f"{display} passed."

        self._log(self.game.status_message)
        self._set_action_message(pass_msg, player.name)
        self._trigger_draw_animations_from_counts(before_counts, show_notice=True)

        self.game.next_player()

        if self.game.pass_count >= len(self.players) - 1:
            self.game.current_table = []
            self.game.pass_count = 0
            self.game.current_player_index = self.game.last_player_index

            # Keep "PlayerX passed" visible first, then show who starts next.
            self._announce_table_reset(delay_ms=900)
            cur = self.game.get_current_player()
            if cur and not cur.is_human:
                self.ai_wait_ms = 900 + self._next_ai_delay_ms()
            else:
                self.ai_wait_ms = 0
            return

        self._schedule_next_ai_turn()

    def _round_end(self):
        winner = self.game.round_winner.name
        self._log(f">> {winner} won the round!")

        results = self.game.end_round_and_prepare_next()
        if results:
            for r in results:
                self._log(f"{r['name']}: +{r['round_penalty']} | Total {r['total_score']}")

        self.selected = []
        self.action_msg = ""
        self.action_msg_owner = ""
        self.action_msg_ms = 0

        if self.game.game_over:
            self._game_over(results or [], winner)
        else:
            self._set_round_result(winner, results or [])

    def _set_round_result(self, winner_name, results):
        loser_rows = []
        for r in results:
            penalty = r.get("round_penalty", 0)
            if penalty > 0:
                loser_rows.append({
                    "name": r.get("name", ""),
                    "penalty": penalty,
                    "total": r.get("total_score", 0),
                })

        self.round_result = {
            "winner": winner_name,
            "losers": loser_rows,
        }
        self.round_result_ms = self.round_result_duration
        self.round_result_countdown_active = False

    def _set_game_result(self, results, winner_name=""):
        rows = []
        for r in results:
            rows.append({
                "name": r.get("name", ""),
                "penalty": r.get("round_penalty", 0),
                "total": r.get("total_score", 0),
            })

        if not rows:
            for p in self.players:
                rows.append({
                    "name": p.name,
                    "penalty": 0,
                    "total": getattr(p, "total_score", getattr(p, "score", 0)),
                })

        rows.sort(key=lambda row: row["total"])

        loser_name = self.game.match_loser.name if self.game and self.game.match_loser else ""
        self.game_result = {
            "winner": winner_name,
            "loser": loser_name,
            "rows": rows,
        }

    def _finish_round_result(self):
        if not self.round_result:
            return

        self.round_result = None
        self.round_result_ms = 0
        self.round_result_countdown_active = False

        if not self.game or self.game.game_over:
            return

        self.action_msg = ""
        self.action_msg_owner = ""
        self.action_msg_ms = 0

        opening_msg, opening_owner = self._opening_action_message()
        self.pending_opening_msg = opening_msg
        self.pending_opening_owner = opening_owner
        # The explosion already shows the NEXT ROUND teaser, so start dealing
        # directly without a second NEXT ROUND banner.
        self._queue_round_deal_animation("")

    def _game_over(self, results=None, winner_name=""):
        if self.game.match_loser:
            self._log(f"GAME OVER - {self.game.match_loser.name} reached 150 pts")

            self.round_result = None
            self.round_result_ms = 0
            self.round_result_countdown_active = False
            self.action_msg = ""
            self.action_msg_owner = ""
            self.action_msg_ms = 0

            self._set_game_result(results or [], winner_name)

            if self.game.match_loser.is_human:
                self._set_result_banner("YOU LOST!", "lose")
                self.game_result_ready = False
                self.game_result_delay_ms = self.result_banner_duration
            else:
                self._set_result_banner("YOU WIN!", "win")
                self.game_result_ready = False
                self.game_result_delay_ms = self.result_banner_duration

    def _log(self, txt):
        if txt:
            self.messages.append(txt)
            if len(self.messages) > 8:
                self.messages = self.messages[-8:]

    def _notice(self, txt, ms=2000):
        # Game-screen notices should use the same centre narration style
        # as player actions, instead of appearing at the top of the window.
        if self.state == "game" and self.game:
            owner = ""
            try:
                cur = self.game.get_current_player()
                if cur:
                    owner = "You" if cur.is_human else cur.name
            except Exception:
                owner = "You"

            self.notice_txt = ""
            self.notice_ms = 0
            self._set_action_message(txt, owner or "You")
            return

        self.notice_txt = txt
        self.notice_ms = ms

    def _player_display_name(self, name):
        if name.startswith("Player "):
            return name.replace("Player ", "Player")
        return name

    def _player_badge_label(self, name):
        if name.startswith("Player "):
            return "P" + name.split()[-1]
        if name == "You":
            return "Y"
        return str(name)[0].upper()

    def _is_opening_action_message(self, msg):
        # Opening narration such as "Player2 has 3♦. Player2 starts"
        # should stay in the normal centre/top position.
        if not msg:
            return False
        return ("has 3♦" in msg) or msg.endswith("starts") or msg.endswith("start")

    def _player_has_card(self, player, card_text):
        return any(str(card) == card_text for card in player.hand)

    def _opening_action_message(self):
        if not self.game:
            return "", ""

        cur = self.game.get_current_player()

        for p in self.players:
            if self._player_has_card(p, "3♦"):
                display = self._player_display_name(p.name)
                if p.is_human:
                    return "You have 3♦. You start", "You"
                return f"{display} has 3♦. {display} starts", p.name

        if cur:
            display = self._player_display_name(cur.name)
            if cur.is_human:
                return "You start", "You"
            return f"{display} starts", cur.name

        return "", ""

    def _seat_target_pos(self, player_name):
        tcx = self.W // 2
        tcy = self.H // 2
        table_h = self.S(310)
        tr = table_h // 2

        if player_name == "You":
            return tcx - self.S(20), self.H - self.SY(170)

        if self.player_count == 2:
            return tcx - self.S(25), tcy - tr - self.S(20)

        if self.player_count == 3:
            if player_name == "Player 1":
                return tcx - self.SX(145), tcy - self.S(180)
            return tcx + self.SX(145), tcy - self.S(180)

        if self.player_count == 4:
            # 4-player layout: make the opponents feel more rectangular around the table.
            # Player 1 = left side, Player 2 = top side, Player 3 = right side.
            if player_name == "Player 1":
                return tcx - self.SX(255), tcy - self.S(10)
            if player_name == "Player 2":
                return tcx - self.S(25), tcy - tr - self.S(45)
            return tcx + self.SX(220), tcy - self.S(10)

        return tcx, tcy

    def _draw_pile_target_pos(self):
        return self.SX(110), self.SY(285)

    def _add_draw_animation(self, player_name):
        start_x = self.SX(110)
        start_y = self.SY(285)
        end_x, end_y = self._seat_target_pos(player_name)

        self.fly_cards.append({
            "sx": start_x,
            "sy": start_y,
            "ex": end_x,
            "ey": end_y,
            "t": 0,
            "duration": 550,
        })

    def _hand_counts(self):
        return {p.name: len(p.hand) for p in self.players}

    def _trigger_draw_animations_from_counts(self, before_counts, show_notice=False):
        for p in self.players:
            before = before_counts.get(p.name, len(p.hand))
            gained = len(p.hand) - before
            if gained > 0:
                display = self._player_display_name(p.name)
                msg = f"{display} passed"
                self._log(msg)
                self._set_action_message(msg, p.name)
                for _ in range(gained):
                    self._add_draw_animation(p.name)

    def _set_action_message(self, msg, owner_name):
        self.action_msg = msg
        self.action_msg_owner = owner_name
        self.action_msg_ms = self.action_msg_duration

    def _queue_action_message(self, msg, owner_name, delay_ms=900):
        self.pending_action_msg = msg
        self.pending_action_owner = owner_name
        self.pending_action_ms = delay_ms

    def _set_result_banner(self, text, kind="lose"):
        self.result_banner_text = text
        self.result_banner_kind = kind
        self.result_banner_ms = self.result_banner_duration

    def _draw_fly_cards(self, surf):
        for anim in self.fly_cards:
            if anim.get("delay", 0) > 0:
                continue
            t = anim["t"] / anim["duration"]
            t = max(0, min(1, t))
            p = 1 - (1 - t) ** 3

            x = anim["sx"] + (anim["ex"] - anim["sx"]) * p
            y = anim["sy"] + (anim["ey"] - anim["sy"]) * p
            if anim.get("kind") != "deal":
                y -= math.sin(t * math.pi) * self.S(45)
            else:
                y -= math.sin(t * math.pi) * self.S(18)

            draw_back(
                surf,
                int(x),
                int(y),
                self.S(48),
                self.S(68)
            )

    def _draw_deal_banner(self, surf, W, H):
        if not self.deal_banner_text:
            return

        total_ms = 1500
        remain = max(0, min(total_ms, self.deal_banner_ms))
        progress = 1 - (remain / total_ms) if total_ms else 1.0

        # Softer pop-in and a tiny float so it feels more premium.
        scale = 0.96 + 0.20 * math.sin(min(1.0, progress * 1.15) * math.pi / 2)
        alpha = int(255 * (1 - max(0, progress - 0.78) / 0.22))
        alpha = max(0, min(255, alpha))
        float_y = int(self.S(4) * math.sin(progress * math.pi))

        txt = self.deal_banner_text.strip().upper()
        is_round = txt.startswith("ROUND")
        is_next = txt == "NEXT ROUND"

        if is_round:
            main_text = txt
            sub_text = "GET READY"
        elif is_next:
            main_text = "NEXT ROUND"
            sub_text = "AFTER BLAST"
        else:
            main_text = txt
            sub_text = ""

        # Use Cooper Black for all round-effect text.
        main_font_size = max(34, int((58 if (is_round or is_next) else 42) * self.scale * scale))
        sub_font_size = max(18, int(24 * self.scale * scale))
        main_font = pygame.font.SysFont("Cooper black", main_font_size, bold=False)
        sub_font = pygame.font.SysFont("Cooper black", sub_font_size, bold=False)

        if is_next:
            outer_fill = (82, 18, 8, min(232, alpha))
            inner_fill = (148, 42, 14, min(214, alpha))
            border_gold = (255, 204, 72, min(255, alpha))
            border_soft = (255, 238, 174, min(145, alpha))
            accent_fill = (255, 102, 24, min(105, alpha))
            glow_main = (255, 76, 18)
            glow_second = (255, 210, 72)
            main_text_col = (255, 235, 142)
            sub_text_col = (255, 248, 226)
            shadow_col = (88, 18, 8)
        else:
            outer_fill = (42, 24, 8, min(230, alpha))
            inner_fill = (82, 48, 14, min(205, alpha))
            border_gold = (241, 192, 64, min(255, alpha))
            border_soft = (255, 236, 190, min(120, alpha))
            accent_fill = (126, 65, 14, min(80, alpha))
            glow_main = (255, 205, 95)
            glow_second = (255, 236, 155)
            main_text_col = (255, 232, 162)
            sub_text_col = (240, 240, 255)
            shadow_col = (35, 16, 10)

        main_surf = main_font.render(main_text, True, main_text_col)
        sub_surf = sub_font.render(sub_text, True, sub_text_col) if sub_text else None

        pad_x = self.S(48)
        pad_y = self.S(28)
        gap_y = self.S(10)

        width = main_surf.get_width() + pad_x * 2
        if sub_surf:
            width = max(width, sub_surf.get_width() + pad_x * 2)
            height = main_surf.get_height() + sub_surf.get_height() + pad_y * 2 + gap_y
        else:
            height = main_surf.get_height() + pad_y * 2

        # Make the ROUND banner as large as the NEXT ROUND banner so the
        # opening round effect has the same visual impact.
        if is_round:
            next_probe = main_font.render("NEXT ROUND", True, main_text_col)
            width = max(width, next_probe.get_width() + pad_x * 2)

        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        rect = panel.get_rect()

        # Glow
        glow = pygame.Surface((width + self.S(56), height + self.S(56)), pygame.SRCALPHA)
        glow_rect = glow.get_rect()
        for i in range(5, 0, -1):
            g_alpha = max(8, int((alpha * 0.18) / i))
            pygame.draw.rect(
                glow,
                (*glow_main, g_alpha),
                glow_rect.inflate(-i * self.S(8), -i * self.S(8)),
                border_radius=self.S(26)
            )
        for i in range(4, 0, -1):
            g_alpha = max(8, int((alpha * 0.13) / i))
            pygame.draw.rect(
                glow,
                (*glow_second, g_alpha),
                glow_rect.inflate(-i * self.S(14), -i * self.S(14)),
                border_radius=self.S(24)
            )

        # Main panel
        pygame.draw.rect(panel, outer_fill, rect, border_radius=self.S(20))
        pygame.draw.rect(panel, inner_fill, rect.inflate(-self.S(6), -self.S(6)), border_radius=self.S(18))
        pygame.draw.rect(panel, accent_fill, rect.inflate(-self.S(12), -self.S(12)), border_radius=self.S(16))
        pygame.draw.rect(panel, border_gold, rect, self.S(2), border_radius=self.S(20))
        pygame.draw.rect(panel, border_soft, rect.inflate(-self.S(10), -self.S(10)), 1, border_radius=self.S(16))

        # Small flame strokes for NEXT ROUND.
        if is_next:
            flame_layer = pygame.Surface((width, height), pygame.SRCALPHA)
            for i in range(9):
                x = int(width * (0.13 + i * 0.095))
                base_y = height - self.S(10)
                flame_h = self.S(18 + (i % 3) * 5)
                pts = [
                    (x, base_y - flame_h),
                    (x - self.S(9), base_y),
                    (x + self.S(9), base_y),
                ]
                pygame.draw.polygon(flame_layer, (255, 118, 24, int(70 * alpha / 255)), pts)
            panel.blit(flame_layer, (0, 0))

        # Side accents
        cy = rect.centery
        pygame.draw.line(panel, border_gold, (self.S(16), cy), (self.S(34), cy), self.S(2))
        pygame.draw.line(panel, border_gold, (rect.right - self.S(34), cy), (rect.right - self.S(16), cy), self.S(2))

        # Tiny diamonds for style
        d = self.S(5)
        for x in (self.S(26), rect.right - self.S(26)):
            pts = [(x, self.S(16)), (x + d, self.S(16) + d), (x, self.S(16) + 2 * d), (x - d, self.S(16) + d)]
            pygame.draw.polygon(panel, border_gold, pts)

        # Text shadow + text
        main_shadow = main_font.render(main_text, True, shadow_col)
        main_shadow.set_alpha(min(140, alpha))
        main_y = pad_y + main_surf.get_height() // 2
        panel.blit(main_shadow, main_shadow.get_rect(center=(rect.centerx + self.S(2), main_y + self.S(2))))
        main_surf.set_alpha(alpha)
        panel.blit(main_surf, main_surf.get_rect(center=(rect.centerx, main_y)))

        if sub_surf:
            sub_shadow = sub_font.render(sub_text, True, shadow_col)
            sub_shadow.set_alpha(min(110, alpha))
            sub_y = pad_y + main_surf.get_height() + gap_y + sub_surf.get_height() // 2
            panel.blit(sub_shadow, sub_shadow.get_rect(center=(rect.centerx + self.S(1), sub_y + self.S(1))))
            sub_surf.set_alpha(alpha)
            panel.blit(sub_surf, sub_surf.get_rect(center=(rect.centerx, sub_y)))

        # Really place it in the middle of the table area.
        center_y = H // 2 + float_y

        glow.set_alpha(min(220, alpha))
        surf.blit(glow, glow.get_rect(center=(W // 2, center_y)))
        surf.blit(panel, panel.get_rect(center=(W // 2, center_y)))

    def _draw_deal_deck(self, surf, W, H):
        if not self.dealing_locked:
            return

        cx = W // 2
        cy = H // 2 - self.S(12)
        remaining = max(0, self.deal_deck_remaining)

        # Draw a small stack in the centre to visually represent the 52-card deck.
        layers = min(4, max(1, remaining // 13 + 1))
        for i in range(layers):
            draw_back(
                surf,
                cx - self.S(30) - i * self.S(2),
                cy - self.S(42) - i * self.S(2),
                self.S(60),
                self.S(85)
            )

        blit_text(
            surf,
            str(remaining),
            self.fonts["bodyb"],
            C_GOLD,
            cx,
            cy + self.S(58),
            anchor="center"
        )

    # GAME DRAW
    def _draw_game(self):
        W, H = self.W, self.H
        s = self.screen

        # Game screen background: same style as the cover page,
        # with a brighter center and darker outer edges.
        self._draw_table_gradient()

        cur = self.game.get_current_player()
        human_turn = (
            cur.is_human
            and not self.game.game_over
            and not self.round_result
            and not self.game_result
            and self.ai_wait_ms <= 0
            and not self.dealing_locked
        )
        n = len(self.players)

        # Main table position
        # Use a slightly lower visual center, because the player's hand/buttons/log
        # make the lower half visually heavier. This makes the table look centered.
        tcx = W // 2
        tcy = self.H // 2 

        table_w = self.S(550)
        table_h = self.S(310)
        tr = table_h // 2

        table_rect = pygame.Rect(
            tcx - table_w // 2,
            tcy - table_h // 2,
            table_w,
            table_h
        )

        # Soft table shadow
        shadow_rect = table_rect.copy()
        shadow_rect.y += self.S(8)
        pygame.draw.ellipse(s, (0, 0, 0, 55), shadow_rect)

        # Table body and gold outline
        pygame.draw.ellipse(s, C_TABLE_DK, table_rect)
        pygame.draw.ellipse(s, C_RING, table_rect, max(2, self.S(3)))

        # Thin inner highlight makes the oval look more intentional
        inner_rect = table_rect.inflate(-self.S(14), -self.S(14))
        pygame.draw.ellipse(s, (255, 220, 120), inner_rect, max(1, self.S(1)))

        # During the round banner moment, keep the scene clean:
        # only show the background, table, and the round effect.
        if self.dealing_locked and self.deal_banner_ms > 0:
            self._draw_deal_banner(s, W, H)
            return

        ai = self.players[1:]
        if n == 2:
            self._opp(s, ai[0], tcx, tcy - tr - self.S(55), "top", cur)
        elif n == 3:
            self._opp(s, ai[0], tcx - self.SX(145), tcy - self.S(180), "left", cur)
            self._opp(s, ai[1], tcx + self.SX(145), tcy - self.S(180), "right", cur)
        elif n == 4:
            # 4-player layout: make the three opponents form a rectangle.
            # Left and right opponents use 90-degree rotated card backs.
            side_cy = tcy - self.S(8)
            left_side_x = tcx - table_w // 2 + self.S(24)
            right_side_x = tcx + table_w // 2 - self.S(25)
            top_y = tcy - tr - self.S(70)

            self._opp(s, ai[0], left_side_x, side_cy, "left", cur)
            self._opp(s, ai[1], tcx, top_y, "top", cur)
            self._opp(s, ai[2], right_side_x, side_cy, "right", cur)

        self._draw_centre(s, tcx, tcy)

        show_draw_pile = (n != 4)
        px, py = self.SX(100), self.SY(260)
        if show_draw_pile:
            if not self.dealing_locked:
                draw_back(s, px, py, self.S(60), self.S(85))
                if len(self.game.draw_pile) > 1:
                    draw_back(s, px - self.S(4), py - self.S(4), self.S(60), self.S(85))
            blit_text(s, "Draw Pile", self.fonts["sm"], C_TXT_LIGHT, px + self.S(30), py + self.S(-20), anchor="center")
            draw_count = 0 if self.dealing_locked else len(self.game.draw_pile)
            blit_text(s, str(draw_count), self.fonts["bodyb"], C_GOLD, px + self.S(30), py + self.S(100), anchor="center")

        self._draw_deal_deck(s, W, H)
        self._draw_fly_cards(s)
        self._draw_deal_banner(s, W, H)

        # Pin Game Info to the real right edge with the same width as New Game,
        # and place it around the vertical center of the window.
        panel_w = self.S(102)
        panel_h = self.S(126 + len(self.players) * 20)
        panel_x = W - panel_w - self.S(16)
        panel_y = H // 2 - panel_h // 2

        self._draw_panel(s, panel_x, panel_y, cur)
        self._draw_hand(s, tcx)

        av_cx = tcx - self.SX(30)
        av_cy = H - self.SY(200)
        draw_avatar(s, self.fonts, av_cx, av_cy, self.S(18), "Y", active=human_turn)
        blit_text(s, "You", self.fonts["bodyb"], C_GOLD, av_cx + self.S(25), av_cy - self.S(7), anchor="midleft")
        you_count = 0 if self.dealing_locked else len(self.players[0].hand)
        blit_text(s, f"{you_count} cards", self.fonts["sm"], C_TXT_LIGHT, av_cx + self.S(25), av_cy + self.S(9), anchor="midleft")

        ht = H - self.SY(60)
        bx = tcx - self.S(190)
        self.b_play.r = self.S(10)
        self.b_pass.r = self.S(10)
        self.b_clr.r = self.S(10)
        self.b_play.move(bx, ht, self.S(120), self.S(40))
        self.b_pass.move(bx + self.S(130), ht, self.S(120), self.S(40))
        self.b_clr.move(bx + self.S(260), ht, self.S(130), self.S(40))
        self.b_play.disabled = not human_turn
        self.b_pass.disabled = not human_turn
        self.b_clr.disabled = not human_turn
        self.b_play.draw(s, self.fonts, scale=self.scale)
        self.b_pass.draw(s, self.fonts, scale=self.scale)
        self.b_clr.draw(s, self.fonts, scale=self.scale)

        self.b_back.r = self.S(8)
        self.b_back.move(self.SX(16), self.SY(12), self.S(52), self.S(38))
        self.b_back.draw(s, self.fonts, scale=self.scale)

        self.b_new.r = self.S(8)
        self.b_new.move(W - self.S(118), self.SY(12), self.S(102), self.S(32))
        self.b_new.draw(s, self.fonts, scale=self.scale)

        #self._draw_log(s, W, H)
        if self.notice_txt:
            self._draw_notice(s, W)
        if self.round_result:
            self._draw_round_result(s, W, H)
        if self.result_banner_text:
            self._draw_result_banner(s, W, H)
        if self.game_result and self.game_result_ready:
            self._draw_game_result(s, W, H)

    def _opp(self, surf, player, ox, oy, seat, cur):
        active = (player == cur)

        nc = 0 if self.dealing_locked else len(player.hand)
        lbl = player.name
        cnt = f"{nc} cards"
        badge = self._player_badge_label(player.name)

        if seat == "top":
            avatar_y = oy - self.S(8)
            label_y = oy - self.S(15)
            count_y = oy - self.S(0)
            card_y = oy + self.S(20)
            card_w = self.S(55)
            card_h = self.S(80)
            spread = 0.75

            if self.player_count == 4:
                # In 4-player mode, compress the top row a little more so 13 cards
                # fit comfortably without feeling crowded.
                avatar_y = oy - self.S(10)
                label_y = oy - self.S(17)
                count_y = oy - self.S(1)
                card_y = oy + self.S(18)
                card_w = self.S(44)
                card_h = self.S(64)
                spread = 0.60

            draw_avatar(surf, self.fonts, ox - self.S(45), avatar_y, self.S(18), badge, active=active)

            blit_text(
                surf, lbl, self.fonts["bodyb"], C_GOLD,
                ox - self.S(20), label_y,
                anchor="midleft"
            )

            blit_text(
                surf, cnt, self.fonts["sm"], C_TXT_LIGHT,
                ox - self.S(20), count_y,
                anchor="midleft"
            )

            draw_fan_backs_horiz(
                surf,
                ox + self.S(-25),
                card_y,
                nc,
                cw=card_w,
                ch=card_h,
                spread_scale=spread
            )

        elif seat == "left":
            if self.player_count == 4:
                # 4-player mode: centered side nameplate with badge above text.
                label_x = ox - self.S(82)
                label_y = oy - self.S(34)

                draw_avatar(surf, self.fonts, label_x, label_y, self.S(17), badge, active=active)
                blit_text(surf, lbl, self.fonts["sm"], C_WHITE, label_x, label_y + self.S(26), anchor="midtop")
                blit_text(surf, cnt, self.fonts["sm"], C_GOLD, label_x, label_y + self.S(44), anchor="midtop")

                draw_rotated_stack_backs_vert(
                    surf,
                    ox,
                    oy,
                    nc,
                    cw=self.S(34),
                    ch=self.S(50),
                    spread_scale=0.36,
                    angle=90
                )
            else:
                # 3-player layout
                draw_avatar(surf, self.fonts, ox - self.S(112), oy - self.S(-2), self.S(17), badge, active=active)
                blit_text(surf, lbl, self.fonts["sm"], C_WHITE, ox - self.S(87), oy - self.S(8), anchor="midleft")
                blit_text(surf, cnt, self.fonts["sm"], C_GOLD, ox - self.S(87), oy + self.S(9), anchor="midleft")

                draw_slanted_stack_backs(
                    surf,
                    ox + self.S(30),
                    oy - self.S(6),
                    nc,
                    cw=self.S(38),
                    ch=self.S(54),
                    dx=-self.S(15),
                    dy=self.S(7)
                )

        elif seat == "right":
            if self.player_count == 4:
                # 4-player mode: centered side nameplate with badge above text.
                # Move Player 3 a bit left so it sits between the card stack and Game Info.
                label_x = ox + self.S(68)
                label_y = oy - self.S(34)

                draw_avatar(surf, self.fonts, label_x, label_y, self.S(17), badge, active=active)
                blit_text(surf, lbl, self.fonts["sm"], C_WHITE, label_x, label_y + self.S(26), anchor="midtop")
                blit_text(surf, cnt, self.fonts["sm"], C_GOLD, label_x, label_y + self.S(44), anchor="midtop")

                draw_rotated_stack_backs_vert(
                    surf,
                    ox,
                    oy,
                    nc,
                    cw=self.S(34),
                    ch=self.S(50),
                    spread_scale=0.36,
                    angle=270
                )
            else:
                # 3-player layout
                draw_avatar(surf, self.fonts, ox + self.S(112), oy - self.S(-2), self.S(17), badge, active=active)
                blit_text(surf, lbl, self.fonts["sm"], C_WHITE, ox + self.S(87), oy - self.S(8), anchor="midright")
                blit_text(surf, cnt, self.fonts["sm"], C_GOLD, ox + self.S(87), oy + self.S(9), anchor="midright")

                draw_slanted_stack_backs(
                    surf,
                    ox - self.S(68),
                    oy - self.S(6),
                    nc,
                    cw=self.S(38),
                    ch=self.S(54),
                    dx=self.S(15),
                    dy=self.S(7)
                )

    def _filtered_center_status_message(self):
        msg = self.game.status_message or ""
        if not msg:
            return ""

        # In 2-player mode, these system hints are too noisy because the turn flow is obvious.
        # Keep real action narration, but hide round/table reset explanations.
        if self.player_count == 2:
            hidden_phrases = [
                "All other players passed",
                "No player has",
                "Round ",
            ]
            if any(phrase in msg for phrase in hidden_phrases):
                return ""

        return msg

    def _draw_centre(self, surf, cx, cy):
        owner = self.action_msg_owner or ""
        cards = [] if self.dealing_locked else (list(self.game.current_table) if self.game.current_table else [])
        cw, ch = self.S(48), self.S(68)
        gap = self.S(6)

        if cards:
            total = len(cards) * (cw + gap) - gap
            sx = cx - total // 2

            for i, card in enumerate(cards):
                draw_face(
                    surf,
                    self.fonts,
                    sx + i * (cw + gap),
                    cy - ch // 2 - self.S(15),
                    cw,
                    ch,
                    str(card),
                    show_corner_suit=False,
                    big_suit_scale=0.75
                )

        if self.result_banner_text or self.round_result or self.game_result or self.dealing_locked:
            return

        # Only draw the current action message.
        # Do not fall back to self.game.status_message here, otherwise the same
        # player action appears once as an animated action and then again as a
        # normal status message.
        msg = self.action_msg
        if not msg:
            return

        has_table_cards = bool(cards)

        msg_x = cx

        if self.player_count == 4 and not self._is_opening_action_message(msg):
            # In 4-player mode, place the action narration near the side
            # of the player who made the move.
            if owner == "Player 1":
                # P1 is on the left side, so the message sits left of the centre cards.
                # Nudge it slightly right and slightly down.
                msg_x = cx - self.S(142)
                msg_y = cy - self.S(33)
            elif owner == "Player 2":
                # P2 is on the top side, so the message stays above the centre cards.
                msg_x = cx
                msg_y = cy - ch // 2 - self.S(57)
            elif owner == "Player 3":
                # P3 is on the right side, so the message sits right of the centre cards.
                # Nudge it slightly left and slightly down.
                msg_x = cx + self.S(142)
                msg_y = cy - self.S(33)
            elif owner == "You":
                # Your actions stay below the centre cards.
                msg_x = cx
                msg_y = cy + ch // 2 + self.S(12)
            else:
                msg_y = cy + ch // 2 + self.S(4)
        else:
            # Opening narration and non-4-player layouts keep the original positions.
            if owner == "You":
                msg_y = cy + ch // 2 + self.S(12)
            elif owner:
                msg_y = cy - ch // 2 - self.S(57)
            else:
                msg_y = cy + ch // 2 + self.S(4)

        self._draw_center_message(surf, msg, msg_x, msg_y)

    def _draw_center_message(self, surf, msg, cx, y):
        if not msg:
            return

        life = 1.0
        if self.action_msg:
            life = max(0, min(1, self.action_msg_ms / self.action_msg_duration))

        # Same animated feeling as the draw-card movement: small pop + fade.
        pop = 1 + 0.08 * math.sin((1 - life) * math.pi)
        alpha = 255 if not self.action_msg else int(90 + 165 * min(1, life * 1.6))
        y = int(y - math.sin((1 - life) * math.pi) * self.S(4))

        text_size = max(8, int(13 * self.scale * pop))
        suit_size = max(10, int(15 * self.scale * pop))
        text_font = pygame.font.SysFont("Cooper black", text_size, bold=False)
        suit_font = pygame.font.SysFont("Times New Roman", suit_size, bold=True)

        def render_parts(line_text):
            parts = []
            temp = ""
            for ch_msg in line_text:
                if ch_msg in RED_SUITS or ch_msg in {"♠", "♣"}:
                    if temp:
                        parts.append(("text", temp))
                        temp = ""
                    parts.append(("suit", ch_msg))
                else:
                    temp += ch_msg
            if temp:
                parts.append(("text", temp))

            rendered = []
            width = 0
            for part_type, value in parts:
                if part_type == "suit":
                    color = C_RED if value in RED_SUITS else C_BLACK
                    outline = suit_font.render(value, True, C_WHITE)
                    img = suit_font.render(value, True, color)
                    temp_surf = pygame.Surface((img.get_width() + 4, img.get_height() + 4), pygame.SRCALPHA)
                    temp_surf.blit(outline, (0, 2))
                    temp_surf.blit(outline, (4, 2))
                    temp_surf.blit(outline, (2, 0))
                    temp_surf.blit(outline, (2, 4))
                    temp_surf.blit(img, (2, 2))
                    img = temp_surf
                else:
                    img = text_font.render(value, True, C_WHITE)

                img.set_alpha(alpha)
                rendered.append(img)
                width += img.get_width()

            return rendered, width

        # Wider box so long narration is not cut off.
        max_box_w = min(self.W - self.SX(230), self.S(560))
        max_text_w = max_box_w - self.S(24)

        rendered_parts, total_w = render_parts(msg)

        # If a message is still too long, shrink it once instead of clipping it.
        if total_w > max_text_w:
            shrink = max(0.72, max_text_w / max(1, total_w))
            text_font = pygame.font.SysFont("Cooper black", max(8, int(text_size * shrink)), bold=False)
            suit_font = pygame.font.SysFont("Times New Roman", max(10, int(suit_size * shrink)), bold=True)
            rendered_parts, total_w = render_parts(msg)

        lw = min(total_w + self.S(22), max_box_w)
        lh = self.S(28)
        lr = pygame.Rect(cx - lw // 2, y, lw, lh)

        box = pygame.Surface((lr.w, lr.h), pygame.SRCALPHA)
        pygame.draw.rect(box, (*C_NOTICE_BG, int(alpha * 0.80)), (0, 0, lr.w, lr.h), border_radius=self.S(7))
        pygame.draw.rect(box, (*C_GOLD, int(alpha * 0.95)), (0, 0, lr.w, lr.h), max(1, self.S(1)), border_radius=self.S(7))
        surf.blit(box, lr.topleft)

        text_x = cx - total_w // 2
        for img in rendered_parts:
            rect = img.get_rect(midleft=(text_x, lr.centery))
            surf.blit(img, rect)
            text_x += img.get_width()


    def _draw_bomb_flame(self, surf, cx, cy, size, intensity=1.0, angle=0):
        size = int(size)
        intensity = max(0.0, min(1.0, intensity))

        flame = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
        fc = flame.get_rect().center

        flicker = math.sin(pygame.time.get_ticks() * 0.018) * 0.18 + random.uniform(-0.08, 0.08)
        scale = 0.85 + intensity * 0.45 + flicker
        flame_h = int(size * 1.45 * scale)
        flame_w = int(size * 0.82 * scale)

        outer = [
            (fc[0], fc[1] - flame_h),
            (fc[0] - flame_w, fc[1] - int(flame_h * 0.20)),
            (fc[0] - int(flame_w * 0.28), fc[1] + int(flame_h * 0.28)),
            (fc[0], fc[1] + int(flame_h * 0.10)),
            (fc[0] + int(flame_w * 0.28), fc[1] + int(flame_h * 0.28)),
            (fc[0] + flame_w, fc[1] - int(flame_h * 0.20)),
        ]

        mid = [
            (fc[0], fc[1] - int(flame_h * 0.78)),
            (fc[0] - int(flame_w * 0.55), fc[1] - int(flame_h * 0.05)),
            (fc[0], fc[1] + int(flame_h * 0.16)),
            (fc[0] + int(flame_w * 0.55), fc[1] - int(flame_h * 0.05)),
        ]

        inner = [
            (fc[0], fc[1] - int(flame_h * 0.46)),
            (fc[0] - int(flame_w * 0.28), fc[1] + int(flame_h * 0.04)),
            (fc[0], fc[1] + int(flame_h * 0.16)),
            (fc[0] + int(flame_w * 0.28), fc[1] + int(flame_h * 0.04)),
        ]

        pygame.draw.polygon(flame, (255, 72, 28, 235), outer)
        pygame.draw.polygon(flame, (255, 162, 38, 245), mid)
        pygame.draw.polygon(flame, (255, 245, 128, 255), inner)

        glow_r = int(size * (1.15 + intensity * 0.7))
        pygame.draw.circle(flame, (255, 116, 32, 55), fc, glow_r)
        pygame.draw.circle(flame, (255, 224, 92, 45), fc, int(glow_r * 0.58))

        if angle:
            flame = pygame.transform.rotate(flame, angle)

        rect = flame.get_rect(center=(int(cx), int(cy)))
        surf.blit(flame, rect.topleft)

    def _draw_bomb_panel(self, surf, cx, cy, radius, t, title, winner_text, loser_rows):
        t = max(0.0, min(1.0, t))
        pulse = math.sin(t * math.pi * 10) * self.S(2.0)
        body_r = int(radius + pulse)

        # Shadow + glow
        pygame.draw.circle(surf, (0, 0, 0, 115), (cx + self.S(7), cy + self.S(12)), body_r)

        glow = pygame.Surface((body_r * 4, body_r * 4), pygame.SRCALPHA)
        gc = glow.get_rect().center
        pygame.draw.circle(glow, (255, 90, 25, 38), gc, int(body_r * 1.36))
        pygame.draw.circle(glow, (255, 204, 65, 24), gc, int(body_r * 1.02))
        surf.blit(glow, glow.get_rect(center=(cx, cy)))

        # Bomb body
        pygame.draw.circle(surf, (12, 13, 18), (cx, cy), body_r)
        pygame.draw.circle(surf, (38, 39, 48), (cx - self.S(7), cy - self.S(9)), int(body_r * 0.84))
        pygame.draw.circle(surf, (3, 4, 7), (cx, cy), body_r, max(3, self.S(4)))

        # White highlight moved upward by another 10px, plus a second smaller dot
        # diagonally to the lower-left for a more bomb-like glossy reflection.
        main_dot_center = (
            cx - int(body_r * 0.24) - self.S(10),
            cy - int(body_r * 0.54) - self.S(10)
        )
        pygame.draw.circle(
            surf,
            (255, 255, 255, 30),
            main_dot_center,
            int(body_r * 0.13)
        )
        pygame.draw.circle(
            surf,
            (255, 255, 255, 22),
            (main_dot_center[0] - self.S(40), main_dot_center[1] + self.S(16)),
            max(self.S(7), int(body_r * 0.055))
        )

        # Fuse base
        fuse_base = pygame.Rect(cx - self.S(16), cy - body_r - self.S(7), self.S(32), self.S(22))
        rrect(surf, (12, 13, 18), fuse_base, r=self.S(8), bw=self.S(2), bc=(3, 4, 7))

        # Fuse path from bomb body to outer tip. The flame should move from the
        # outer tip toward the bomb body.
        fuse_len = self.S(134)
        burn = max(0.0, min(1.0, t))
        start = pygame.Vector2(cx, cy - body_r - self.S(5))
        end = pygame.Vector2(cx - fuse_len, cy - body_r - self.S(72))

        points = []
        for i in range(16):
            p = i / 15
            x = start.x + (end.x - start.x) * p
            y = start.y + (end.y - start.y) * p
            y += math.sin(p * math.pi * 3) * self.S(8)
            points.append((int(x), int(y)))

        pygame.draw.lines(surf, (92, 65, 42), False, points, max(4, self.S(5)))
        pygame.draw.lines(surf, (232, 190, 96), False, points, max(1, self.S(2)))

        # Burned fuse part should be behind the flame (from outer end inward).
        burn_index = int((len(points) - 1) * burn)
        flame_index = max(0, len(points) - 1 - burn_index)
        burned_points = points[flame_index:]
        if len(burned_points) >= 2:
            pygame.draw.lines(surf, (35, 25, 18), False, burned_points, max(5, self.S(6)))

        flame_pos = points[flame_index]
        self._draw_bomb_flame(
            surf,
            flame_pos[0],
            flame_pos[1] - self.S(5),
            self.S(17),
            intensity=0.45 + burn * 0.8
        )

        # Text layout - slightly smaller and better spaced so winner text is clear.
        title_font = pygame.font.SysFont("Cooper black", max(16, int(26 * self.scale)), bold=False)
        win_font = pygame.font.SysFont("Cooper black", max(15, int(20 * self.scale)), bold=False)
        row_font = pygame.font.SysFont("Cooper black", max(12, int(14 * self.scale)), bold=False)
        timer_font = pygame.font.SysFont("Cooper black", max(17, int(27 * self.scale)), bold=False)

        title_y = cy - self.S(50)
        winner_y = cy - self.S(18)
        line_y = cy + self.S(4)

        title_img = title_font.render(title, True, (255, 210, 72))
        title_shadow = title_font.render(title, True, (95, 24, 10))
        surf.blit(title_shadow, title_shadow.get_rect(center=(cx + self.S(2), title_y + self.S(2))))
        surf.blit(title_img, title_img.get_rect(center=(cx, title_y)))

        winner_img = win_font.render(winner_text, True, C_WHITE)
        surf.blit(winner_img, winner_img.get_rect(center=(cx, winner_y)))

        pygame.draw.line(
            surf,
            (255, 188, 52),
            (cx - int(body_r * 0.50), line_y),
            (cx + int(body_r * 0.50), line_y),
            max(1, self.S(2))
        )

        if not loser_rows:
            msg = row_font.render("No penalty this round", True, (245, 236, 210))
            surf.blit(msg, msg.get_rect(center=(cx, cy + self.S(18))))
        else:
            start_y = cy + self.S(35)
            for i, row in enumerate(loser_rows[:4]):
                name = self._player_display_name(row["name"])
                left = f"{name} lost"
                right = f"+{row['penalty']}  Total {row['total']}"
                y = start_y + i * self.S(20)

                left_img = row_font.render(left, True, C_WHITE)
                right_img = row_font.render(right, True, (255, 210, 72))

                surf.blit(left_img, left_img.get_rect(midleft=(cx - int(body_r * 0.54), y)))
                surf.blit(right_img, right_img.get_rect(midright=(cx + int(body_r * 0.54), y)))

        if self.round_result_countdown_active:
            countdown_ms = max(0, self.round_result_ms - self.round_result_explosion_ms - self.round_result_teaser_ms)
            countdown = countdown_ms / 1000.0
        else:
            countdown = self.round_result_countdown_ms / 1000.0
        timer_col = (255, 70, 28) if countdown <= 1.2 else (255, 218, 92)
        timer = timer_font.render(f"{countdown:.1f}", True, timer_col)
        # Keep the countdown higher so it does not collide with the press hint below.
        surf.blit(timer, timer.get_rect(center=(cx, cy + body_r - self.S(56))))

    def _draw_bomb_explosion(self, surf, cx, cy, progress):
        progress = max(0.0, min(1.0, progress))
        now = pygame.time.get_ticks()

        flash_alpha = int(215 * (1 - progress))
        if flash_alpha > 0:
            flash = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            flash.fill((255, 238, 170, flash_alpha))
            surf.blit(flash, (0, 0))

        max_r = self.S(215)
        r = int(max_r * (0.30 + progress * 0.90))

        burst = pygame.Surface((r * 3, r * 3), pygame.SRCALPHA)
        bc = burst.get_rect().center
        for i in range(26):
            ang = (i / 26) * math.tau + math.sin(now * 0.003 + i) * 0.08
            inner = int(r * (0.12 + 0.08 * math.sin(i)))
            outer = int(r * (0.70 + 0.28 * math.sin(i * 1.7)))
            p1 = (int(bc[0] + math.cos(ang - 0.07) * inner), int(bc[1] + math.sin(ang - 0.07) * inner))
            p2 = (int(bc[0] + math.cos(ang) * outer), int(bc[1] + math.sin(ang) * outer))
            p3 = (int(bc[0] + math.cos(ang + 0.07) * inner), int(bc[1] + math.sin(ang + 0.07) * inner))
            col = (255, 196, 54, int(235 * (1 - progress)))
            pygame.draw.polygon(burst, col, [p1, p2, p3])

        pygame.draw.circle(burst, (255, 238, 120, int(235 * (1 - progress))), bc, int(r * 0.42))
        pygame.draw.circle(burst, (255, 92, 28, int(185 * (1 - progress))), bc, int(r * 0.72), max(6, self.S(9)))
        pygame.draw.circle(burst, (255, 255, 255, int(180 * (1 - progress))), bc, int(r * 0.26))
        surf.blit(burst, burst.get_rect(center=(cx, cy)))

        for i in range(18):
            ang = i * 0.95 + now * 0.001
            dist = self.S(35) + progress * self.S(150) + (i % 4) * self.S(7)
            sx = cx + math.cos(ang) * dist
            sy = cy + math.sin(ang) * dist * 0.72
            sr = int(self.S(14 + (i % 5) * 4) * (0.65 + progress))
            alpha = int(90 * (1 - progress))
            pygame.draw.circle(surf, (90, 82, 75, alpha), (int(sx), int(sy)), sr)

        for i in range(34):
            ang = i * 0.83
            dist = progress * self.S(235) * (0.55 + (i % 5) * 0.12)
            x = cx + math.cos(ang) * dist
            y = cy + math.sin(ang) * dist
            size = max(2, self.S(3 + i % 4))
            col = (40, 30, 24) if i % 2 else (255, 170, 45)
            pygame.draw.circle(surf, col, (int(x), int(y)), size)

    def _draw_teaser_smoke(self, surf, cx, cy, progress):
        progress = max(0.0, min(1.0, progress))
        now = pygame.time.get_ticks() * 0.001
        cloud = pygame.Surface((self.S(520), self.S(240)), pygame.SRCALPHA)
        ccx, ccy = cloud.get_width() // 2, cloud.get_height() // 2
        puffs = [
            (-84, -18, 30), (-46, -38, 22), (4, -50, 18), (52, -14, 28),
            (88, 18, 24), (20, 34, 20), (-34, 42, 18), (-86, 20, 24),
        ]
        for i, (ox, oy, rad) in enumerate(puffs):
            drift_x = math.sin(now * 0.9 + i) * self.S(3)
            drift_y = math.cos(now * 0.7 + i * 0.8) * self.S(2)
            alpha = int(90 * (0.85 + 0.15 * math.sin(now + i)) * (0.75 + 0.25 * progress))
            pygame.draw.circle(
                cloud,
                (96, 84, 78, alpha),
                (int(ccx + self.S(ox) + drift_x), int(ccy + self.S(oy) + drift_y)),
                self.S(rad)
            )
        surf.blit(cloud, cloud.get_rect(center=(cx, cy - self.S(8))))

    def _draw_round_next_button(self, surf, cx, cy, active=False):
        hover = self.b_round_next.hovered and not self.b_round_next.disabled
        pulse = 1.0 + (0.018 if hover else 0.0) + (0.010 * math.sin(pygame.time.get_ticks() * 0.008))
        bs = 0.6

        def DS(v):
            return max(1, int(self.S(v) * bs))

        # Red emergency push button style, scaled down to 0.6x.
        w = max(DS(100), int(self.S(100) * pulse * bs))
        h = max(DS(72), int(self.S(72) * pulse * bs))
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (cx, cy)
        self.b_round_next.move(rect.x, rect.y, rect.w, rect.h)

        base_shadow = pygame.Rect(rect.x + DS(4), rect.y + DS(34), rect.w - DS(8), DS(24))
        base_ring = pygame.Rect(rect.x + DS(9), rect.y + DS(27), rect.w - DS(18), DS(24))
        side_band = pygame.Rect(rect.x + DS(22), rect.y + DS(19), rect.w - DS(44), DS(24))
        top_cap = pygame.Rect(rect.x + DS(16), rect.y + DS(2), rect.w - DS(32), DS(37))

        if active:
            top_cap.y += DS(4)
            side_band.y += DS(4)

        glow = pygame.Surface((rect.w + DS(54), rect.h + DS(42)), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (255, 120, 74, 22 if hover else 14), glow.get_rect())
        surf.blit(glow, glow.get_rect(center=rect.center))

        # Bottom dark base
        pygame.draw.ellipse(surf, (26, 27, 31), base_shadow)
        pygame.draw.ellipse(surf, (54, 55, 60), base_shadow, max(1, DS(2)))

        # Metallic ring
        pygame.draw.ellipse(surf, (181, 181, 188), base_ring)
        inner_ring = base_ring.inflate(-DS(6), -DS(6))
        pygame.draw.ellipse(surf, (208, 208, 214), inner_ring)
        pygame.draw.ellipse(surf, (112, 112, 120), base_ring, max(1, DS(2)))

        # Red side band
        pygame.draw.ellipse(surf, (88, 0, 0), side_band)
        pygame.draw.ellipse(surf, (132, 10, 10), side_band, max(1, DS(2)))

        # Red top button
        pygame.draw.ellipse(surf, (232, 0, 0), top_cap)
        pygame.draw.ellipse(surf, (120, 0, 0), top_cap, max(1, DS(2)))

        # Top glossy highlight
        shine = pygame.Rect(
            top_cap.x + DS(10),
            top_cap.y + DS(5),
            top_cap.w - DS(20),
            max(DS(10), top_cap.h // 4),
        )
        pygame.draw.ellipse(surf, (255, 120, 120, 85), shine)

    def _draw_next_round_teaser(self, surf, cx, cy, progress):
        progress = max(0.0, min(1.0, progress))

        # NEXT ROUND now grows out from the explosion instead of suddenly appearing.
        # It starts tiny, quickly expands, then gives a small bounce so it feels
        # connected to the bomb blast.
        pop = 0.18 + 0.95 * (1 - (1 - progress) ** 3)
        bounce = 1.0 + 0.10 * math.sin(progress * math.pi) * (1 - progress)
        scale_mul = pop * bounce
        alpha = int(255 * min(1.0, progress * 1.8))

        # Smoke appears behind the growing text.
        self._draw_teaser_smoke(surf, cx, cy - self.S(3), progress)

        font_size = max(10, int(62 * self.scale * scale_mul))
        sub_size = max(8, int(22 * self.scale * scale_mul))
        font = pygame.font.SysFont("Cooper black", font_size, bold=False)
        sub_font = pygame.font.SysFont("Cooper black", sub_size, bold=False)

        text = font.render("NEXT ROUND", True, (255, 232, 142))
        sub = sub_font.render("SHUFFLE AND DEAL", True, C_WHITE)
        shadow = font.render("NEXT ROUND", True, (90, 20, 8))
        shadow2 = sub_font.render("SHUFFLE AND DEAL", True, (90, 20, 8))

        for img in (text, sub, shadow, shadow2):
            img.set_alpha(alpha)

        # The glow scales with the text so the blast feels like it is pushing
        # the NEXT ROUND banner outward.
        glow_w = max(20, int(self.S(560) * scale_mul))
        glow_h = max(20, int(self.S(170) * scale_mul))
        glow = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
        glow_alpha = int(74 * min(1.0, progress * 1.4))
        glow_alpha2 = int(22 * min(1.0, progress * 1.4))

        pygame.draw.ellipse(glow, (255, 90, 22, glow_alpha), glow.get_rect())
        inner = glow.get_rect().inflate(
            -max(1, int(self.S(80) * scale_mul)),
            -max(1, int(self.S(46) * scale_mul))
        )
        if inner.w > 0 and inner.h > 0:
            pygame.draw.ellipse(glow, (255, 212, 90, glow_alpha2), inner)
        surf.blit(glow, glow.get_rect(center=(cx, cy + self.S(2))))

        # Tiny upward settling motion while the text grows.
        rise = int(self.S(18) * (1 - progress))
        text_y = cy - rise
        sub_gap = int(self.S(50) * scale_mul)

        surf.blit(shadow, shadow.get_rect(center=(cx + self.S(4), text_y + self.S(4))))
        surf.blit(text, text.get_rect(center=(cx, text_y)))
        surf.blit(shadow2, shadow2.get_rect(center=(cx + self.S(2), text_y + sub_gap + self.S(2))))
        surf.blit(sub, sub.get_rect(center=(cx, text_y + sub_gap)))

    def _draw_round_result(self, surf, W, H):
        if not self.round_result:
            return

        if self.round_result_countdown_active:
            life = max(0, min(1, self.round_result_ms / max(1, self.round_result_duration)))
            elapsed = self.round_result_duration - self.round_result_ms
        else:
            life = 1.0
            elapsed = 0

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay_alpha = 118 if not self.round_result_countdown_active else 110 + int(42 * (1 - life))
        overlay.fill((0, 0, 0, overlay_alpha))
        surf.blit(overlay, (0, 0))

        cx = W // 2
        # Move the whole ROUND RESULT bomb panel down by another 10px.
        cy = H // 2 + self.S(18)

        winner_name = self._player_display_name(self.round_result.get("winner", ""))
        winner_text = f"{winner_name} WIN!"
        losers = self.round_result.get("losers", [])

        countdown_end = self.round_result_countdown_ms
        explosion_end = countdown_end + self.round_result_explosion_ms

        # Button moves down by 20px total from the old position.
        button_y = cy + self.S(198)
        self.b_round_next.disabled = self.round_result_countdown_active

        if (not self.round_result_countdown_active) or elapsed < countdown_end:
            local_t = 0.0 if not self.round_result_countdown_active else min(1.0, elapsed / max(1, countdown_end))
            danger = max(0.0, (local_t - 0.58) / 0.42) if self.round_result_countdown_active else 0.0
            shake_x = int(math.sin(pygame.time.get_ticks() * 0.055) * self.S(5) * danger)
            shake_y = int(math.cos(pygame.time.get_ticks() * 0.047) * self.S(4) * danger)

            radius = min(self.S(188), max(self.S(146), int(min(W, H) * 0.295)))
            self._draw_bomb_panel(
                surf,
                cx + shake_x,
                cy + shake_y,
                radius,
                local_t,
                "ROUND RESULT",
                winner_text,
                losers
            )

            hint_font = pygame.font.SysFont("Cooper black", max(12, int(16 * self.scale)), bold=False)
            hint = hint_font.render("Press to go NEXT ROUND", True, (255, 232, 142))
            hint_shadow = hint_font.render("Press to go NEXT ROUND", True, (95, 24, 10))
            # Press hint moves up by 5px from the previous version.
            hint_y = cy + self.S(154)
            surf.blit(hint_shadow, hint_shadow.get_rect(center=(cx + self.S(1), hint_y + self.S(1))))
            surf.blit(hint, hint.get_rect(center=(cx, hint_y)))
            self._draw_round_next_button(surf, cx, button_y, active=self.round_result_countdown_active)

            if self.round_result_countdown_active and danger > 0:
                warn = pygame.Surface((W, H), pygame.SRCALPHA)
                warn_alpha = int(62 * danger * (0.55 + 0.45 * math.sin(pygame.time.get_ticks() * 0.018)))
                pygame.draw.rect(warn, (255, 35, 20, warn_alpha), warn.get_rect(), width=max(10, self.S(24)))
                surf.blit(warn, (0, 0))

        elif elapsed < explosion_end:
            p = (elapsed - countdown_end) / max(1, self.round_result_explosion_ms)
            self._draw_bomb_explosion(surf, cx, cy, p)

            # Let NEXT ROUND grow together with the explosion.
            teaser_p = max(0.0, min(1.0, (p - 0.18) / 0.82))
            self._draw_next_round_teaser(surf, cx, cy, teaser_p)

        else:
            # Explosion has already grown NEXT ROUND to full size.
            # Keep it on screen without replaying the grow/explosion teaser.
            self._draw_next_round_teaser(surf, cx, cy, 1.0)


    def _draw_game_result(self, surf, W, H):
        if not self.game_result:
            return

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surf.blit(overlay, (0, 0))

        cx = W // 2
        cy = H // 2

        panel_w = min(self.S(560), W - self.SX(130))
        panel_h = self.S(320)
        panel = pygame.Rect(cx - panel_w // 2, cy - panel_h // 2, panel_w, panel_h)

        glow = pygame.Surface((panel.w + self.S(70), panel.h + self.S(70)), pygame.SRCALPHA)
        glow_rect = glow.get_rect()
        for i in range(5, 0, -1):
            pygame.draw.rect(
                glow,
                (110, 86, 255, max(8, 46 // i)),
                glow_rect.inflate(-i * self.S(9), -i * self.S(9)),
                border_radius=self.S(34)
            )
        for i in range(4, 0, -1):
            pygame.draw.rect(
                glow,
                (255, 205, 95, max(8, 36 // i)),
                glow_rect.inflate(-i * self.S(15), -i * self.S(15)),
                border_radius=self.S(32)
            )
        surf.blit(glow, (panel.x - self.S(35), panel.y - self.S(35)))

        box = pygame.Surface((panel.w, panel.h), pygame.SRCALPHA)
        pygame.draw.rect(box, (33, 22, 62, 242), (0, 0, panel.w, panel.h), border_radius=self.S(22))
        inner_rect = pygame.Rect(self.S(10), self.S(10), panel.w - self.S(20), panel.h - self.S(20))
        pygame.draw.rect(box, (59, 42, 110, 218), inner_rect, border_radius=self.S(17))
        pygame.draw.rect(box, (241, 192, 64, 255), (0, 0, panel.w, panel.h), max(2, self.S(2)), border_radius=self.S(22))
        pygame.draw.rect(
            box,
            (255, 236, 190, 120),
            inner_rect,
            max(1, self.S(1)),
            border_radius=self.S(17)
        )
        surf.blit(box, panel.topleft)

        title_font = pygame.font.SysFont("Cooper black", max(20, int(34 * self.scale)), bold=False)
        h_font = pygame.font.SysFont("Cooper black", max(15, int(21 * self.scale)), bold=False)
        row_font = pygame.font.SysFont("Cooper black", max(11, int(14 * self.scale)), bold=False)

        title = title_font.render("GAME RESULT", True, C_GOLD)
        surf.blit(title, title.get_rect(center=(cx, panel.y + self.S(38))))

        loser_name = self._player_display_name(self.game_result.get("loser", ""))
        if loser_name == "You":
            summary = "You reached 150 points"
        else:
            summary = f"{loser_name} reached 150 points"

        summary_img = h_font.render(summary, True, C_WHITE)
        surf.blit(summary_img, summary_img.get_rect(center=(cx, panel.y + self.S(76))))

        line_y = panel.y + self.S(105)
        pygame.draw.line(
            surf,
            (255, 220, 120),
            (panel.x + self.S(36), line_y),
            (panel.right - self.S(36), line_y),
            max(1, self.S(1))
        )

        rows = self.game_result.get("rows", [])
        start_y = panel.y + self.S(132)
        for i, row in enumerate(rows[:4]):
            name = self._player_display_name(row["name"])
            total = row["total"]
            penalty = row["penalty"]

            label = f"{i + 1}. {name}"
            score = f"+{penalty} this round   Total {total}"

            y = start_y + i * self.S(28)
            left_img = row_font.render(label, True, C_WHITE if row["name"] != self.game_result.get("loser") else C_GOLD)
            right_img = row_font.render(score, True, C_TXT_MUTED if row["name"] != self.game_result.get("loser") else C_GOLD)

            surf.blit(left_img, left_img.get_rect(midleft=(panel.x + self.S(50), y)))
            surf.blit(right_img, right_img.get_rect(midright=(panel.right - self.S(50), y)))

        btn_y = panel.bottom - self.S(64)
        self.b_again.r = self.S(12)
        self.b_end.r = self.S(12)
        self.b_again.move(cx - self.S(185), btn_y, self.S(170), self.S(44))
        self.b_end.move(cx + self.S(15), btn_y, self.S(170), self.S(44))

        self.b_again.disabled = False
        self.b_end.disabled = False
        self.b_again.draw(surf, self.fonts, glow=True, scale=self.scale)
        self.b_end.draw(surf, self.fonts, scale=self.scale)


    def _draw_result_banner(self, surf, W, H):
        if not self.result_banner_text:
            return

        life = max(0, min(1, self.result_banner_ms / max(1, self.result_banner_duration)))
        t = 1 - life

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay_alpha = int(55 + 65 * min(1, t * 1.8))
        overlay.fill((0, 0, 0, overlay_alpha))
        surf.blit(overlay, (0, 0))

        cx = W // 2
        cy = H // 2 - self.S(8)

        glow_radius = self.S(150) + int(self.S(20) * math.sin(t * math.pi * 3) * (0.9 - 0.6 * t))
        glow = pygame.Surface((glow_radius * 2 + self.S(40), glow_radius * 2 + self.S(40)), pygame.SRCALPHA)
        gcx = glow.get_width() // 2
        gcy = glow.get_height() // 2

        if self.result_banner_kind == "win":
            # Win keeps the bright circular glow.
            glow_col = (255, 205, 70, 60)
            pygame.draw.circle(glow, glow_col, (gcx, gcy), glow_radius)
            pygame.draw.circle(glow, (255, 255, 255, 24), (gcx, gcy), int(glow_radius * 0.66))
        else:
            # Lose uses a single-color thick red X.
            # Slightly larger than the original, but not too oversized.
            x_len = int(glow_radius * 0.85)
            # Thicker than the previous version, with a darker muted red.
            x_w = max(40, self.S(94))
            # Darker, muted red with slightly lower opacity.
            x_color = (150, 30, 30, 120)

            pygame.draw.line(
                glow,
                x_color,
                (gcx - x_len, gcy - x_len),
                (gcx + x_len, gcy + x_len),
                x_w
            )
            pygame.draw.line(
                glow,
                x_color,
                (gcx + x_len, gcy - x_len),
                (gcx - x_len, gcy + x_len),
                x_w
            )

        surf.blit(glow, (cx - glow.get_width() // 2, cy - glow.get_height() // 2))

        pop = 1 + 0.24 * math.sin(min(1, t * 1.2) * math.pi)
        pop += 0.04 * math.sin(t * math.pi * 6) * life
        text_size = max(36, int(82 * self.scale * pop))
        shadow_font = pygame.font.SysFont("Cooper black", text_size, bold=False)
        main_font = pygame.font.SysFont("Cooper black", text_size, bold=False)

        text = self.result_banner_text
        shadow = shadow_font.render(text, True, (90, 10, 10))
        outline = main_font.render(text, True, (255, 215, 80))
        main = main_font.render(text, True, C_WHITE)

        banner_y = int(cy - self.S(8) - math.sin(t * math.pi) * self.S(10))

        for alpha_mult, scale_extra in ((28, 1.12), (20, 1.18)):
            g = main_font.render(text, True, (255, 255, 255))
            g = pygame.transform.rotozoom(g, 0, scale_extra)
            g.set_alpha(alpha_mult)
            grect = g.get_rect(center=(cx, banner_y))
            surf.blit(g, grect)

        shadow_rect = shadow.get_rect(center=(cx + self.S(5), banner_y + self.S(6)))
        surf.blit(shadow, shadow_rect)

        outline_offsets = [(-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)]
        for ox, oy in outline_offsets:
            rect = outline.get_rect(center=(cx + self.S(ox), banner_y + self.S(oy)))
            surf.blit(outline, rect)

        main_rect = main.get_rect(center=(cx, banner_y))
        surf.blit(main, main_rect)

    def _draw_hand(self, surf, cx):
        self.hand_rects = []
        if self.dealing_locked:
            return

        hand = self.players[0].hand
        if not hand:
            return

        cw, ch = self.S(80), self.S(100)
        n = len(hand)
        usable_w = self.W - self.SX(250)
        spread = min(self.S(60), usable_w // max(n, 1))
        spread = max(self.S(20), spread)
        total_w = spread * (n - 1) + cw
        sx = cx - total_w // 2
        sy = self.H - self.SY(170)

        for i, card in enumerate(hand):
            sel = card in self.selected
            x = sx + i * spread
            y = sy - (self.S(14) if sel else 0)
            draw_face(surf, self.fonts, x, y, cw, ch, str(card), selected=sel, show_corner_suit=False, big_suit_scale=1.45)
            click_w = spread if i < n - 1 else cw
            self.hand_rects.append((pygame.Rect(x, y, click_w, ch), card))

    def _draw_panel(self, surf, x, y, cur):
        # Game Info size changes with player count:
        # 2 players = shorter, 3 players = medium, 4 players = taller.
        # Same base width as the New Game button.
        pw = self.S(102)
        ph = self.S(126 + len(self.players) * 20)
        panel = pygame.Rect(x, y, pw, ph)
        rrect(surf, C_PANEL_BG, panel, r=self.S(10), bw=self.S(2), bc=C_RING)

        mid = x + pw // 2
        blit_text(surf, "Game Info", self.fonts["sm"], C_GOLD, mid, y + self.S(14), anchor="center")
        blit_text(surf, f"Round {self.game.round_number}", self.fonts["bodyb"], C_WHITE, mid, y + self.S(40), anchor="center")
        blit_text(surf, "Turn", self.fonts["sm"], C_TXT_LIGHT, mid, y + self.S(68), anchor="center")
        blit_text(surf, cur.name, self.fonts["bodyb"], C_GOLD, mid, y + self.S(87), anchor="center")

        blit_text(surf, "Score", self.fonts["sm"], C_TXT_LIGHT, mid, y + self.S(114), anchor="center")
        start_y = y + self.S(136)

        for i, p in enumerate(self.players):
            score = getattr(p, "total_score", getattr(p, "score", 0))
            score_txt = f"{p.name}: {score}"
            blit_text(
                surf,
                score_txt,
                self.fonts["sm"],
                C_GOLD if p == cur else C_TXT_MUTED,
                mid,
                start_y + i * self.S(18),
                anchor="center"
            )

    def _draw_log(self, surf, W, H):
        lx = self.SX(110)
        ly = H - self.SY(52)
        lw = W - self.SX(220)
        lh = self.S(34)
        rrect(surf, C_NOTICE_BG, pygame.Rect(lx, ly, lw, lh), r=self.S(8), bw=self.S(2), bc=C_RING)

        shown = self.messages[-1:]
        msg = shown[0] if shown else ""
        blit_text(surf, msg[:110], self.fonts["sm"], C_GOLD, lx + self.S(10), ly + self.S(10), anchor="topleft")

    def _draw_notice(self, surf, W):
        nr = pygame.Rect(W // 2 - self.S(180), self.SY(46), self.S(360), self.S(30))
        rrect(surf, (15, 8, 3), nr, r=self.S(8), bw=self.S(2), bc=C_GOLD)
        blit_text(surf, self.notice_txt, self.fonts["sm"], C_GOLD, W // 2, nr.centery, anchor="center")


def run_gui():
    gui = Big2GUI()
    gui.run()
