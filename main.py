import pygame
import sys
import random
import math
import time
import array

# Pygame & Mixer Initialization
pygame.init()

# Audio Hardware Initialize Safely
try:
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
except Exception as mixer_err:
    print(f"Mixer initialization error: {mixer_err}")

# Screen Setup - Stable Windowed Mode
try:
    INFO = pygame.display.Info()
    SCREEN_WIDTH = int(INFO.current_w * 0.95) if (INFO and INFO.current_w) else 480
    SCREEN_HEIGHT = int(INFO.current_h * 0.90) if (INFO and INFO.current_h) else 800
except:
    SCREEN_WIDTH = 480
    SCREEN_HEIGHT = 800

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake Game Pro Master")

clock = pygame.time.Clock()

# Colors
GREEN = (34, 139, 34)
DARK_GREEN = (15, 75, 15)
GRID_LINE = (25, 100, 25)
WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
RED = (230, 30, 30)
YELLOW = (255, 215, 0)
ORANGE = (255, 130, 0)
GRAY = (100, 100, 100)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (180, 180, 180)
BLUE = (30, 144, 255)

SNAKE_COLOR = (60, 255, 60)

# Safe Font Loading System (Prevents crash if font doesn't exist)
def get_safe_font(size, bold=False):
    try:
        return pygame.font.SysFont('Arial', int(size), bold=bold)
    except:
        return pygame.font.Font(pygame.font.get_default_font(), int(size))

font_title = get_safe_font(SCREEN_WIDTH * 0.085, bold=True)
font_large = get_safe_font(SCREEN_WIDTH * 0.065, bold=True)
font_medium = get_safe_font(SCREEN_WIDTH * 0.05, bold=True)
font_small = get_safe_font(SCREEN_WIDTH * 0.038, bold=True)
font_huge_d = get_safe_font(SCREEN_WIDTH * 0.15, bold=True)

# Grid Configuration
GRID_W, GRID_H = 14, 16
BLOCK_SIZE = int(SCREEN_WIDTH * 0.88) // GRID_W
GAME_W = GRID_W * BLOCK_SIZE
GAME_H = GRID_H * BLOCK_SIZE
GAME_X = (SCREEN_WIDTH - GAME_W) // 2
GAME_Y = int(SCREEN_HEIGHT * 0.04)

# Screen State Engine
current_screen = "menu"
score = 0
game_over = False
is_paused = False
show_exit_dialog = False  

# Sub-popup Engine states inside Info Screen
active_info_popup = None  # "credits" or "bug_status"

START_SPEED = 280
current_speed = START_SPEED

sound_val = 0.8
music_val = 0.5  
loading_start_time = 0
loading_pct = 0
last_loading_sound_pct = -1  

snake = []
snake_dir = (1, 0)
food_pos = (4, 4)

# --- AUTOMATIC INTERNAL SOUND GENERATOR (SAFE WRAPPED) ---
def build_synth_sound(frequency, duration_ms, is_square=False, volume_factor=1.0):
    try:
        sample_rate = 44100
        num_samples = int(sample_rate * (duration_ms / 1000.0))
        raw_buffer = array.array('h', [0] * (num_samples * 2)) 
        for i in range(num_samples):
            t = float(i) / sample_rate
            if is_square:
                val = 16000 if math.sin(2.0 * math.pi * frequency * t) >= 0 else -16000
            else:
                val = int(24000.0 * math.sin(2.0 * math.pi * frequency * t))
            if num_samples - i < 400:
                val = int(val * ((num_samples - i) / 400.0))
            val = int(val * volume_factor)
            raw_buffer[i * 2] = val
            raw_buffer[i * 2 + 1] = val
        return pygame.mixer.Sound(buffer=raw_buffer)
    except Exception as e:
        print(f"Sound Gen Shielded: {e}")
        return None

eat_sound = build_synth_sound(659.25, 120, is_square=False)   
crash_sound = build_synth_sound(120.0, 450, is_square=True)    
click_sound = build_synth_sound(880.0, 35, is_square=False)    
load_tick_sound = build_synth_sound(440.0, 50, is_square=False, volume_factor=0.6) 

# --- AUTOMATIC RETRO MUSIC SYSTEM ---
bg_notes = [261.63, 293.66, 329.63, 349.23, 392.00, 349.23, 329.63, 293.66] 
current_note_index = 0
last_note_time = 0
note_duration = 250 

music_tones = []
for note in bg_notes:
    tone = build_synth_sound(note, note_duration - 20, is_square=True, volume_factor=0.15)
    if tone: music_tones.append(tone)

def play_background_music_tick():
    global last_note_time, current_note_index
    if not music_tones or not music_val > 0 or current_screen == "settings":
        return
    current_time = pygame.time.get_ticks()
    if current_time - last_note_time >= note_duration:
        try:
            tone = music_tones[current_note_index]
            if tone:
                tone.set_volume(music_val)
                tone.play()
            current_note_index = (current_note_index + 1) % len(music_tones)
            last_note_time = current_time
        except:
            pass

def update_volumes():
    try:
        if eat_sound: eat_sound.set_volume(sound_val)
        if crash_sound: crash_sound.set_volume(sound_val)
        if click_sound: click_sound.set_volume(sound_val)
        if load_tick_sound: load_tick_sound.set_volume(sound_val)
    except:
        pass

update_volumes()

SNAKE_CLOCK = pygame.USEREVENT + 1
pygame.time.set_timer(SNAKE_CLOCK, START_SPEED)

def respawn_game():
    global snake, snake_dir, food_pos, score, game_over, is_paused, current_speed
    score = 0
    game_over = False
    is_paused = False
    current_speed = START_SPEED
    pygame.time.set_timer(SNAKE_CLOCK, current_speed)
    start_x = random.randint(3, GRID_W - 4)
    start_y = random.randint(3, GRID_H - 4)
    snake = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]
    snake_dir = random.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])
    respawn_food()

def respawn_food():
    global food_pos
    while True:
        pos = (random.randint(0, GRID_W - 1), random.randint(0, GRID_H - 1))
        if pos not in snake:
            food_pos = pos
            break

# PERFECT ISOMETRIC 3D PUSH BUTTON
def draw_drawing_3d_button(surf, text, font, x, y, w, h, base_color, shadow_color, text_color, pressed=False):
    thickness = 8
    if pressed:
        ox, oy = x + thickness, y + thickness
        pygame.draw.rect(surf, base_color, (ox, oy, w, h), border_radius=6)
        pygame.draw.rect(surf, BLACK, (ox, oy, w, h), 3, border_radius=6)
        if text != "":
            txt_surf = font.render(text, True, text_color)
            txt_rect = txt_surf.get_rect(center=(ox + w//2, oy + h//2))
            surf.blit(txt_surf, txt_rect)
    else:
        pts_side = [(x + w, y), (x + w + thickness, y + thickness), (x + w + thickness, y + h + thickness), (x + w, y + h)]
        pts_bottom = [(x, y + h), (x + thickness, y + h + thickness), (x + w + thickness, y + h + thickness), (x + w, y + h)]
        pygame.draw.polygon(surf, shadow_color, pts_side)
        pygame.draw.polygon(surf, shadow_color, pts_bottom)
        pygame.draw.polygon(surf, BLACK, pts_side, 3)
        pygame.draw.polygon(surf, BLACK, pts_bottom, 3)
        pygame.draw.rect(surf, base_color, (x, y, w, h), border_radius=6)
        pygame.draw.rect(surf, BLACK, (x, y, w, h), 3, border_radius=6)
        if text != "":
            txt_surf = font.render(text, True, text_color)
            txt_rect = txt_surf.get_rect(center=(x + w//2, y + h//2))
            surf.blit(txt_surf, txt_rect)

# DYNAMIC MECHANICAL GEAR VECTOR GENERATOR
def draw_gear_icon(surf, cx, cy, r, pressed=False):
    offset = 5 if pressed else 0
    ncx, ncy = cx + offset, cy + offset
    if not pressed:
        pygame.draw.circle(surf, BLACK, (cx + 4, cy + 4), r)
    pygame.draw.circle(surf, LIGHT_GRAY if not pressed else GRAY, (ncx, ncy), r)
    pygame.draw.circle(surf, BLACK, (ncx, ncy), r, 3)
    num_teeth = 8
    for i in range(num_teeth):
        angle = i * (2 * math.pi / num_teeth)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        p1 = (ncx + (r - 2) * cos_a - 5 * sin_a, ncy + (r - 2) * sin_a + 5 * cos_a)
        p2 = (ncx + (r + 8) * cos_a - 4 * sin_a, ncy + (r + 8) * sin_a + 4 * cos_a)
        p3 = (ncx + (r + 8) * cos_a + 4 * sin_a, ncy + (r + 8) * sin_a - 4 * cos_a)
        p4 = (ncx + (r - 2) * cos_a + 5 * sin_a, ncy + (r - 2) * sin_a - 5 * cos_a)
        pygame.draw.polygon(surf, LIGHT_GRAY if not pressed else GRAY, [p1, p2, p3, p4])
        pygame.draw.polygon(surf, BLACK, [p1, p2, p3, p4], 2)
    pygame.draw.circle(surf, LIGHT_GRAY if not pressed else GRAY, (ncx, ncy), r - 1)
    pygame.draw.circle(surf, DARK_GRAY, (ncx, ncy), int(r * 0.35))
    pygame.draw.circle(surf, BLACK, (ncx, ncy), int(r * 0.35), 2)

def draw_retro_bug(surf, cx, cy):
    pygame.draw.line(surf, RED, (cx - 25, cy - 10), (cx + 25, cy + 10), 3)
    pygame.draw.line(surf, RED, (cx - 25, cy), (cx + 25, cy), 3)
    pygame.draw.line(surf, RED, (cx - 25, cy + 10), (cx + 25, cy - 10), 3)
    pygame.draw.ellipse(surf, ORANGE, (cx - 14, cy - 18, 28, 36))
    pygame.draw.ellipse(surf, BLACK, (cx - 14, cy - 18, 28, 36), 2)
    pygame.draw.circle(surf, YELLOW, (cx, cy - 18), 10)
    pygame.draw.circle(surf, BLACK, (cx, cy - 18), 10, 2)
    pygame.draw.circle(surf, WHITE, (cx - 4, cy - 22), 3)
    pygame.draw.circle(surf, WHITE, (cx + 4, cy - 22), 3)
    pygame.draw.circle(surf, BLACK, (cx - 4, cy - 22), 1)
    pygame.draw.circle(surf, BLACK, (cx + 4, cy - 22), 1)
    pygame.draw.line(surf, BLACK, (cx - 4, cy - 26), (cx - 10, cy - 34), 2)
    pygame.draw.line(surf, BLACK, (cx + 4, cy - 26), (cx + 10, cy - 34), 2)

# Dynamic Scale Mapping
play_btn_w, play_btn_h = int(SCREEN_WIDTH * 0.58), int(SCREEN_HEIGHT * 0.085)
play_btn_x, play_btn_y = (SCREEN_WIDTH - play_btn_w) // 2, int(SCREEN_HEIGHT * 0.48)
btn_play_rect = pygame.Rect(play_btn_x, play_btn_y, play_btn_w, play_btn_h)

set_cx, set_cy, set_r = int(SCREEN_WIDTH * 0.16), int(SCREEN_HEIGHT * 0.09), 26
info_cx, info_cy, info_r = set_cx + int(SCREEN_WIDTH * 0.22), set_cy, 24

panel_w, panel_h = int(SCREEN_WIDTH * 0.85), int(SCREEN_HEIGHT * 0.58)
panel_x, panel_y = (SCREEN_WIDTH - panel_w) // 2, (SCREEN_HEIGHT - panel_h) // 2

slide_w = int(panel_w * 0.8)
slide_h = 24
slide_x = panel_x + (panel_w - slide_w) // 2
sound_slide_y = panel_y + 155
music_slide_y = panel_y + 265

sound_rect = pygame.Rect(slide_x - 15, sound_slide_y - 15, slide_w + 30, slide_h + 30)
music_rect = pygame.Rect(slide_x - 15, music_slide_y - 15, slide_w + 30, slide_h + 30)

# Layout for Info Screen (Only 2 interactable boxes)
box_width = int(panel_w * 0.88)
box_height = int(panel_h * 0.18)
box_x_coord = panel_x + (panel_w - box_width) // 2

rect_info_box2 = pygame.Rect(box_x_coord, panel_y + 140, box_width, box_height) # 'D' box
rect_info_box3 = pygame.Rect(box_x_coord, panel_y + 260, box_width, box_height) # Bug box

# Sub Popup Inside Info Setup
pop_w, pop_h = int(SCREEN_WIDTH * 0.80), int(SCREEN_HEIGHT * 0.45)
pop_x, pop_y = (SCREEN_WIDTH - pop_w) // 2, (SCREEN_HEIGHT - pop_h) // 2
btn_ok_w, btn_ok_h = int(pop_w * 0.35), int(pop_h * 0.18)
btn_ok_rect = pygame.Rect((SCREEN_WIDTH - btn_ok_w) // 2, pop_y + pop_h - btn_ok_h - 20, btn_ok_w, btn_ok_h)

exit_box_w, exit_box_h = int(SCREEN_WIDTH * 0.85), int(SCREEN_HEIGHT * 0.30)
exit_box_x = (SCREEN_WIDTH - exit_box_w) // 2
exit_box_y = (SCREEN_HEIGHT - exit_box_h) // 2

exit_btn_w, exit_btn_h = int(exit_box_w * 0.36), int(exit_box_h * 0.24)
exit_btn_y = exit_box_y + exit_box_h - exit_btn_h - 28
btn_yes_rect = pygame.Rect(exit_box_x + 35, exit_btn_y, exit_btn_w, exit_btn_h)
btn_no_rect = pygame.Rect(exit_box_x + exit_box_w - exit_btn_w - 35, exit_btn_y, exit_btn_w, exit_btn_h)

dpad_sz = int(SCREEN_WIDTH * 0.16)
dpad_cx = int(SCREEN_WIDTH * 0.26)
dpad_cy = SCREEN_HEIGHT - int(SCREEN_HEIGHT * 0.18)

dpad_rects = {
    "UP": pygame.Rect(dpad_cx - dpad_sz//2, dpad_cy - dpad_sz*1.5, dpad_sz, dpad_sz),
    "DOWN": pygame.Rect(dpad_cx - dpad_sz//2, dpad_cy + dpad_sz//2, dpad_sz, dpad_sz),
    "LEFT": pygame.Rect(dpad_cx - dpad_sz*1.5, dpad_cy - dpad_sz//2, dpad_sz, dpad_sz),
    "RIGHT": pygame.Rect(dpad_cx + dpad_sz//2, dpad_cy - dpad_sz//2, dpad_sz, dpad_sz)
}

act_w = int(SCREEN_WIDTH * 0.36)
act_h = int(SCREEN_HEIGHT * 0.072)
act_x = int(SCREEN_WIDTH * 0.56)
act_gap = 18 
act_y1 = dpad_cy - dpad_sz*1.2
act_y2 = act_y1 + act_h + act_gap

btn_pause_rect = pygame.Rect(act_x, act_y1, act_w, act_h)
btn_reset_rect = pygame.Rect(act_x, act_y2, act_w, act_h)

gov_btn_w = int(SCREEN_WIDTH * 0.36)
gov_btn_h = int(SCREEN_HEIGHT * 0.07)
gov_btn_y = (SCREEN_HEIGHT // 2) + 60
btn_restart_rect = pygame.Rect((SCREEN_WIDTH // 2) - gov_btn_w - 15, gov_btn_y, gov_btn_w, gov_btn_h)
btn_home_rect = pygame.Rect((SCREEN_WIDTH // 2) + 15, gov_btn_y, gov_btn_w, gov_btn_h)

button_press_states = {
    "PLAY": False, "UP": False, "DOWN": False, "LEFT": False, "RIGHT": False,
    "PAUSE": False, "RESET": False, "RESTART": False, "HOME": False,
    "SET": False, "INFO": False, "CLOSE_PANEL": False, "YES": False, "NO": False, "OK_BTN": False
}

def draw_menu_background(surf):
    surf.fill(GREEN)
    box_w, box_h = int(SCREEN_WIDTH * 0.86), int(SCREEN_HEIGHT * 0.14)
    box_x, box_y = (SCREEN_WIDTH - box_w) // 2, int(SCREEN_HEIGHT * 0.22)
    draw_drawing_3d_button(surf, "SNAKE GAME", font_title, box_x, box_y, box_w, box_h, DARK_GRAY, BLACK, YELLOW)
    draw_gear_icon(surf, set_cx, set_cy, set_r, button_press_states["SET"])
    info_offset = 5 if button_press_states["INFO"] else 0
    pygame.draw.circle(surf, BLACK, (info_cx + 3, info_cy + 3), info_r)
    pygame.draw.circle(surf, BLUE if not button_press_states["INFO"] else DARK_GRAY, (info_cx + info_offset, info_cy + info_offset), info_r)
    pygame.draw.circle(surf, BLACK, (info_cx + info_offset, info_cy + info_offset), info_r, 3)
    surf.blit(font_medium.render("i", True, WHITE), (info_cx - 5 + info_offset, info_cy - 14 + info_offset))

# Master Process Loop
while True:
    mx, my = pygame.mouse.get_pos()
    
    if current_screen in ["menu", "loading", "game"] and not show_exit_dialog:
        play_background_music_tick()
        
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                show_exit_dialog = True
                continue
                
        if event.type == pygame.MOUSEBUTTONDOWN:
            if show_exit_dialog:
                if btn_yes_rect.collidepoint(mx, my): button_press_states["YES"] = True
                if btn_no_rect.collidepoint(mx, my): button_press_states["NO"] = True
                continue  
                
            if current_screen == "menu":
                if math.hypot(mx - set_cx, my - set_cy) < set_r + 6:
                    button_press_states["SET"] = True
                    if click_sound: 
                        try: click_sound.play()
                        except: pass
                elif math.hypot(mx - info_cx, my - info_cy) < info_r:
                    button_press_states["INFO"] = True
                    if click_sound: 
                        try: click_sound.play()
                        except: pass
                elif btn_play_rect.collidepoint(mx, my):
                    button_press_states["PLAY"] = True
                    if click_sound: 
                        try: click_sound.play()
                        except: pass
                    
            elif current_screen == "settings":
                if sound_rect.collidepoint(mx, my):
                    sound_val = max(0.0, min(1.0, (mx - slide_x) / slide_w))
                    update_volumes()
                elif music_rect.collidepoint(mx, my):
                    music_val = max(0.0, min(1.0, (mx - slide_x) / slide_w))
                
                back_w, back_h = int(SCREEN_WIDTH * 0.4), int(SCREEN_HEIGHT * 0.065)
                back_y = panel_y + panel_h - back_h - 25
                back_x = (SCREEN_WIDTH - back_w) // 2
                if back_x <= mx <= back_x + back_w and back_y <= my <= back_y + back_h:
                    button_press_states["CLOSE_PANEL"] = True
                    if click_sound: 
                        try: click_sound.play()
                        except: pass
                    
            elif current_screen == "info":
                if active_info_popup is not None:
                    if btn_ok_rect.collidepoint(mx, my):
                        button_press_states["OK_BTN"] = True
                        if click_sound: 
                            try: click_sound.play()
                            except: pass
                    continue

                if rect_info_box2.collidepoint(mx, my):
                    active_info_popup = "credits"
                    if click_sound: 
                        try: click_sound.play()
                        except: pass
                elif rect_info_box3.collidepoint(mx, my):
                    active_info_popup = "bug_status"
                    if click_sound: 
                        try: click_sound.play()
                        except: pass
                
                back_w, back_h = int(SCREEN_WIDTH * 0.4), int(SCREEN_HEIGHT * 0.065)
                back_y = panel_y + panel_h - back_h - 25
                back_x = (SCREEN_WIDTH - back_w) // 2
                if back_x <= mx <= back_x + back_w and back_y <= my <= back_y + back_h:
                    button_press_states["CLOSE_PANEL"] = True
                    if click_sound: 
                        try: click_sound.play()
                        except: pass
                    
            elif current_screen == "game":
                if game_over:
                    if btn_restart_rect.collidepoint(mx, my): 
                        button_press_states["RESTART"] = True
                        if click_sound: 
                            try: click_sound.play()
                            except: pass
                    if btn_home_rect.collidepoint(mx, my): 
                        button_press_states["HOME"] = True
                        if click_sound: 
                            try: click_sound.play()
                            except: pass
                else:
                    for d, rect in dpad_rects.items():
                        if rect.collidepoint(mx, my):
                            button_press_states[d] = True
                            if click_sound: 
                                try: click_sound.play()
                                except: pass
                            if d == "UP" and snake_dir != (0, 1): snake_dir = (0, -1)
                            elif d == "DOWN" and snake_dir != (0, -1): snake_dir = (0, 1)
                            elif d == "LEFT" and snake_dir != (1, 0): snake_dir = (-1, 0)
                            elif d == "RIGHT" and snake_dir != (-1, 0): snake_dir = (1, 0)
                    if btn_pause_rect.collidepoint(mx, my): 
                        button_press_states["PAUSE"] = True
                        if click_sound: 
                            try: click_sound.play()
                            except: pass
                    if btn_reset_rect.collidepoint(mx, my): 
                        button_press_states["RESET"] = True
                        if click_sound: 
                            try: click_sound.play()
                            except: pass

        if event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
            if not show_exit_dialog and current_screen == "settings":
                if sound_rect.collidepoint(mx, my):
                    sound_val = max(0.0, min(1.0, (mx - slide_x) / slide_w))
                    update_volumes()
                elif music_rect.collidepoint(mx, my):
                    music_val = max(0.0, min(1.0, (mx - slide_x) / slide_w))

        if event.type == pygame.MOUSEBUTTONUP:
            if show_exit_dialog:
                if button_press_states["YES"]: pygame.quit(); sys.exit()
                if button_press_states["NO"]: 
                    show_exit_dialog = False
                    if click_sound: 
                        try: click_sound.play()
                        except: pass
                button_press_states["YES"] = False; button_press_states["NO"] = False
                continue

            if current_screen == "menu":
                if button_press_states["SET"]: current_screen = "settings"
                if button_press_states["INFO"]: current_screen = "info"; active_info_popup = None
                if button_press_states["PLAY"]:
                    current_screen = "loading"
                    loading_start_time = time.time()
                    loading_pct = 0
                    last_loading_sound_pct = -1
            elif current_screen == "info":
                if button_press_states["OK_BTN"]:
                    active_info_popup = None
                elif button_press_states["CLOSE_PANEL"]:
                    current_screen = "menu"
            elif current_screen == "settings" and button_press_states["CLOSE_PANEL"]:
                current_screen = "menu"
            elif current_screen == "game":
                if game_over:
                    if button_press_states["RESTART"]: respawn_game()
                    if button_press_states["HOME"]: current_screen = "menu"
                else:
                    if button_press_states["PAUSE"]: is_paused = not is_paused
                    if button_press_states["RESET"]: respawn_game()

            for key in button_press_states: button_press_states[key] = False

        if event.type == SNAKE_CLOCK and current_screen == "game" and not show_exit_dialog:
            if not game_over and not is_paused:
                hx, hy = snake[0]
                new_head = (hx + snake_dir[0], hy + snake_dir[1])
                if (new_head[0] < 0 or new_head[0] >= GRID_W or new_head[1] < 0 or new_head[1] >= GRID_H or new_head in snake):
                    game_over = True
                    if crash_sound: 
                        try: crash_sound.play()
                        except: pass
                else:
                    snake.insert(0, new_head)
                    if new_head == food_pos:
                        score += 10
                        if eat_sound: 
                            try: eat_sound.play()
                            except: pass
                        respawn_food()
                        if current_speed > 100:
                            current_speed -= 12
                            pygame.time.set_timer(SNAKE_CLOCK, current_speed)
                    else:
                        snake.pop()

    # --- RENDER STAGE ---
    if current_screen == "menu":
        draw_menu_background(screen)
        draw_drawing_3d_button(screen, "PLAY", font_large, btn_play_rect.x, btn_play_rect.y, btn_play_rect.width, btn_play_rect.height, (0, 210, 0), (0, 110, 0), WHITE, button_press_states["PLAY"])
        
    elif current_screen == "loading":
        draw_menu_background(screen)
        draw_drawing_3d_button(screen, "PLAY", font_large, btn_play_rect.x, btn_play_rect.y, btn_play_rect.width, btn_play_rect.height, (0, 210, 0), (0, 110, 0), WHITE, False)
        blur_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        blur_overlay.fill((0, 0, 0, 160)) 
        screen.blit(blur_overlay, (0, 0))
        
        elapsed = time.time() - loading_start_time
        if elapsed < 0.8: loading_pct = 25
        elif elapsed < 1.5: loading_pct = 55
        elif elapsed < 2.2: loading_pct = 80
        elif elapsed < 2.8: loading_pct = 100
        else: current_screen = "game"; respawn_game()
        
        if loading_pct != last_loading_sound_pct:
            if load_tick_sound: 
                try: load_tick_sound.play()
                except: pass
            last_loading_sound_pct = loading_pct
        
        lb_w, lb_h = int(SCREEN_WIDTH * 0.78), 34
        lb_x, lb_y = (SCREEN_WIDTH - lb_w) // 2, (SCREEN_HEIGHT // 2) - 17
        pygame.draw.rect(screen, BLACK, (lb_x, lb_y, lb_w, lb_h), 4, border_radius=6)
        pygame.draw.rect(screen, DARK_GRAY, (lb_x+2, lb_y+2, lb_w-4, lb_h-4), border_radius=4)
        progress_fill = int((lb_w - 8) * (loading_pct / 100))
        if progress_fill > 0:
            pygame.draw.rect(screen, YELLOW, (lb_x + 4, lb_y + 4, progress_fill, lb_h - 8), border_radius=4)
        loading_text = font_medium.render("LOADING...", True, WHITE)
        screen.blit(loading_text, loading_text.get_rect(center=(SCREEN_WIDTH//2, lb_y - 35)))
            
    elif current_screen in ["settings", "info"]:
        draw_menu_background(screen)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        screen.blit(overlay, (0, 0))
        
        draw_drawing_3d_button(screen, "", font_medium, panel_x, panel_y, panel_w, panel_h, DARK_GRAY, BLACK, WHITE)
        
        if current_screen == "settings":
            screen.blit(font_large.render("SETTINGS", True, YELLOW), (panel_x + 30, panel_y + 25))
            screen.blit(font_small.render(f"GAME SOUND: {int(sound_val*100)}%", True, WHITE), (panel_x + 35, panel_y + 115))
            pygame.draw.rect(screen, BLACK, (slide_x, sound_slide_y, slide_w, slide_h), border_radius=4)
            pygame.draw.rect(screen, GRAY, (slide_x+2, sound_slide_y+2, slide_w-4, slide_h-4), border_radius=3)
            if sound_val > 0:
                pygame.draw.rect(screen, GREEN, (slide_x+2, sound_slide_y+2, int((slide_w-4)*sound_val), slide_h-4), border_radius=3)
            
            sknob_x = slide_x + int((slide_w - 4) * sound_val)
            sknob_y = sound_slide_y + (slide_h // 2)
            pygame.draw.circle(screen, BLACK, (sknob_x + 2, sknob_y + 2), 16)
            pygame.draw.circle(screen, WHITE, (sknob_x, sknob_y), 15)
            pygame.draw.circle(screen, LIGHT_GRAY, (sknob_x, sknob_y), 11)
            pygame.draw.circle(screen, BLACK, (sknob_x, sknob_y), 15, 2)
            
            screen.blit(font_small.render(f"MUSIC VOL: {int(music_val*100)}%", True, WHITE), (panel_x + 35, panel_y + 215))
            pygame.draw.rect(screen, BLACK, (slide_x, music_slide_y, slide_w, slide_h), border_radius=4)
            pygame.draw.rect(screen, GRAY, (slide_x+2, music_slide_y+2, slide_w-4, slide_h-4), border_radius=3)
            if music_val > 0:
                pygame.draw.rect(screen, BLUE, (slide_x+2, music_slide_y+2, int((slide_w-4)*music_val), slide_h-4), border_radius=3)
            
            mknob_x = slide_x + int((slide_w - 4) * music_val)
            mknob_y = music_slide_y + (slide_h // 2)
            pygame.draw.circle(screen, BLACK, (mknob_x + 2, mknob_y + 2), 16)
            pygame.draw.circle(screen, WHITE, (mknob_x, mknob_y), 15)
            pygame.draw.circle(screen, LIGHT_GRAY, (mknob_x, mknob_y), 11)
            pygame.draw.circle(screen, BLACK, (mknob_x, mknob_y), 15, 2)
            screen.blit(font_small.render("DIGITAL SYNTH ACTIVE (NO FILES REQUIRED)", True, LIGHT_GRAY), (panel_x + 35, panel_y + 320))
            
        elif current_screen == "info":
            # HEADER: SNAKE GAME VERSION 1.0
            txt_ver = font_medium.render("SNAKE GAME VERSION 1.0", True, YELLOW)
            screen.blit(txt_ver, txt_ver.get_rect(center=(panel_x + panel_w//2, panel_y + 65)))
            
            # 'D' box
            pygame.draw.rect(screen, BLACK, rect_info_box2, border_radius=8)
            txt_d = font_huge_d.render("D", True, YELLOW)
            screen.blit(txt_d, txt_d.get_rect(center=rect_info_box2.center))
            
            # Bug Box
            pygame.draw.rect(screen, BLACK, rect_info_box3, border_radius=8)
            draw_retro_bug(screen, rect_info_box3.centerx, rect_info_box3.centery)
            
            # --- SUB POPUPS ---
            if active_info_popup == "credits":
                pop_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                pop_overlay.fill((0, 0, 0, 180))
                screen.blit(pop_overlay, (0, 0))
                
                draw_drawing_3d_button(screen, "", font_medium, pop_x, pop_y, pop_w, pop_h, DARK_GRAY, BLACK, WHITE)
                
                credits_lines = [
                    "CODE BY: ANMOL",
                    "MUSIC BY: ANMOL",
                    "INTERFACE DESIGN: ANMOL",
                    "GAME DIRECTOR: ANMOL"
                ]
                line_y = pop_y + 50
                for line in credits_lines:
                    txt_rend = font_medium.render(line, True, YELLOW if "CODE" in line else WHITE)
                    screen.blit(txt_rend, txt_rend.get_rect(center=(SCREEN_WIDTH//2, line_y)))
                    line_y += 50
                    
                draw_drawing_3d_button(screen, "OK", font_medium, btn_ok_rect.x, btn_ok_rect.y, btn_ok_rect.width, btn_ok_rect.height, GREEN, (10, 110, 10), WHITE, button_press_states["OK_BTN"])
                
            elif active_info_popup == "bug_status":
                pop_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                pop_overlay.fill((0, 0, 0, 180))
                screen.blit(pop_overlay, (0, 0))
                
                draw_drawing_3d_button(screen, "", font_medium, pop_x, pop_y, pop_w, pop_h, DARK_GRAY, BLACK, WHITE)
                txt_bug = font_medium.render("Some bugs have been fixed.", True, WHITE)
                screen.blit(txt_bug, txt_bug.get_rect(center=(SCREEN_WIDTH//2, pop_y + int(pop_h * 0.35))))
                draw_drawing_3d_button(screen, "OK", font_medium, btn_ok_rect.x, btn_ok_rect.y, btn_ok_rect.width, btn_ok_rect.height, GREEN, (10, 110, 10), WHITE, button_press_states["OK_BTN"])

        if active_info_popup is None:
            back_w, back_h = int(SCREEN_WIDTH * 0.4), int(SCREEN_HEIGHT * 0.065)
            back_y = panel_y + panel_h - back_h - 20
            back_x = (SCREEN_WIDTH - back_w) // 2
            draw_drawing_3d_button(screen, "BACK", font_medium, back_x, back_y, back_w, back_h, RED, (120, 10, 10), WHITE, button_press_states["CLOSE_PANEL"])

    elif current_screen == "game":
        screen.fill(GREEN)
        pygame.draw.rect(screen, BLACK, (GAME_X-4, GAME_Y-4, GAME_W+8, GAME_H+8), 4)
        pygame.draw.rect(screen, DARK_GREEN, (GAME_X, GAME_Y, GAME_W, GAME_H))
        
        for col in range(GRID_W + 1): pygame.draw.line(screen, GRID_LINE, (GAME_X + col*BLOCK_SIZE, GAME_Y), (GAME_X + col*BLOCK_SIZE, GAME_Y + GAME_H), 1)
        for row in range(GRID_H + 1): pygame.draw.line(screen, GRID_LINE, (GAME_X, GAME_Y + row*BLOCK_SIZE), (GAME_X + GAME_W, GAME_Y + row*BLOCK_SIZE), 1)
            
        ax_p = GAME_X + food_pos[0]*BLOCK_SIZE + BLOCK_SIZE//2
        ay_p = GAME_Y + food_pos[1]*BLOCK_SIZE + BLOCK_SIZE//2
        pygame.draw.circle(screen, RED, (ax_p, ay_p), BLOCK_SIZE//2 - 2)
        
        for index in range(len(snake) - 1):
            c1x = GAME_X + snake[index][0]*BLOCK_SIZE + BLOCK_SIZE//2
            c1y = GAME_Y + snake[index][1]*BLOCK_SIZE + BLOCK_SIZE//2
            c2x = GAME_X + snake[index+1][0]*BLOCK_SIZE + BLOCK_SIZE//2
            c2y = GAME_Y + snake[index+1][1]*BLOCK_SIZE + BLOCK_SIZE//2
            pygame.draw.line(screen, SNAKE_COLOR, (c1x, c1y), (c2x, c2y), BLOCK_SIZE)

        for index, segment in enumerate(snake):
            cx = GAME_X + segment[0]*BLOCK_SIZE + BLOCK_SIZE//2
            cy = GAME_Y + segment[1]*BLOCK_SIZE + BLOCK_SIZE//2
            radius = BLOCK_SIZE // 2
            pygame.draw.circle(screen, SNAKE_COLOR, (cx, cy), radius)
            
            if index == 0:
                eye_radius = 6
                pupil_radius = 2.5
                if snake_dir == (1, 0): e1_pos = (cx + 3, cy - 7); e2_pos = (cx + 3, cy + 7)
                elif snake_dir == (-1, 0): e1_pos = (cx - 3, cy - 7); e2_pos = (cx - 3, cy + 7)
                elif snake_dir == (0, -1): e1_pos = (cx - 7, cy - 3); e2_pos = (cx + 7, cy - 3)
                else: e1_pos = (cx - 7, cy + 3); e2_pos = (cx + 7, cy + 3)
                
                pygame.draw.circle(screen, WHITE, e1_pos, eye_radius)
                pygame.draw.circle(screen, WHITE, e2_pos, eye_radius)
                pygame.draw.circle(screen, BLACK, e1_pos, eye_radius, 1)
                pygame.draw.circle(screen, BLACK, e2_pos, eye_radius, 1)
                pygame.draw.circle(screen, BLACK, e1_pos, pupil_radius)
                pygame.draw.circle(screen, BLACK, e2_pos, pupil_radius)

        screen.blit(font_medium.render(f"SCORE: {score}", True, WHITE), (GAME_X, GAME_Y + GAME_H + 8))

        for d, r in dpad_rects.items():
            draw_drawing_3d_button(screen, "", font_small, r.x, r.y, r.width, r.height, (0, 210, 0), (0, 100, 0), WHITE, button_press_states[d])
            shift = 8 if button_press_states[d] else 0
            bx, by = r.x + r.width//2 + shift, r.y + r.height//2 + shift
            if d == "UP": pygame.draw.polygon(screen, WHITE, [(bx, by-10), (bx-8, by+6), (bx+8, by+6)])
            elif d == "DOWN": pygame.draw.polygon(screen, WHITE, [(bx, by+10), (bx-8, by-6), (bx+8, by-6)])
            elif d == "LEFT": pygame.draw.polygon(screen, WHITE, [(bx-10, by), (bx+6, by-8), (bx+6, by+8)])
            elif d == "RIGHT": pygame.draw.polygon(screen, WHITE, [(bx+10, by), (bx-6, by-8), (bx-6, by+8)])
            
        draw_drawing_3d_button(screen, "PAUSE", font_medium, btn_pause_rect.x, btn_pause_rect.y, btn_pause_rect.width, btn_pause_rect.height, DARK_GRAY, BLACK, WHITE, button_press_states["PAUSE"])
        draw_drawing_3d_button(screen, "RESET", font_medium, btn_reset_rect.x, btn_reset_rect.y, btn_reset_rect.width, btn_reset_rect.height, DARK_GRAY, BLACK, WHITE, button_press_states["RESET"])

        if game_over:
            gov_blur = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            gov_blur.fill((0, 0, 0, 195))
            screen.blit(gov_blur, (0, 0))
            g_txt1 = font_large.render("GAME OVER", True, ORANGE)
            g_txt2 = font_large.render("GAME OVER", True, YELLOW)
            screen.blit(g_txt1, g_txt1.get_rect(center=(SCREEN_WIDTH//2 + 3, SCREEN_HEIGHT//2 - 48)))
            screen.blit(g_txt2, g_txt2.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50)))
            draw_drawing_3d_button(screen, "RESTART", font_medium, btn_restart_rect.x, btn_restart_rect.y, btn_restart_rect.width, btn_restart_rect.height, (0, 190, 0), (0, 90, 0), WHITE, button_press_states["RESTART"])
            draw_drawing_3d_button(screen, "HOME", font_medium, btn_home_rect.x, btn_home_rect.y, btn_home_rect.width, btn_home_rect.height, (220, 160, 0), (120, 80, 0), WHITE, button_press_states["HOME"])

    if show_exit_dialog:
        exit_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        exit_overlay.fill((10, 12, 10, 215))  
        screen.blit(exit_overlay, (0, 0))
        draw_drawing_3d_button(screen, "", font_medium, exit_box_x, exit_box_y, exit_box_w, exit_box_h, DARK_GRAY, BLACK, WHITE, False)
        msg_surf = font_medium.render("ARE YOU WANT TO EXIT?", True, YELLOW)
        msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH // 2, exit_box_y + 60))
        screen.blit(msg_surf, msg_rect)
        draw_drawing_3d_button(screen, "YES", font_medium, btn_yes_rect.x, btn_yes_rect.y, btn_yes_rect.width, btn_yes_rect.height, RED, (130, 10, 10), WHITE, button_press_states["YES"])
        draw_drawing_3d_button(screen, "NO", font_medium, btn_no_rect.x, btn_no_rect.y, btn_no_rect.width, btn_no_rect.height, GREEN, (10, 120, 10), WHITE, button_press_states["NO"])

    pygame.display.flip()
    clock.tick(60)
