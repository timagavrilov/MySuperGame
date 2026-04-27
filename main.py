import pygame, random, math, os, json, sys

# ВПИШИ СЮДА ПУТЬ К ПАПКЕ, КОТОРЫЙ ТЫ УЗНАЛ В ШАГЕ 1
# Например: "/storage/emulated/0/Download/"
# ОБЯЗАТЕЛЬНО оставь кавычки!
MY_PATH = "/storage/emulated/0/project/" 

os.chdir(MY_PATH)

def resource_path(relative_path):
    return os.path.join(MY_PATH, relative_path)

# Функция для вибрации на Android
def vibrate(milliseconds=50):
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        activity = PythonActivity.mActivity
        vibrator = activity.getSystemService(Context.VIBRATOR_SERVICE)
        vibrator.vibrate(milliseconds)
    except:
        pass

# --- ИНИЦИАЛИЗАЦИЯ И УНИВЕРСАЛЬНЫЕ ПУТИ ---
pygame.init()
pygame.mixer.init()

# Автоматическое определение папки с файлами (для APK и Pydroid)
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
elif "__file__" in globals():
    base_path = os.path.dirname(os.path.abspath(__file__))
else:
    base_path = "."

os.chdir(base_path)

# Дополнительная проверка для Pydroid, если файлы лежат в Pictures
android_pics_path = "/storage/emulated/0/Pictures/игра"
if os.path.exists(android_pics_path) and not getattr(sys, 'frozen', False):
    os.chdir(android_pics_path)

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font_main = pygame.font.SysFont("Arial", 40, bold=True)
font_big = pygame.font.SysFont("Arial", 60, bold=True)
font_lvl = pygame.font.SysFont("comic", 80, bold=True)
WHITE = (255, 255, 255)

# --- СОСТОЯНИЯ ИГРЫ ---
STATE_LOADING = "LOADING"
STATE_MENU = "MENU"
STATE_LEVELS = "LEVELS"
STATE_GAME = "GAME"
STATE_SHOP = "SHOP"
STATE_PAUSE = "PAUSE"
STATE_GAMEOVER = "GAMEOVER"
STATE_BRIEFING = "BRIEFING"
STATE_FREE_PLAY = "FREE_PLAY"

game_state = STATE_LOADING 
loading_progress = 0
selected_mission_id = 1 
level_page = 0

# --- ЗАГРУЗКА ДАННЫХ (JSON) ---
player_save = {
    "money": 1000,
    "unlocked_levels": 1,
    "current_skin": "hero.png",
    "bought_skins": ["hero.png"],
    "upgrades": {
        "speed": 0, "damage": 0, "invis": 0, "magnet": 0,
        "zombie": 0, "freeze": 0, "health": 0, "shield": 0   
    },
    "free_record_time": 0,
    "free_record_kills": 0
}

# Данные о скинах (цены и редкость)
SKINS_CONFIG = {
    "hero.png": {"name": "Шериф", "price": 0, "rarity": "ОБЫЧНЫЙ", "color": (200, 200, 200)},
    "samurai.png": {"name": "Самурай", "price": 500, "rarity": "ЭПИК", "color": (180, 50, 255)},
    "shaman.png": {"name": "Шаман", "price": 1500, "rarity": "ЛЕГЕНДА", "color": (255, 215, 0)}
}

def save_game():
    with open("save.json", "w") as f:
        json.dump(player_save, f)
def get_money_text(n):
    units = n % 10
    tens = n % 100
    if 11 <= tens <= 19:
        return f"{n} монет"
    if units == 1:
        return f"{n} монета"
    if 2 <= units <= 4:
        return f"{n} монеты"
    return f"{n} монет"

# Умная загрузка: исправляет старые файлы сохранения
if os.path.exists("save.json"):
    with open("save.json", "r") as f:
        try:
            old_data = json.load(f)
            # Если в старом файле нет новых ключей, берем их из шаблона выше
            for key in player_save:
                if key not in old_data:
                    old_data[key] = player_save[key]
            player_save = old_data
        except:
            pass # Если файл битый, используем стандартный player_save
# --- ДАННЫЕ ДЛЯ СВОБОДНОЙ ИГРЫ (ВСТАВЛЯТЬ ТУТ) ---
STATE_FREE_PLAY = "FREE_PLAY"
free_play_timer = 0
free_play_kills = 0
free_play_record_time = player_save.get("free_record_time", 0)
free_play_record_kills = player_save.get("free_record_kills", 0)
bonus_list = ["zombie", "magnet", "freeze", "invis"]

def start_free_play():
    global player, enemies, bullets, drops, free_play_kills, free_play_timer, game_state, enemy_bullets, current_mission
    global free_play_record_time, free_play_record_kills
    player = Player()
    enemies, bullets, drops, enemy_bullets = [], [], [], []
    free_play_kills = 0
    free_play_timer = 0
    current_mission = None
    # Синхронизируем рекорды из сохранения перед началом
    free_play_record_time = player_save.get("free_record_time", 0)
    free_play_record_kills = player_save.get("free_record_kills", 0)
    game_state = STATE_FREE_PLAY
# Исправленная функция загрузки (теперь использует ресурсный путь)
def load_img(name, size, is_bg=False):
    path = resource_path(name) # Добавляем полный путь к имени файла
    if not os.path.exists(path): 
        print(f"Ошибка: файл {name} не найден по пути {path}")
        return None
    img = pygame.image.load(path)
    if is_bg: 
        return pygame.transform.smoothscale(img.convert(), (WIDTH, HEIGHT))
    img = img.convert_alpha()
    if name != "flash.png": img.set_colorkey((255, 255, 255))
    return pygame.transform.smoothscale(img, (size, size))

# Загружаем всё через обновленную функцию
img_hero = load_img(player_save["current_skin"], 170)
img_samurai = load_img("samurai.png", 350)
img_shaman = load_img("shaman.png", 350)
img_enemy = load_img("enemy.png", 90)
img_archer = load_img("archer.png", 140)
enemy_bullets = [] 
img_elite = load_img("elite_enemy.png", 110)
img_boss = load_img("boss.png", 220)
img_coin = load_img("coin.png", 60)
img_exp = load_img("exp.png", 50)
img_flash = load_img("flash.png", 90)
img_btn_shop = load_img("btn_shop.png", 280)
img_btn_ars = load_img("btn_ars.png", 280)
img_lvl_btn = load_img("level_btn.png", 190)
img_shop_bg = load_img("shop_bg.jpg", 0, True)
img_bg = load_img("bg.jpg", 0, True)
img_boost_magnet = load_img("boost_magnet.png", 70)
img_boost_invis = load_img("boost_invis.png", 70)
img_boost_zombie = load_img("boost_zombie.png", 70)
img_boost_freeze = load_img("boost_freeze.png", 70)
img_boost_speed = load_img("boost_speed.png", 70)
img_boost_power = load_img("boost_power.png", 70)
img_boost_health = load_img("boost_health.png", 70)
img_boost_shield = load_img("boost_shield.png", 70)

# Загрузка экранов загрузки (с использованием resource_path)
img_load1_path = resource_path("loading1.png")
if os.path.exists(img_load1_path):
    img_load1 = pygame.image.load(img_load1_path).convert()
    img_load1 = pygame.transform.smoothscale(img_load1, (WIDTH, int(HEIGHT * 0.9)))
else:
    img_load1 = None

img_load2_path = resource_path("loading2.png")
if os.path.exists(img_load2_path):
    img_load2 = pygame.image.load(img_load2_path).convert()
    img_load2 = pygame.transform.smoothscale(img_load2, (WIDTH, int(HEIGHT * 0.9)))
else:
    img_load2 = None
# --- НОВЫЕ КАРТИНКИ (ШАГ 1 И 2) ---
img_shuriken = load_img("shuriken.png", 60) # Сюрикен Самурая
img_magic = load_img("magic_ball.png", 70)   # Магия Шамана
img_dust = load_img("dust.png", 100)        # Пыль при спавне

def update_hero_img():
    global img_hero, img_hero_big
    img_hero = load_img(player_save["current_skin"], 170)
    img_hero_big = load_img(player_save["current_skin"], 600)
update_hero_img()

# --- ЗАГРУЗКА МУЗЫКИ И ЗВУКОВ ---
m_path = resource_path("music.mp3")
if os.path.exists(m_path):
    pygame.mixer.music.load(m_path)
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play(-1)

# Функции звуков выстрела и килла
shot_path = resource_path("shot.wav")
snd_shot = pygame.mixer.Sound(shot_path) if os.path.exists(shot_path) else None
if snd_shot: snd_shot.set_volume(0.1)

kill_path = resource_path("kill.wav")
snd_kill = pygame.mixer.Sound(kill_path) if os.path.exists(kill_path) else None
if snd_kill: snd_kill.set_volume(0.2)

# --- КЛАССЫ ИГРЫ ---
class Player:
    def __init__(self):
        self.pos = pygame.Vector2(WIDTH//2, HEIGHT//2)
        self.hp, self.level, self.exp = 100, 1, 0
        self.angle, self.facing_right = 0, True
        self.flash_timer = 0
        self.magnet_timer = 0
        self.invis_timer = 0
        self.zombie_timer = 0
        self.freeze_timer = 0
        self.shield_timer = 0
    def move(self, target):
        # Было +1, станет +0.5. На максе (10 ур) будет 12 — это быстро, но управляемо.
        current_speed = 7 + (player_save["upgrades"]["speed"] * 0.5)
        
        dir = target - self.pos
        if dir.length() > 5: 
            self.pos += dir.normalize() * current_speed
            return True
        return False

class Enemy:
    def __init__(self, p_pos, type="normal"):
        ang = random.uniform(0, 6.28)
        self.pos = p_pos + pygame.Vector2(math.cos(ang), math.sin(ang)) * WIDTH//1.2
        self.type = type
        self.hp = 1 if type=="normal" else (2 if type=="archer" else (5 if type=="elite" else 50))
        self.speed = random.uniform(3, 5) if type=="normal" else (4 if type=="archer" else 6)
        if type == "boss": self.speed = 2
        self.size = 60 if type=="normal" else (100 if type=="archer" else 200)
        self.shoot_timer = 0

    def move(self, p_pos):
        if player.freeze_timer > 0: return

        target = pygame.Vector2(WIDTH//2, HEIGHT//2) if player.invis_timer > 0 else p_pos
        dist = self.pos.distance_to(target)
        dir_vec = (target - self.pos)
        
        if dir_vec.length() > 0:
            dir = dir_vec.normalize()
            
            # ЛОГИКА АРБАЛЕТЧИКА: Держать дистанцию
            if self.type == "archer":
                if dist > 400: # Если далеко — подходит
                    self.pos += dir * self.speed
                elif dist < 300: # Если слишком близко — отходит
                    self.pos -= dir * self.speed
                
                # Стрельба (раз в 1.5 секунды)
                self.shoot_timer += 1
                if self.shoot_timer > 90 and player.invis_timer <= 0:
                    enemy_bullets.append(Bullet(self.pos, target, "arrow"))
                    # ЭФФЕКТ: Вспышка у арбалета
                    pygame.draw.circle(screen, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), 40, 2)
                    self.shoot_timer = 0
            else:
                # Обычное движение для остальных
                self.pos += dir * self.speed

class Bullet:
    def __init__(self, pos, target, b_type="bullet"):
        self.pos = pygame.Vector2(pos)
        self.type = b_type
        # Сюрикен летит быстрее (35), обычная пуля (25)
        speed = 30 if b_type == "shuriken" else 25
        self.vel = (target - pos).normalize() * speed
        self.angle = 0 
    def update(self):
        self.pos += self.vel
        self.angle += 10 # Скорость вращения сюрикена

class Drop:
    def __init__(self, pos, type="exp"):
        self.pos = pygame.Vector2(pos)
        self.type = type

# --- МЕНЕДЖЕР УРОВНЕЙ (30 ХАРДКОРНЫХ ЛОКАЦИЙ) ---
mission_goals = {
    # ГЛАВА 1: Начало хаоса
    1: {"kills": 30, "desc": "Разминка: 30 мышей"},
    2: {"kills": 60, "auto": "freeze", "desc": "Тир: заморозка каждые 3 килла"},
    3: {"kills": 150, "auto": "zombie", "desc": "Дробовик-шоу: мясорубка!"},
    4: {"boss": 1, "desc": "Первый Жирный: убей Босса"},
    5: {"kills": 50, "only": "archer", "desc": "Снайперская дуэль: только лучники"},
    6: {"kills": 100, "auto": "magnet", "desc": "Золотая жила: монеты рекой"},
    7: {"kills": 200, "auto": "zombie", "rate": 20, "desc": "Мясная лавка: ОЧЕНЬ много мышей"},
    8: {"kills": 30, "only": "elite", "auto": "zombie", "desc": "Элитная охота: только элита"},
    9: {"kills": 70, "only": "archer", "auto": "shield", "desc": "Прорыв: снайперы и щиты"},
    10: {"boss": 1, "auto": "zombie", "desc": "Финал главы: Босс и Дробовики"},
    
    # ГЛАВА 2: Мастера стрельбы
    11: {"boss": 2, "desc": "Два брата: битва с двумя боссами"},
    12: {"kills": 150, "only": "archer", "auto": "freeze", "desc": "Снайперский ад: они стоят"},
    13: {"kills": 60, "only": "elite", "auto": "zombie", "desc": "Элитный десант"},
    14: {"kills": 500, "auto": "shield", "rate": 15, "desc": "Стена на стену: бессмертие"},
    15: {"boss": 3, "desc": "Тройничок: три босса сразу"},
    16: {"kills": 200, "only": "archer", "rate": 10, "desc": "Град стрел: уклоняйся!"},
    17: {"kills": 800, "auto": "zombie", "rate": 10, "desc": "Ультра-хаос: телефон сгорит"},
    18: {"kills": 50, "only": "elite", "auto": "freeze", "desc": "Замороженные гиганты"},
    19: {"boss": 2, "auto": "magnet", "desc": "Боссы и куча денег"},
    20: {"boss": 1, "rate": 5, "auto": "zombie", "desc": "Крысиный король: безумие миньонов"},

    # ГЛАВА 3: Апокалипсис
    21: {"kills": 1000, "auto": "zombie", "rate": 8, "desc": "Пулеметчик: 1000 фрагов"},
    22: {"kills": 200, "only": "archer", "auto": "shield", "desc": "Батальон снайперов"},
    23: {"kills": 1500, "auto": "zombie", "rate": 5, "desc": "ПОЛНЫЙ АПОКАЛИПСИС"},
    24: {"boss": 5, "desc": "Парад Боссов: 5 по очереди"},
    25: {"kills": 100, "only": "elite", "auto": "zombie", "desc": "Штурм элиты"},
    26: {"kills": 300, "only": "archer", "auto": "zombie", "desc": "Снайперы против дробовика"},
    27: {"kills": 2000, "auto": "shield", "rate": 5, "desc": "2000 мышей: выживи любой ценой"},
    28: {"boss": 5, "auto": "zombie", "desc": "Пять всадников смерти"},
    29: {"kills": 300, "only": "elite", "rate": 10, "auto": "health", "desc": "Танковый прорыв"},
    30: {"boss": 10, "auto": "zombie", "rate": 3, "desc": "ФИНАЛ: 10 БОССОВ!"}
}

# --- ИГРОВЫЕ ПЕРЕМЕННЫЕ ---
player, enemies, bullets, drops = Player(), [], [], []
joystick_pos, shoot_timer, kills_count = None, 0, 0
elite_kills = 0
game_timer = 0

# Таймер и список фонов для смены неба
sky_timer = 0
sky_imgs = ["bg_morning.jpg", "bg.jpg", "bg_evening.jpg", "bg_night.jpg"]
current_sky_idx = 0  # ТЕПЕРЬ С 0 (УТРО)

# Сразу при запуске ставим первый фон из списка
if os.path.exists(sky_imgs[current_sky_idx]):
    img_bg = load_img(sky_imgs[current_sky_idx], 0, True)

def start_mission(m_id):
    global player, enemies, bullets, drops, kills_count, elite_kills, game_timer, game_state, current_mission, bosses_spawned
    bosses_spawned = False 
    player = Player()
    enemies, bullets, drops = [], [], []
    kills_count, elite_kills, game_timer = 0, 0, 0
    current_mission = m_id
    game_state = STATE_GAME

# --- ГЛАВНЫЙ ЦИКЛ ---
run = True
last_bg_name = "" # Обязательно для работы фонов

while run:
    screen.fill((20, 20, 40))
    m_pos = pygame.Vector2(pygame.mouse.get_pos())
    
    # --- 1. ЭКРАН ЗАГРУЗКИ (ИСПРАВЛЕНО ПОД ЭКРАН ТЕЛЕФОНА) ---
    if game_state == STATE_LOADING:
        loading_progress += 0.6  # Скорость загрузки
        
        # Выбираем имя файла
        if loading_progress < 50:
            target_bg_name = "loading1.png"
        else:
            target_bg_name = "loading2.png"
        
        # Загружаем и ПРАВИЛЬНО масштабируем через resource_path
        if target_bg_name != last_bg_name:
            path = resource_path(target_bg_name) # ПРИНУДИТЕЛЬНЫЙ ПУТЬ
            if os.path.exists(path):
                raw_img = pygame.image.load(path).convert()
                # Сжимаем картинку до 90% высоты, чтобы она была выше кнопок Android
                img_bg = pygame.transform.smoothscale(raw_img, (WIDTH, int(HEIGHT * 0.9)))
                last_bg_name = target_bg_name
        
        # Рисуем фон (черный фон сзади, чтобы не было дырок)
        screen.fill((0, 0, 0))
        if img_bg: 
            # Рисуем картинку от верхнего края
            screen.blit(img_bg, (0, 0))
        else:
            txt = font_big.render(f"ЗАГРУЗКА... {int(loading_progress)}%", True, WHITE)
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2))

        # Когда загрузка закончена
        if loading_progress >= 100:
            game_state = STATE_MENU
            last_bg_name = "" 
            
        pygame.display.flip()
        clock.tick(60)
        continue 

    # --- 2. ЛОГИКА ФОНОВ (МЕНЮ И БОЙ) ---
    if game_state == STATE_GAME or game_state == STATE_FREE_PLAY:
        target_bg = "bg.jpg"
    else:
        # В остальных случаях (Меню, Магазин, Уровни) — меняем небо по таймеру
        sky_timer += 1
        if sky_timer > 1200:
            current_sky_idx = (current_sky_idx + 1) % len(sky_imgs)
            sky_timer = 0
        target_bg = sky_imgs[current_sky_idx]

    # Подгружаем нужный фон (ТОЛЬКО если он изменился)
    if target_bg != last_bg_name:
        path = resource_path(target_bg) # Добавляем путь
        if os.path.exists(path):
            # Используем нашу функцию load_img, она уже умеет в resource_path
            img_bg = load_img(target_bg, 0, True) 
            last_bg_name = target_bg

    # Отрисовка фона (если мы не в режиме загрузки, там своя логика)
    if game_state != STATE_LOADING:
        if img_bg: 
            screen.blit(img_bg, (0, 0))

    # 1. ОБРАБОТЧИК СОБЫТИЙ (КЛИКИ)
    for e in pygame.event.get():
        if e.type == pygame.QUIT: run = False
        
        if e.type == pygame.MOUSEBUTTONDOWN:
            # --- КЛИКИ В ГЛАВНОМ МЕНЮ ---
            if game_state == STATE_MENU:
                play_w, play_h = int(WIDTH * 0.6), int(HEIGHT * 0.07)
                btn_w, btn_h = int(WIDTH * 0.4), int(HEIGHT * 0.08)
                
                # Кнопка В БОЙ (Высота 1.8)
                if pygame.Rect(WIDTH//2 - play_w//2, HEIGHT//1.5, play_w, play_h).collidepoint(e.pos):
                    game_state = STATE_LEVELS
                
                # Кнопка МАГАЗИН
                if pygame.Rect(WIDTH * 0.05, HEIGHT * 0.8, btn_w, btn_h).collidepoint(e.pos):
                    game_state = STATE_SHOP
                
                # Кнопка УСИЛЕНИЯ
                if pygame.Rect(WIDTH * 0.55, HEIGHT * 0.8, btn_w, btn_h).collidepoint(e.pos):
                    game_state = "UPGRADES"
                    
                # КЛИК ПО ЛЕВОЙ СТРЕЛКЕ (Огромная зона слева)
                left_rect = pygame.Rect(WIDTH//2 - 500, HEIGHT//2.0 - 150, 250, 300)
                if left_rect.collidepoint(e.pos):
                    if len(player_save["bought_skins"]) > 1:
                        idx = player_save["bought_skins"].index(player_save["current_skin"])
                        player_save["current_skin"] = player_save["bought_skins"][(idx - 1) % len(player_save["bought_skins"])]
                        update_hero_img()
                        save_game()

                # КЛИК ПО ПРАВОЙ СТРЕЛКЕ (Огромная зона справа)
                right_rect = pygame.Rect(WIDTH//2 + 250, HEIGHT//2.0 - 150, 250, 300)
                if right_rect.collidepoint(e.pos):
                    if len(player_save["bought_skins"]) > 1:
                        idx = player_save["bought_skins"].index(player_save["current_skin"])
                        player_save["current_skin"] = player_save["bought_skins"][(idx + 1) % len(player_save["bought_skins"])]
                        update_hero_img()
                        save_game()

            # --- КЛИКИ В МАГАЗИНЕ ---
            elif game_state == STATE_SHOP:
                # Кнопка НАЗАД
                if pygame.Rect(30, 30, 100, 60).collidepoint(e.pos):
                    game_state = STATE_MENU
                
                # Кнопки покупки (координаты под карточками)
                btn_samurai = pygame.Rect(WIDTH//4 - 120, HEIGHT//2 + 160, 240, 70)
                btn_shaman = pygame.Rect(WIDTH//4 * 3 - 120, HEIGHT//2 + 160, 240, 70)

                # Самурай
                if btn_samurai.collidepoint(e.pos):
                    if "samurai.png" in player_save["bought_skins"]:
                        player_save["current_skin"] = "samurai.png"
                    elif player_save["money"] >= 500:
                        player_save["money"] -= 500
                        player_save["bought_skins"].append("samurai.png")
                        player_save["current_skin"] = "samurai.png"
                    update_hero_img() # Мгновенно меняем картинку
                    save_game()

                # Шаман
                if btn_shaman.collidepoint(e.pos):
                    if "shaman.png" in player_save["bought_skins"]:
                        player_save["current_skin"] = "shaman.png"
                    elif player_save["money"] >= 1500:
                        player_save["money"] -= 1500
                        player_save["bought_skins"].append("shaman.png")
                        player_save["current_skin"] = "shaman.png"
                    update_hero_img() # Мгновенно меняем картинку
                    save_game()

            # --- КЛИКИ НА ЭКРАНЕ УРОВНЕЙ (ЛОГИКА СТРЕЛОК И УРОВНЕЙ) ---
            elif game_state == STATE_LEVELS:
                # 1. Кнопка НАЗАД В МЕНЮ
                if pygame.Rect(30, 30, 160, 70).collidepoint(e.pos):
                    game_state = STATE_MENU
                
                # Координаты сетки
                sx, sy = (WIDTH - (5 * 200)) // 2, (HEIGHT - (3 * 200)) // 2
                
                # 2. ЛОГИКА ПЕРЕКЛЮЧЕНИЯ СТРАНИЦ
                btn_w, btn_h = 300, 90
                btn_page_rect = pygame.Rect(WIDTH//2 - btn_w//2, sy + 620, btn_w, btn_h)
                
                # 3. Кнопка СВОБОДНАЯ ИГРА
                free_btn_w, free_btn_h = 400, 90
                free_btn_rect = pygame.Rect(WIDTH//2 - free_btn_w//2, sy + 730, free_btn_w, free_btn_h)

                if btn_page_rect.collidepoint(e.pos):
                    level_page = 1 if level_page == 0 else 0
                    pygame.time.delay(150)
                elif free_btn_rect.collidepoint(e.pos):
                    start_free_play()
                    pygame.time.delay(150)
                else:
                    # 4. Клик по карточкам уровней
                    start_lvl = 1 if level_page == 0 else 16
                    for i in range(start_lvl, start_lvl + 15):
                        idx = i - start_lvl
                        r, c = idx // 5, idx % 5
                        rect = pygame.Rect(sx + c * 200, sy + r * 200, 190, 190)
                        if rect.collidepoint(e.pos) and i <= player_save["unlocked_levels"]:
                            selected_mission_id = i
                            game_state = "BRIEFING"

            # --- КЛИКИ В ИГРЕ И СМЕРТЬ ---
            elif game_state == STATE_GAME or game_state == STATE_FREE_PLAY:
                joystick_pos = pygame.Vector2(e.pos)
            elif game_state == STATE_GAMEOVER:
                if pygame.Rect(WIDTH//2-100, HEIGHT//2, 200, 60).collidepoint(e.pos):
                    game_state = STATE_MENU

        if e.type == pygame.MOUSEBUTTONUP:
            joystick_pos = None


    # 2. ОТРИСОВКА ЭКРАНА МЕНЮ
    if game_state == STATE_MENU:
        # Красивый баланс в главном меню
        money_menu_str = get_money_text(player_save['money'])
        bal_menu_txt = font_main.render(money_menu_str, True, (255, 220, 0))
        if img_coin:
            coin_icon_menu = pygame.transform.scale(img_coin, (50, 50))
            screen.blit(coin_icon_menu, (60, 115))
            screen.blit(font_main.render(money_menu_str, True, (0, 0, 0)), (122, 122))
            screen.blit(bal_menu_txt, (120, 120))
        else:
            screen.blit(font_main.render(money_menu_str, True, (0, 0, 0)), (62, 122))
            screen.blit(bal_menu_txt, (60, 120))
        
        # БОЛЬШОЙ ФЕНЕК (теперь ЧЕТКИЙ из img_hero_big)
        if 'img_hero_big' in globals() and img_hero_big:
            h_size = int(WIDTH * 0.75) 
            h_scaled = pygame.transform.scale(img_hero_big, (h_size, h_size))
            screen.blit(h_scaled, h_scaled.get_rect(center=(WIDTH//2, HEIGHT//2.2)))
            
        # Кнопка В БОЙ (Спустили с HEIGHT//2 на HEIGHT//1.6)
        play_w, play_h = int(WIDTH * 0.6), int(HEIGHT * 0.07)
        play_rect = pygame.Rect(WIDTH//2 - play_w//2, HEIGHT//1.5, play_w, play_h)        
        # Рисуем саму кнопку
        pygame.draw.rect(screen, (0, 200, 100), play_rect, border_radius=20)
        pygame.draw.rect(screen, WHITE, play_rect, 4, border_radius=20)
        
        # Текст на кнопке
        btn_txt = font_main.render("В БОЙ", True, WHITE)
        screen.blit(btn_txt, (play_rect.centerx - btn_txt.get_width()//2, play_rect.centery - btn_txt.get_height()//2))
        
        # МАГАЗИН И АРСЕНАЛ (на 80% высоты экрана, чтобы не прилипали к низу)
        btn_w, btn_h = int(WIDTH * 0.4), int(HEIGHT * 0.08)
        # Магазин слева, Арсенал справа
        s_r = pygame.Rect(WIDTH * 0.05, HEIGHT * 0.8, btn_w, btn_h)
        a_r = pygame.Rect(WIDTH * 0.55, HEIGHT * 0.8, btn_w, btn_h)
        
        for r, img, txt, col in [(s_r, img_btn_shop, "МАГАЗИН", (255,220,0)), (a_r, img_btn_ars, "УСИЛЕНИЯ", (0,200,255))]:
            pygame.draw.rect(screen, (0,0,0,200), r, border_radius=15)
            pygame.draw.rect(screen, col, r, 3, border_radius=15)
            
            if img:
                # Масштабируем картинку прямо под размер кнопки и рисуем
                img_scaled = pygame.transform.scale(img, (r.width, r.height))
                screen.blit(img_scaled, r)
            else:

                t = font_main.render(txt, True, WHITE)
                screen.blit(t, (r.centerx-t.get_width()//2, r.centery-t.get_height()//2))
        if len(player_save["bought_skins"]) > 1:
            l_arr = font_lvl.render("<", True, WHITE)
            r_arr = font_lvl.render(">", True, WHITE)
            screen.blit(l_arr, (WIDTH//2 - 400, HEIGHT//2.0 - 5))
            screen.blit(r_arr, (WIDTH//2 + 300, HEIGHT//2.0 - 0))
            
    elif game_state == "UPGRADES":
        screen.fill((25, 25, 40)) 
        if img_shop_bg: screen.blit(img_shop_bg, (0,0))
        
        # Кнопка НАЗАД
        back_btn = pygame.Rect(30, 30, 160, 70)
        pygame.draw.rect(screen, (200, 50, 50), back_btn, border_radius=15)
        screen.blit(font_main.render("НАЗАД", True, WHITE), (50, 45))
        if pygame.mouse.get_pressed()[0] and back_btn.collidepoint(m_pos):
            game_state = STATE_MENU

        # Баланс
        bal_txt = font_main.render(get_money_text(player_save["money"]), True, (255, 215, 0))
        screen.blit(bal_txt, (WIDTH - bal_txt.get_width() - 40, 45))

        # --- ЗАГОЛОВОК 1 ---
        t_base = font_big.render("БАЗОВЫЕ УЛУЧШЕНИЯ", True, (0, 255, 255))
        screen.blit(t_base, (WIDTH//2 - t_base.get_width()//2, 120))

        # 1. БАЗОВЫЕ
        base_data = [("speed", "СКОРОСТЬ"), ("damage", "УРОН")]
        card_w, card_h = 450, 400 
        for i, (key, name) in enumerate(base_data):
            lvl = player_save["upgrades"].get(key, 0)
            x_pos = WIDTH//2 - card_w - 20 if i == 0 else WIDTH//2 + 20
            card_r = pygame.Rect(x_pos, 200, card_w, card_h)
            
            pygame.draw.rect(screen, (0,0,0,200), card_r, border_radius=30)
            pygame.draw.rect(screen, (0, 200, 255), card_r, 5, border_radius=30)
            
            n_txt = font_big.render(name, True, WHITE)
            screen.blit(n_txt, (card_r.centerx - n_txt.get_width()//2, card_r.y + 20))
            
            # --- ВСТАВКА КАРТИНКИ (ШАГ 1) ---
            b_img = img_boost_speed if key == "speed" else img_boost_power
            if b_img:
                icon_img = pygame.transform.scale(b_img, (150, 150))
                screen.blit(icon_img, icon_img.get_rect(center=(card_r.centerx, card_r.y + 165)))
            
            t_lvl = font_main.render(f"{lvl}/10 yp.", True, (0, 255, 255))
            screen.blit(t_lvl, (card_r.centerx - t_lvl.get_width()//2, card_r.bottom - 130))

            cost = 10 + (lvl * 50) if lvl < 10 else "MAX"
            btn_buy = pygame.Rect(card_r.x + 40, card_r.bottom - 80, card_w - 80, 60)
            can_buy = cost != "MAX" and player_save["money"] >= cost
            pygame.draw.rect(screen, (0, 200, 100) if can_buy else (60,60,60), btn_buy, border_radius=15)
            
            if pygame.mouse.get_pressed()[0] and btn_buy.collidepoint(m_pos) and can_buy:
                player_save["money"] -= cost
            if pygame.mouse.get_pressed()[0] and btn_buy.collidepoint(m_pos) and can_buy:
                player_save["money"] -= cost
                if key not in player_save["upgrades"]:
                    player_save["upgrades"][key] = 0
                player_save["upgrades"][key] += 1
                save_game()
                pygame.time.delay(180)
                save_game(); pygame.time.delay(180)
            
            c_txt = font_main.render(str(cost) if cost=="MAX" else f"${cost}", True, WHITE)
            screen.blit(c_txt, (btn_buy.centerx - c_txt.get_width()//2, btn_buy.centery - 20))

        # --- ЗАГОЛОВОК 2 ---
        t_bonus = font_big.render("ДОПОЛНИТЕЛЬНЫЕ БОНУСЫ", True, (200, 100, 255))
        screen.blit(t_bonus, (WIDTH//2 - t_bonus.get_width()//2, 620))

        # 2. БОНУСЫ (СЕТКА 3 РЯДА С КАРТИНКАМИ)
        bonus_data = [
            ("invis", "НЕВИДИМОСТЬ"), ("magnet", "МАГНИТ"),
            ("zombie", "ДРОБОВИК"), ("freeze", "ЗАМОРОЗКА"),
            ("health", "АПТЕЧКА"), ("shield", "ЩИТ")
        ]
        # Словарь, чтобы код понимал, какую картинку рисовать
        bonus_imgs = {
            "invis": img_boost_invis, "magnet": img_boost_magnet,
            "zombie": img_boost_zombie, "freeze": img_boost_freeze,
            "health": img_boost_health, "shield": img_boost_shield
        }

        for i, (key, name) in enumerate(bonus_data):
            row, col = i // 2, i % 2
            lvl = player_save["upgrades"].get(key, 0)
            x_pos = WIDTH//2 - card_w - 20 if col == 0 else WIDTH//2 + 20
            y_pos = 700 + row * 430
            card_r = pygame.Rect(x_pos, y_pos, card_w, card_h)
            
            pygame.draw.rect(screen, (0,0,0,200), card_r, border_radius=30)
            pygame.draw.rect(screen, (200, 100, 255), card_r, 5, border_radius=30)

            n_txt = font_big.render(name, True, WHITE)
            screen.blit(n_txt, (card_r.centerx - n_txt.get_width()//2, card_r.y + 20))

            # --- ВСТАВКА КАРТИНКИ БОНУСА ---
            b_img = bonus_imgs.get(key)
            if b_img:
                icon_img = pygame.transform.scale(b_img, (140, 140))
                screen.blit(icon_img, icon_img.get_rect(center=(card_r.centerx, card_r.y + 165)))

            t_lvl = font_main.render(f"{lvl}/10 yp.", True, (200, 100, 255))
            screen.blit(t_lvl, (card_r.centerx - t_lvl.get_width()//2, card_r.bottom - 130))

            cost = 10 + (lvl * 50) if lvl < 10 else "MAX"
            btn_buy = pygame.Rect(card_r.x + 40, card_r.bottom - 80, card_w - 80, 60)
            can_buy = cost != "MAX" and player_save["money"] >= cost
            pygame.draw.rect(screen, (0, 200, 100) if can_buy else (60,60,60), btn_buy, border_radius=15)
            
            if pygame.mouse.get_pressed()[0] and btn_buy.collidepoint(m_pos) and can_buy:
                player_save["money"] -= cost
            if pygame.mouse.get_pressed()[0] and btn_buy.collidepoint(m_pos) and can_buy:
                player_save["money"] -= cost
                # Проверяем, есть ли ключ, если нет — создаем его
                if key not in player_save["upgrades"]:
                    player_save["upgrades"][key] = 0
                player_save["upgrades"][key] += 1
                save_game()
                pygame.time.delay(180)
                save_game(); pygame.time.delay(180)
            
            c_txt = font_main.render(str(cost) if cost=="MAX" else f"${cost}", True, WHITE)
            screen.blit(c_txt, (btn_buy.centerx - c_txt.get_width()//2, btn_buy.centery - 20))

    # --- ЛОГИКА ВЫБОРА УРОВНЕЙ (ОТРИСОВКА) ---
    elif game_state == STATE_LEVELS:
        # Кнопка МЕНЮ
        back_rect = pygame.Rect(30, 30, 160, 70)
        pygame.draw.rect(screen, (150, 0, 0), back_rect, border_radius=15)
        screen.blit(font_main.render("МЕНЮ", True, WHITE), (55, 45))
        
        # Сетка уровней
        sx, sy = (WIDTH - (5 * 200)) // 2, (HEIGHT - (3 * 200)) // 2 
        start_lvl = 1 if level_page == 0 else 16
        
        for i in range(start_lvl, start_lvl + 15):
            idx = i - start_lvl
            row, col = idx // 5, idx % 5
            rect = pygame.Rect(sx + col * 200, sy + row * 200, 190, 190)
            
            if i <= player_save["unlocked_levels"]:
                if img_lvl_btn:
                    screen.blit(pygame.transform.scale(img_lvl_btn, (190, 190)), rect)
                else:
                    pygame.draw.rect(screen, (0, 200, 100), rect, border_radius=15)
                txt = font_lvl.render(str(i), True, WHITE)
                screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))
            else:
                pygame.draw.rect(screen, (60, 60, 60), rect, border_radius=15)
                pygame.draw.circle(screen, (30, 30, 30), rect.center, 15)

        # КНОПКА ПЕРЕКЛЮЧЕНИЯ (РИСОВАНИЕ)
        btn_w, btn_h = 300, 90
        btn_page_rect = pygame.Rect(WIDTH//2 - btn_w//2, sy + 620, btn_w, btn_h)
        pygame.draw.rect(screen, (50, 50, 70), btn_page_rect, border_radius=20)
        pygame.draw.rect(screen, (0, 200, 255), btn_page_rect, 3, border_radius=20)
        
        btn_text = "ДАЛЕЕ >" if level_page == 0 else "< НАЗАД"
        t_render = font_main.render(btn_text, True, WHITE)
        screen.blit(t_render, (btn_page_rect.centerx - t_render.get_width()//2, btn_page_rect.centery - t_render.get_height()//2))
        
    # --- КНОПКА "СВОБОДНАЯ ИГРА" ---
        free_btn_w, free_btn_h = 400, 90
        free_btn_rect = pygame.Rect(WIDTH//2 - free_btn_w//2, sy + 730, free_btn_w, free_btn_h)
        pygame.draw.rect(screen, (100, 50, 200), free_btn_rect, border_radius=25)
        pygame.draw.rect(screen, (255, 215, 0), free_btn_rect, 5, border_radius=25)
        free_txt = font_main.render("СВОБОДНАЯ ИГРА", True, (255, 255, 255))
        screen.blit(free_txt, (free_btn_rect.centerx - free_txt.get_width()//2, free_btn_rect.centery - free_txt.get_height()//2))
                
    # --- ЭКРАН МАГАЗИНА ---
    elif game_state == STATE_SHOP:
        # 1. РИСУЕМ ФОН МАГАЗИНА
        if 'img_shop_bg' in globals() and img_shop_bg:
            screen.blit(img_shop_bg, (0, 0))
        else:
            screen.fill((15, 15, 25)) 
        
        # 2. Кнопка НАЗАД (Стрелочка)
        back_btn = pygame.Rect(30, 30, 100, 60)
        pygame.draw.rect(screen, (50, 50, 60), back_btn, border_radius=15)
        screen.blit(font_main.render("<", True, WHITE), (70, 40))

        # 3. БАЛАНС (Сверху справа с правильным склонением)
        money_str = get_money_text(player_save['money'])
        bal_txt = font_main.render(money_str, True, (255, 220, 0))
        bg_rect = pygame.Rect(WIDTH - bal_txt.get_width() - 80, 35, bal_txt.get_width() + 40, 60)
        pygame.draw.rect(screen, (0, 0, 0, 150), bg_rect, border_radius=10)
        screen.blit(bal_txt, (WIDTH - bal_txt.get_width() - 60, 40))

        # 4. КАРТОЧКА САМУРАЯ (ЭПИК)
        s_rect = pygame.Rect(WIDTH//4 - 150, HEIGHT//2 - 250, 300, 500)
        pygame.draw.rect(screen, (30, 30, 45, 200), s_rect, border_radius=25)
        pygame.draw.rect(screen, (180, 50, 255), s_rect, 6, border_radius=25)
        
        # Надпись редкости (с тенью)
        txt_rare_s = font_main.render("ЭПИК", True, (180, 50, 255))
        screen.blit(font_main.render("ЭПИК", True, (0, 0, 0)), (s_rect.centerx - txt_rare_s.get_width()//2 + 2, s_rect.y + 22))
        screen.blit(txt_rare_s, (s_rect.centerx - txt_rare_s.get_width()//2, s_rect.y + 20))
        
        if img_samurai: 
            # Сдвиг -175 (половина от 350), чтобы был ровно по центру
            screen.blit(img_samurai, (s_rect.centerx - 175, s_rect.y + 60))
        
        # Кнопка КУПИТЬ/ВЫБРАТЬ Самурай
        btn_s = pygame.Rect(s_rect.x + 30, s_rect.bottom - 90, 240, 70)
        pygame.draw.rect(screen, (180, 50, 255), btn_s, border_radius=15)
        
        if "samurai.png" in player_save["bought_skins"]:
            txt_s = font_main.render("ВЫБРАТЬ", True, WHITE)
            screen.blit(txt_s, (btn_s.centerx - txt_s.get_width()//2, btn_s.centery - 20))
        else:
            # ЦЕНА + МОНЕТКА
            p_txt = font_main.render("500", True, (0, 0, 0))
            total_w = p_txt.get_width() + 45
            screen.blit(p_txt, (btn_s.centerx - total_w//2, btn_s.centery - 20))
            if img_coin:
                coin_s = pygame.transform.scale(img_coin, (40, 40))
                screen.blit(coin_s, (btn_s.centerx + total_w//2 - 40, btn_s.centery - 15))

        # 5. КАРТОЧКА ШАМАНА (ЛЕГЕНДА)
        sh_rect = pygame.Rect(WIDTH//4 * 3 - 150, HEIGHT//2 - 250, 300, 500)
        pygame.draw.rect(screen, (30, 30, 45, 200), sh_rect, border_radius=25)
        pygame.draw.rect(screen, (255, 215, 0), sh_rect, 6, border_radius=25)
        
        # Надпись редкости (с тенью)
        txt_rare_sh = font_main.render("ЛЕГЕНДА", True, (255, 215, 0))
        screen.blit(font_main.render("ЛЕГЕНДА", True, (0, 0, 0)), (sh_rect.centerx - txt_rare_sh.get_width()//2 + 2, sh_rect.y + 22))
        screen.blit(txt_rare_sh, (sh_rect.centerx - txt_rare_sh.get_width()//2, sh_rect.y + 20))
        
        if img_shaman: 
            screen.blit(img_shaman, (sh_rect.centerx - 175, sh_rect.y + 60))

        # Кнопка КУПИТЬ/ВЫБРАТЬ Шаман
        btn_sh = pygame.Rect(sh_rect.x + 30, sh_rect.bottom - 90, 240, 70)
        pygame.draw.rect(screen, (255, 215, 0), btn_sh, border_radius=15)
        
        if "shaman.png" in player_save["bought_skins"]:
            txt_sh = font_main.render("ВЫБРАТЬ", True, (0, 0, 0))
            screen.blit(txt_sh, (btn_sh.centerx - txt_sh.get_width()//2, btn_sh.centery - 20))
        else:
            # ЦЕНА + МОНЕТКА
            p_txt = font_main.render("1500", True, (0, 0, 0))
            total_w = p_txt.get_width() + 45
            screen.blit(p_txt, (btn_sh.centerx - total_w//2, btn_sh.centery - 20))
            if img_coin:
                coin_s = pygame.transform.scale(img_coin, (40, 40))
                screen.blit(coin_s, (btn_sh.centerx + total_w//2 - 40, btn_sh.centery - 15))

    # --- ЛОГИКА ИГРЫ ---
    elif game_state == STATE_GAME:
        game_timer += 1/60
        if joystick_pos:
            player.move(player.pos + (m_pos - joystick_pos))
        
        # 1. УМНЫЙ СПАВН (Исправленный: Боссы поштучно + Только нужные типы)
        goal = mission_goals.get(current_mission, {})
        s_rate = goal.get("rate", 40 if current_mission < 5 else 25)
        
        # Лимит врагов (на мясных уровнях до 60, на обычных 30)
        max_en = 60 if s_rate < 15 else 30

        # А) СПАВН ОБЫЧНЫХ ВРАГОВ (с учетом настройки "only")
        if len(enemies) < max_en and random.randint(0, s_rate) == 0:
            if "only" in goal:
                # Если в миссии только снайперы или элита - спавним их
                etype = goal["only"]
                enemies.append(Enemy(player.pos, etype))
            elif "kills" in goal or "time" in goal:
                # Если обычная миссия - стандартный рандом (без лишних боссов)
                rand = random.random()
                if rand < 0.15: etype = "elite"
                elif rand < 0.35: etype = "archer" 
                else: etype = "normal"
                enemies.append(Enemy(player.pos, etype))

        # Б) СПАВН БОССОВ (Строго по количеству из mission_goals)
        if "boss" in goal and not bosses_spawned and game_timer > 3:
            # Считаем, сколько боссов уже на экране
            current_bosses = sum(1 for en in enemies if en.type == "boss")
            if current_bosses < goal["boss"]:
                # Доспавниваем ровно столько, сколько не хватает
                for _ in range(goal["boss"] - current_bosses):
                    enemies.append(Enemy(player.pos, "boss"))
            bosses_spawned = True # Закрываем спавн боссов для этой миссии

        # 2. АВТО-СТРЕЛЬБА
        shoot_timer += 1
        if enemies and shoot_timer > 15:
            target = min(enemies, key=lambda e: e.pos.distance_to(player.pos))
            player.angle = math.degrees(math.atan2(target.pos.y-player.pos.y, target.pos.x-player.pos.x))
            player.facing_right = target.pos.x > player.pos.x
            b_type = "shuriken" if player_save["current_skin"] == "samurai.png" else ("magic" if player_save["current_skin"] == "shaman.png" else "bullet")
            bullets.append(Bullet(player.pos, target.pos, b_type))
            player.flash_timer = 5
            if snd_shot: snd_shot.play()
            shoot_timer = 0

        # 3. ТВОИ ПУЛИ
        for b in bullets[:]:
            b.update()
            if b.pos.x < -100 or b.pos.x > WIDTH+100 or b.pos.y < -100 or b.pos.y > HEIGHT+100:
                bullets.remove(b)
                continue

            if b.type == "shuriken" and img_shuriken:
                s_scaled = pygame.transform.smoothscale(img_shuriken, (30, 30))
                rot_s = pygame.transform.rotate(s_scaled, b.angle)
                screen.blit(rot_s, rot_s.get_rect(center=b.pos))
            elif b.type == "magic" and img_magic:
                m_scaled = pygame.transform.smoothscale(img_magic, (45, 45))
                screen.blit(m_scaled, m_scaled.get_rect(center=b.pos))
            else:
                pygame.draw.circle(screen, WHITE, (int(b.pos.x), int(b.pos.y)), 8)

            for e in enemies[:]:
                if e.pos.distance_to(b.pos) < e.size//2:
                    total_dmg = (2 if b.type == "magic" else 1) + (player_save["upgrades"]["damage"] * 0.3)
                    e.hp -= total_dmg
                    if b in bullets: bullets.remove(b)
                    if e.hp <= 0:
                        if snd_kill: snd_kill.play()
                        if e.type == "elite": elite_kills += 1
                        enemies.remove(e)
                        kills_count += 1
                        
                        # --- НОВАЯ ЛОГИКА АВТО-ДРОПА ---
                        goal = mission_goals.get(current_mission, {})
                        # Проверяем, есть ли в уровне настройка "auto" (каждый 3-й килл)
                        if "auto" in goal and kills_count % 3 == 0:
                            drops.append(Drop(e.pos, goal["auto"]))
                        else:
                            # Стандартный случайный дроп (10% шанс)
                            if random.random() < 0.1:
                                drops.append(Drop(e.pos, random.choice(["magnet", "invis", "zombie", "freeze", "health", "shield"])))
                            else:
                                # Обычные монетки или опыт
                                drops.append(Drop(e.pos, "coin" if random.randint(0,5)>3 else "exp"))
                        
                        if len(drops) > 60: drops.pop(0)
                        break
                    
        # 4. ВРАЖЕСКИЕ ЯДРА (АРБАЛЕТЧИКИ)
        for eb in enemy_bullets[:]:
            eb.update()
            pygame.draw.circle(screen, (255, 50, 50), (int(eb.pos.x), int(eb.pos.y)), 15)
            pygame.draw.circle(screen, (0, 0, 0), (int(eb.pos.x), int(eb.pos.y)), 10)
            pygame.draw.circle(screen, (255, 255, 255), (int(eb.pos.x - 3), int(eb.pos.y - 3)), 3)
            
            if eb.pos.distance_to(player.pos) < 55:
                # ПРОВЕРКА ЩИТА: урон только если щит не активен
                if player.shield_timer <= 0:
                    player.hp -= 10 
                    vibrate(100) 
                    player.pos += eb.vel.normalize() * 20 
                
                # Ядро исчезает при любом столкновении с игроком
                if eb in enemy_bullets: enemy_bullets.remove(eb)
            elif eb.pos.x < -100 or eb.pos.x > WIDTH+100 or eb.pos.y < -100 or eb.pos.y > HEIGHT+100:
                if eb in enemy_bullets: enemy_bullets.remove(eb)

        # 5. ВРАГИ (Движение и Отрисовка)
        for e in enemies[:]:
            e.move(player.pos)
            img = img_boss if e.type=="boss" else (img_archer if e.type=="archer" else (img_elite if e.type=="elite" else img_enemy))
            if img: 
                face_right = e.pos.x < player.pos.x
                e_img = pygame.transform.flip(img, not face_right, False)
                screen.blit(e_img, e_img.get_rect(center=e.pos))
            
            if e.pos.distance_to(player.pos) < e.size//2: 
                # Урон наносится только если ЩИТ НЕ АКТИВЕН
                if player.shield_timer <= 0:
                    player.hp -= 0.5
                    if random.randint(0, 10) == 0: vibrate(30) 
                # Если щит активен, мышь просто "толкается", но HP не тратится

        # 6. СБОР ДРОПА
        for d in drops[:]:
            # Выбор спрайта
            d_img = None
            if d.type == "coin": d_img = img_coin
            elif d.type == "exp": d_img = img_exp
            elif d.type == "magnet": d_img = img_boost_magnet
            elif d.type == "invis": d_img = img_boost_invis
            elif d.type == "zombie": d_img = img_boost_zombie
            elif d.type == "freeze": d_img = img_boost_freeze
            elif d.type == "speed": d_img = img_boost_speed
            elif d.type == "power": d_img = img_boost_power
            elif d.type == "health": d_img = img_boost_health
            elif d.type == "shield": d_img = img_boost_shield

            if d_img:
                screen.blit(d_img, d_img.get_rect(center=d.pos))
            else:
                pygame.draw.circle(screen, (255,255,255), (int(d.pos.x), int(d.pos.y)), 25)

            # Магнит монеток
            if player.magnet_timer > 0 and d.type == "coin":
                d.pos += (player.pos - d.pos).normalize() * 15

            # Подбор
            if d.pos.distance_to(player.pos) < 65:
                if d.type == "coin": 
                    player_save["money"] += 1
                elif d.type == "exp": 
                    player.exp += 1
                elif d.type == "health":
                    # Хилит от 5 до 50 HP (зависит от уровня прокачки Аптечки)
                    heal = 5 + (player_save["upgrades"].get("health", 0) * 4.5)
                    player.hp = min(100, player.hp + heal)
                elif d.type == "shield":
                    # Щит: 2 сек на 1 ур. + 0.5 сек за каждый уровень
                    player.shield_timer = (2 + player_save["upgrades"].get("shield", 0) * 0.5) * 60
                elif d.type == "zombie":
                    # Ульта дробовика
                    lvl = player_save["upgrades"].get("zombie", 0)
                    n_p = 6 + (lvl * 2)
                    b_t = "shuriken" if player_save["current_skin"] == "samurai.png" else ("magic" if player_save["current_skin"] == "shaman.png" else "bullet")
                    for i in range(n_p):
                        rad = math.radians((360 / n_p) * i)
                        target = player.pos + pygame.Vector2(math.cos(rad), math.sin(rad)) * 100
                        bullets.append(Bullet(player.pos, target, b_t))
                    if snd_shot: snd_shot.play()
                else:
                    # Обычные таймеры (Магнит, Инвиз, Заморозка)
                    dur = (4 + player_save["upgrades"].get(d.type, 0) * 0.4) * 60
                    if d.type == "magnet": player.magnet_timer = dur
                    if d.type == "invis": player.invis_timer = dur
                    if d.type == "freeze": player.freeze_timer = dur
                
                if d in drops: drops.remove(d)

        # 7. ГЕРОЙ И ЭФФЕКТЫ
        if img_hero:
            h_anim = pygame.transform.flip(img_hero, not player.facing_right, False)
            if player.invis_timer > 0: h_anim.set_alpha(150)
            else: h_anim.set_alpha(255)
            
            # Рисуем щит ВОКРУГ героя (под ним, чтобы не закрывал лицо)
            if player.shield_timer > 0:
                # Сияющий синий круг с эффектом пульсации
                s_size = 180 + random.randint(0, 10)
                shield_surf = pygame.Surface((s_size, s_size), pygame.SRCALPHA)
                # Рисуем несколько кругов для эффекта свечения
                pygame.draw.circle(shield_surf, (0, 150, 255, 100), (s_size//2, s_size//2), s_size//2)
                pygame.draw.circle(shield_surf, (200, 255, 255, 180), (s_size//2, s_size//2), s_size//2, 5)
                screen.blit(shield_surf, shield_surf.get_rect(center=player.pos))
                player.shield_timer -= 1 # Уменьшаем время действия каждый кадр

            screen.blit(h_anim, h_anim.get_rect(center=player.pos))
            
            if player.flash_timer > 0:
                f_rot = pygame.transform.rotate(img_flash, -player.angle)
                screen.blit(f_rot, f_rot.get_rect(center=player.pos + pygame.Vector2(math.cos(math.radians(player.angle)), math.sin(math.radians(player.angle)))*60))
                player.flash_timer -= 1

        # 8. ЕДИНЫЙ HUD И ТАЙМЕРЫ
        # Полоска здоровья
        pygame.draw.rect(screen, (200, 0, 0), (20, 20, 200, 20))
        pygame.draw.rect(screen, (0, 200, 0), (20, 20, int(200*(max(0, player.hp)/100)), 20))
        
        # Кнопка ПАУЗА (Справа сверху)
        pause_btn_rect = pygame.Rect(WIDTH - 120, 20, 100, 100)
        pygame.draw.rect(screen, (40, 40, 60, 200), pause_btn_rect, border_radius=20)
        pygame.draw.rect(screen, WHITE, pause_btn_rect, 4, border_radius=20)
        pygame.draw.rect(screen, WHITE, (WIDTH - 95, 40, 15, 60)) # Полоска 1
        pygame.draw.rect(screen, WHITE, (WIDTH - 65, 40, 15, 60)) # Полоска 2
        
        if pygame.mouse.get_pressed()[0] and pause_btn_rect.collidepoint(m_pos):
            game_state = "PAUSE"
            pygame.time.delay(200)

        screen.blit(font_main.render(f"Монеты: {player_save['money']}", True, (255,255,0)), (20, 50))
        
        goal = mission_goals.get(current_mission, {"kills": 999})
        if "kills" in goal: g_txt = f"Цель: {kills_count}/{goal['kills']} мышей"
        elif "time" in goal: g_txt = f"Выжить: {max(0, int(goal['time'] - game_timer))} сек."
        elif "boss" in goal: g_txt = "Убей босса!"
        else: g_txt = "Выживай!"
        screen.blit(font_main.render(g_txt, True, WHITE), (20, 90))

        # Тиканье и эффекты бонусов
        if player.magnet_timer > 0: player.magnet_timer -= 1
        if player.freeze_timer > 0: player.freeze_timer -= 1
        if player.shield_timer > 0: player.shield_timer -= 1 # Не забудь и про щит!
        if player.invis_timer > 0:
            player.invis_timer -= 1
            img_hero.set_alpha(150)
        else:
            img_hero.set_alpha(255)

        # 9. УСЛОВИЯ ПОБЕДЫ И ПОРАЖЕНИЯ (ИСПРАВЛЕНО)
        win = False
        goal = mission_goals.get(current_mission, {})
        
        if "kills" in goal and kills_count >= goal["kills"]: 
            win = True
        elif "time" in goal and game_timer >= goal["time"]: 
            win = True
        # Победа по боссам: если они заспавнились и их больше нет в списке enemies
        elif "boss" in goal and bosses_spawned:
            if not any(en.type == "boss" for en in enemies): 
                win = True
        
        if win:
            if current_mission == player_save["unlocked_levels"]: 
                player_save["unlocked_levels"] += 1
            save_game()
            enemy_bullets.clear()
            game_state = STATE_LEVELS
            pygame.time.delay(200) # Защита от лишних кликов
        elif player.hp <= 0:
            save_game()
            game_state = STATE_GAMEOVER

    #СВОБОДНАЯ ИГРА
    elif game_state == STATE_FREE_PLAY:
        MAX_TIME = 1732  # 28:52 в секундах
        free_play_timer += 1/60
        
        if free_play_timer >= MAX_TIME or player.hp <= 0:
            previous_state = STATE_FREE_PLAY
            if free_play_timer > player_save.get("free_record_time", 0):
                player_save["free_record_time"] = int(free_play_timer)
            if free_play_kills > player_save.get("free_record_kills", 0):
                player_save["free_record_kills"] = free_play_kills
            save_game()
            game_state = STATE_GAMEOVER
        
        if joystick_pos:
            player.move(player.pos + (m_pos - joystick_pos))
            
        # Дальше идет остальная логика свободной игры (спавн, бонусы и т.д.)
        
        # --- ДИНАМИЧЕСКАЯ СЛОЖНОСТЬ ---
        base_rate = max(8, 40 - int(free_play_timer // 30))
        max_enemies = 30 + int(free_play_timer // 15)
        boss_chance = 0.005 * (free_play_timer // 30)
        
        # Спавн врагов
        if len(enemies) < max_enemies and random.randint(0, int(base_rate)) == 0:
            r = random.random()
            if r < boss_chance:
                etype = "boss"
            elif r < 0.2:
                etype = "elite"
            elif r < 0.4:
                etype = "archer"
            else:
                etype = "normal"
            enemies.append(Enemy(player.pos, etype))
        
        # --- ЦИКЛИЧЕСКИЕ БОНУСЫ КАЖДЫЕ 20 СЕКУНД ---
        current_phase = (int(free_play_timer) // 20) % len(bonus_list)
        
        # Применяем бонус
        if bonus_list[current_phase] == "zombie":
            player.zombie_timer = 10
        elif bonus_list[current_phase] == "magnet":
            player.magnet_timer = 10
        elif bonus_list[current_phase] == "freeze":
            player.freeze_timer = 10
        elif bonus_list[current_phase] == "invis":
            player.invis_timer = 10
        
        # --- АВТО-СТРЕЛЬБА ---
        shoot_timer += 1
        if enemies and shoot_timer > 12:
            target = min(enemies, key=lambda e: e.pos.distance_to(player.pos))
            player.angle = math.degrees(math.atan2(target.pos.y-player.pos.y, target.pos.x-player.pos.x))
            player.facing_right = target.pos.x > player.pos.x
            b_type = "shuriken" if player_save["current_skin"] == "samurai.png" else ("magic" if player_save["current_skin"] == "shaman.png" else "bullet")
            bullets.append(Bullet(player.pos, target.pos, b_type))
            player.flash_timer = 5
            if snd_shot: snd_shot.play()
            shoot_timer = 0
        
        # --- ОБРАБОТКА ПУЛЬ ---
        for b in bullets[:]:
            b.update()
            if b.pos.x < -100 or b.pos.x > WIDTH+100 or b.pos.y < -100 or b.pos.y > HEIGHT+100:
                if b in bullets: bullets.remove(b)
                continue

            if b.type == "shuriken" and img_shuriken:
                s_scaled = pygame.transform.smoothscale(img_shuriken, (30, 30))
                rot_s = pygame.transform.rotate(s_scaled, b.angle)
                screen.blit(rot_s, rot_s.get_rect(center=b.pos))
            elif b.type == "magic" and img_magic:
                m_scaled = pygame.transform.smoothscale(img_magic, (45, 45))
                screen.blit(m_scaled, m_scaled.get_rect(center=b.pos))
            else:
                pygame.draw.circle(screen, WHITE, (int(b.pos.x), int(b.pos.y)), 8)

            for e in enemies[:]:
                if e.pos.distance_to(b.pos) < e.size//2:
                    total_dmg = (2 if b.type == "magic" else 1) + (player_save["upgrades"]["damage"] * 0.3)
                    e.hp -= total_dmg
                    if b in bullets: bullets.remove(b)
                    if e.hp <= 0:
                        if snd_kill: snd_kill.play()
                        enemies.remove(e)
                        free_play_kills += 1
                        
                        # Дропы
                        if random.random() < 0.15:
                            drops.append(Drop(e.pos, random.choice(["magnet", "invis", "zombie", "freeze", "health", "shield"])))
                        else:
                            drops.append(Drop(e.pos, "coin" if random.randint(0,5)>2 else "exp"))
                        
                        if len(drops) > 80: drops.pop(0)
                        break
        
        # --- ВРАЖЕСКИЕ ПУЛИ (ЛУЧНИКИ) ---
        for eb in enemy_bullets[:]:
            eb.update()
            pygame.draw.circle(screen, (255, 50, 50), (int(eb.pos.x), int(eb.pos.y)), 15)
            pygame.draw.circle(screen, (0, 0, 0), (int(eb.pos.x), int(eb.pos.y)), 10)
            pygame.draw.circle(screen, (255, 255, 255), (int(eb.pos.x - 3), int(eb.pos.y - 3)), 3)
            
            if eb.pos.distance_to(player.pos) < 55:
                if player.shield_timer <= 0:
                    player.hp -= 10
                    vibrate(100)
                    player.pos += eb.vel.normalize() * 20
                if eb in enemy_bullets: enemy_bullets.remove(eb)
            elif eb.pos.x < -100 or eb.pos.x > WIDTH+100 or eb.pos.y < -100 or eb.pos.y > HEIGHT+100:
                if eb in enemy_bullets: enemy_bullets.remove(eb)
        
        # --- ДВИЖЕНИЕ И ОТРИСОВКА ВРАГОВ ---
        for e in enemies[:]:
            e.move(player.pos)
            img = img_boss if e.type=="boss" else (img_archer if e.type=="archer" else (img_elite if e.type=="elite" else img_enemy))
            if img:
                face_right = e.pos.x < player.pos.x
                e_img = pygame.transform.flip(img, not face_right, False)
                screen.blit(e_img, e_img.get_rect(center=e.pos))
            
            if e.pos.distance_to(player.pos) < e.size//2:
                if player.shield_timer <= 0:
                    player.hp -= 0.5
                    if random.randint(0, 10) == 0: vibrate(30)
        
        # --- СБОР ДРОПОВ ---
        for d in drops[:]:
            d_img = None
            if d.type == "coin": d_img = img_coin
            elif d.type == "exp": d_img = img_exp
            elif d.type == "magnet": d_img = img_boost_magnet
            elif d.type == "invis": d_img = img_boost_invis
            elif d.type == "zombie": d_img = img_boost_zombie
            elif d.type == "freeze": d_img = img_boost_freeze
            elif d.type == "health": d_img = img_boost_health
            elif d.type == "shield": d_img = img_boost_shield

            if d_img:
                screen.blit(d_img, d_img.get_rect(center=d.pos))
            else:
                pygame.draw.circle(screen, (255,255,255), (int(d.pos.x), int(d.pos.y)), 25)

            if player.magnet_timer > 0 and d.type == "coin":
                d.pos += (player.pos - d.pos).normalize() * 15

            if d.pos.distance_to(player.pos) < 65:
                if d.type == "coin":
                    player_save["money"] += 1
                elif d.type == "exp":
                    player.exp += 1
                elif d.type == "health":
                    heal = 5 + (player_save["upgrades"].get("health", 0) * 4.5)
                    player.hp = min(100, player.hp + heal)
                elif d.type == "shield":
                    player.shield_timer = (2 + player_save["upgrades"].get("shield", 0) * 0.5) * 60
                elif d.type == "zombie":
                    lvl = player_save["upgrades"].get("zombie", 0)
                    n_p = 6 + (lvl * 2)
                    b_t = "shuriken" if player_save["current_skin"] == "samurai.png" else ("magic" if player_save["current_skin"] == "shaman.png" else "bullet")
                    for i in range(n_p):
                        rad = math.radians((360 / n_p) * i)
                        target = player.pos + pygame.Vector2(math.cos(rad), math.sin(rad)) * 100
                        bullets.append(Bullet(player.pos, target, b_t))
                    if snd_shot: snd_shot.play()
                else:
                    dur = (4 + player_save["upgrades"].get(d.type, 0) * 0.4) * 60
                    if d.type == "magnet": player.magnet_timer = dur
                    if d.type == "invis": player.invis_timer = dur
                    if d.type == "freeze": player.freeze_timer = dur
                
                if d in drops: drops.remove(d)
        
        # --- ОТРИСОВКА ГЕРОЯ ---
        if img_hero:
            h_anim = pygame.transform.flip(img_hero, not player.facing_right, False)
            if player.invis_timer > 0: h_anim.set_alpha(150)
            else: h_anim.set_alpha(255)
            
            if player.shield_timer > 0:
                s_size = 180 + random.randint(0, 10)
                shield_surf = pygame.Surface((s_size, s_size), pygame.SRCALPHA)
                pygame.draw.circle(shield_surf, (0, 150, 255, 100), (s_size//2, s_size//2), s_size//2)
                pygame.draw.circle(shield_surf, (200, 255, 255, 180), (s_size//2, s_size//2), s_size//2, 5)
                screen.blit(shield_surf, shield_surf.get_rect(center=player.pos))
                player.shield_timer -= 1

            screen.blit(h_anim, h_anim.get_rect(center=player.pos))
            
            if player.flash_timer > 0:
                f_rot = pygame.transform.rotate(img_flash, -player.angle)
                screen.blit(f_rot, f_rot.get_rect(center=player.pos + pygame.Vector2(math.cos(math.radians(player.angle)), math.sin(math.radians(player.angle)))*60))
                player.flash_timer -= 1
        
        # --- ТАЙМЕРЫ ЭФФЕКТОВ ---
        if player.magnet_timer > 0: player.magnet_timer -= 1
        if player.freeze_timer > 0: player.freeze_timer -= 1
        if player.shield_timer > 0: player.shield_timer -= 1
        if player.invis_timer > 0: player.invis_timer -= 1
        
        # --- HUD СВОБОДНОЙ ИГРЫ (УЛУЧШЕННАЯ ПАНЕЛЬ) ---
        # 1. Расчеты времени
        mins = int(free_play_timer) // 60
        secs = int(free_play_timer) % 60
        time_str = f"{mins:02d}:{secs:02d}"
        
        # 2. Отрисовка подложки (мини-табличка)
        panel_rect = pygame.Rect(10, 10, 320, 240)
        panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (0, 0, 0, 150), (0, 0, panel_rect.width, panel_rect.height), border_radius=15)
        pygame.draw.rect(panel_surf, (0, 200, 255, 200), (0, 0, panel_rect.width, panel_rect.height), 3, border_radius=15)
        screen.blit(panel_surf, (panel_rect.x, panel_rect.y))

        # 3. Полоска здоровья (внутри панели)
        pygame.draw.rect(screen, (100, 0, 0), (25, 25, 280, 25), border_radius=5) # Фон полоски
        pygame.draw.rect(screen, (0, 255, 100), (25, 25, int(280*(max(0, player.hp)/100)), 25), border_radius=5) # ХП


        # 4. Данные (Время, Киллы, Рекорды)
        screen.blit(font_main.render(f"ВРЕМЯ: {time_str}", True, (255, 255, 0)), (25, 60))
        screen.blit(font_main.render(f"УБИТО: {free_play_kills}", True, (255, 255, 0)), (25, 100))
        
        # Рекорды чуть помельче или другим цветом
        rec_mins = free_play_record_time // 60
        rec_secs = free_play_record_time % 60
        record_time_str = f"{rec_mins:02d}:{rec_secs:02d}"
        screen.blit(font_main.render(f"РЕКОРД: {record_time_str}", True, (200, 200, 200)), (25, 150))
        screen.blit(font_main.render(f"МАКС. УБ: {free_play_record_kills}", True, (200, 200, 200)), (25, 190))

        # 5. Бонус (вынесен отдельно внизу панели для красоты)
        bonus_names = ["ДРОБОВИК", "МАГНИТ", "ЗАМОРОЗКА", "НЕВИДИМОСТЬ"]
        next_bonus_sec = 20 - (int(free_play_timer) % 20)
        b_txt = font_main.render(f"БОНУС: {bonus_names[current_phase]} ({next_bonus_sec}с)", True, (0, 255, 255))
        screen.blit(b_txt, (15, 260))

        # 6. Кнопка паузы (справа сверху)
        pause_btn_rect = pygame.Rect(WIDTH - 120, 20, 100, 100)
        pygame.draw.rect(screen, (40, 40, 60, 200), pause_btn_rect, border_radius=20)
        pygame.draw.rect(screen, WHITE, pause_btn_rect, 4, border_radius=20)
        pygame.draw.rect(screen, WHITE, (WIDTH - 95, 40, 15, 60))
        pygame.draw.rect(screen, WHITE, (WIDTH - 65, 40, 15, 60))
        
        if pygame.mouse.get_pressed()[0] and pause_btn_rect.collidepoint(m_pos):
            game_state = STATE_PAUSE
            pygame.time.delay(200)
        
        # 7. Проверка смерти и сохранение рекордов
        if player.hp <= 0:
            # Сверяем текущий результат с тем, что в сохранении
            if int(free_play_timer) > player_save.get("free_record_time", 0):
                player_save["free_record_time"] = int(free_play_timer)
            if free_play_kills > player_save.get("free_record_kills", 0):
                player_save["free_record_kills"] = free_play_kills
            
            save_game() # Записываем обновленный player_save в файл
            
            # Очистка перед выходом в меню
            enemies.clear()
            bullets.clear()
            enemy_bullets.clear()
            game_state = STATE_GAMEOVER

    # --- ЭКРАН ПОРАЖЕНИЯ ---
    elif game_state == STATE_GAMEOVER:
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        txt = font_big.render("ТЫ ПАЛ В БОЮ", True, (255, 0, 0))
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 150))
        
        # Кнопка В МЕНЮ
        btn_r = pygame.Rect(WIDTH//2 - 200, HEIGHT//2, 400, 100)
        pygame.draw.rect(screen, (0, 200, 100), btn_r, border_radius=20)
        t_menu = font_main.render("В МЕНЮ", True, WHITE)
        screen.blit(t_menu, (btn_r.centerx - t_menu.get_width()//2, btn_r.centery - t_menu.get_height()//2))
        
        if pygame.mouse.get_pressed()[0] and btn_r.collidepoint(m_pos):
            save_game()
            enemy_bullets.clear()
            game_state = STATE_MENU
            pygame.time.delay(200)

    # --- ЭКРАН БРИФИНГА (ПЕРЕД БОЕМ) ---
    elif game_state == STATE_BRIEFING:
        # Окно миссии
        brief_r = pygame.Rect(WIDTH//2-350, HEIGHT//2-450, 700, 900)
        pygame.draw.rect(screen, (20, 20, 40), brief_r, border_radius=40)
        pygame.draw.rect(screen, (0, 200, 255), brief_r, 6, border_radius=40)
        
        goal = mission_goals.get(selected_mission_id, {"desc": "Уничтожить врагов"})
        title = font_big.render(f"УРОВЕНЬ {selected_mission_id}", True, (255, 215, 0))
        
        # Текст описания (разбиваем на строки если длинный)
        desc_txt = goal["desc"]
        desc_render = font_main.render(desc_txt, True, WHITE)
        
        screen.blit(title, (brief_r.centerx - title.get_width()//2, brief_r.y + 60))
        screen.blit(desc_render, (brief_r.centerx - desc_render.get_width()//2, brief_r.y + 250))
        
        # Кнопка В БОЙ
        go_btn = pygame.Rect(brief_r.centerx-200, brief_r.bottom-150, 400, 100)
        pygame.draw.rect(screen, (0, 200, 100), go_btn, border_radius=25)
        t_go = font_main.render("В БОЙ!", True, WHITE)
        screen.blit(t_go, (go_btn.centerx - t_go.get_width()//2, go_btn.centery - t_go.get_height()//2))

        if pygame.mouse.get_pressed()[0] and go_btn.collidepoint(m_pos):
            enemy_bullets.clear()
            start_mission(selected_mission_id)
            pygame.time.delay(200)

    elif game_state == STATE_PAUSE:
        # 1. ЗАТЕМНЕНИЕ ФОНА
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        # 2. ОКНО ПАУЗЫ
        p_window = pygame.Rect(WIDTH//2 - 300, HEIGHT//2 - 400, 600, 700)
        pygame.draw.rect(screen, (30, 30, 50), p_window, border_radius=30)
        pygame.draw.rect(screen, (0, 200, 255), p_window, 5, border_radius=30)

        # 3. ТЕКСТ ПАУЗЫ
        p_title = font_big.render("ПАУЗА", True, WHITE)
        screen.blit(p_title, (p_window.centerx - p_title.get_width()//2, p_window.y + 40))

        # 4. ПРОГРЕСС ЦЕЛИ (БЕЗОПАСНЫЙ)
        try:
            # Если мы в Свободной игре (миссия не задана)
            if 'current_mission' not in globals() or current_mission is None:
                progress_txt = f"ВЫЖИВАНИЕ: {free_play_kills} КИЛЛОВ"
            else:
                goal = mission_goals.get(current_mission, {"kills": 999})
                if "kills" in goal:
                    progress_txt = f"УБИТО: {kills_count} / {goal['kills']}"
                elif "time" in goal:
                    progress_txt = f"ВРЕМЯ: {int(game_timer)} / {goal['time']} сек."
                else:
                    progress_txt = "БОСС ЖДЕТ ТЕБЯ"
        except:
            progress_txt = "ПАУЗА"

        p_prog = font_main.render(progress_txt, True, (255, 220, 0))
        screen.blit(p_prog, (p_window.centerx - p_prog.get_width()//2, p_window.y + 180))

        # 5. КНОПКИ
        btn_cont = pygame.Rect(p_window.centerx - 200, p_window.y + 350, 400, 100)
        btn_menu = pygame.Rect(p_window.centerx - 200, p_window.y + 500, 400, 100)

        for btn, txt, col in [(btn_cont, "ПРОДОЛЖИТЬ", (0, 200, 100)), (btn_menu, "В МЕНЮ", (200, 50, 50))]:
            pygame.draw.rect(screen, col, btn, border_radius=20)
            t_render = font_main.render(txt, True, WHITE)
            screen.blit(t_render, (btn.centerx - t_render.get_width()//2, btn.centery - t_render.get_height()//2))

        # Обработка кликов
        if pygame.mouse.get_pressed()[0]:
            if btn_cont.collidepoint(m_pos):
                # Проверяем, куда возвращаться
                if 'current_mission' in globals() and current_mission is not None:
                    game_state = STATE_GAME
                else:
                    game_state = STATE_FREE_PLAY
                pygame.time.delay(200)
            elif btn_menu.collidepoint(m_pos):
                save_game()
                enemy_bullets.clear()
                game_state = STATE_MENU
                pygame.time.delay(200)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
