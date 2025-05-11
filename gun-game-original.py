import pygame
from pygame.locals import *
import sys
import random
import os
import platform
import requests
import json
import threading

pygame.init()

URL = 'http://localhost:5050'

# ウィンドウ設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("ターゲットヒットゲーム")

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# ゲーム設定
FPS = 60
clock = pygame.time.Clock()
GAME_TIME = 30000  # 30秒（ミリ秒）

# プレイヤーの設定
PLAYER_HEALTH = 100  # プレイヤーの最大体力
player_health = PLAYER_HEALTH  # 現在の体力
player_invincible = False  # 無敵状態フラグ
invincible_time = 1000  # 無敵時間（ミリ秒）
last_hit_time = 0  # 最後にダメージを受けた時間

# プレイヤーの照準（画面下部中央に配置）
crosshair_size = 30
crosshair_y_position = SCREEN_HEIGHT - crosshair_size - 20
crosshair = pygame.Rect(SCREEN_WIDTH // 2 - crosshair_size // 2, 
                      crosshair_y_position, 
                      crosshair_size, crosshair_size)
crosshair_speed = 5

# 弾の設定
bullets = []
bullet_size = 10
bullet_speed = 10
cooldown_time = 300  # 弾の発射クールダウン（ミリ秒）
last_shot_time = 0

# 敵の弾の設定
enemy_bullets = []
enemy_bullet_size = 8
enemy_bullet_speed = 7
enemy_shoot_cooldown = 1500

# ターゲット設定
targets = []
target_size_min = 15
target_size_max = 40
spawn_time = 800
last_spawn_time = 0
max_targets = 7

# スコア
score = 0
shots_fired = 0
shots_hit = 0

# プラットフォーム検出
system_platform = platform.system()

# フォント設定（プラットフォーム別）
def get_font(size=36):
    """プラットフォームに応じた適切な日本語フォントを取得する。sizeでフォントサイズ指定可"""
    if system_platform == "Darwin":  # Mac OS
        mac_fonts = [
            '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc',
            '/System/Library/Fonts/Hiragino Sans GB.ttc',
            '/System/Library/Fonts/AppleSDGothicNeo.ttc',
            '/Library/Fonts/Osaka.ttf',
            '/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc'
        ]
        mac_sys_fonts = ['Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'AppleGothic', 'Osaka']
        for font_path in mac_fonts:
            if os.path.exists(font_path):
                try:
                    return pygame.font.Font(font_path, size)
                except:
                    pass
        for font_name in mac_sys_fonts:
            try:
                return pygame.font.SysFont(font_name, size)
            except:
                pass
    elif system_platform == "Windows":
        win_fonts = ['Yu Gothic', 'MS Gothic', 'Meiryo', 'MS Mincho', 'Yu Mincho', 'MS PGothic']
        for font_name in win_fonts:
            try:
                return pygame.font.SysFont(font_name, size)
            except:
                pass
    common_fonts = ['Arial Unicode MS', 'Sans', 'FreeSans']
    for font_name in common_fonts:
        try:
            return pygame.font.SysFont(font_name, size)
        except:
            pass
    print("警告: 適切な日本語フォントが見つかりませんでした。デフォルトフォントを使用します。")
    return pygame.font.SysFont(None, size)

# プラットフォーム情報を表示
print(f"実行プラットフォーム: {system_platform}")

# フォントオブジェクトを取得
font = get_font(36)

# スコアボード用フォントサイズ
SCOREBOARD_TITLE_SIZE = 24
SCOREBOARD_HEADER_SIZE = 20
SCOREBOARD_TEXT_SIZE = 18

# スコアボード用フォント
scoreboard_title_font = None
scoreboard_header_font = None
scoreboard_text_font = None

def init_scoreboard_fonts():
    """スコアボード用フォントの初期化 (get_fontを利用)"""
    global scoreboard_title_font, scoreboard_header_font, scoreboard_text_font
    try:
        scoreboard_title_font = get_font(SCOREBOARD_TITLE_SIZE)
        scoreboard_header_font = get_font(SCOREBOARD_HEADER_SIZE)
        scoreboard_text_font = get_font(SCOREBOARD_TEXT_SIZE)
    except:
        scoreboard_title_font = pygame.font.Font(None, SCOREBOARD_TITLE_SIZE)
        scoreboard_header_font = pygame.font.Font(None, SCOREBOARD_HEADER_SIZE)
        scoreboard_text_font = pygame.font.Font(None, SCOREBOARD_TEXT_SIZE)

# スコアボード用フォントを初期化
init_scoreboard_fonts()

# ゲームの状態
game_state = "playing"
start_time = pygame.time.get_ticks()

# スコアボード設定
player_name = "Player1"  # デフォルトのプレイヤー名
scoreboard_data = []
scoreboard_visible = True  # デフォルトで表示
scoreboard_update_interval = 5000  # 5秒ごとに更新
last_scoreboard_update = 0

def connect_to_scoreboard():
    """スコアボードサーバーに接続"""
    try:
        response = requests.get(f"{URL}/get_scores")
        if response.status_code == 200:
            get_scoreboard()  # 接続時に初期データを取得
            return True
        return False
    except Exception as e:
        print(f"スコアボードサーバーへの接続に失敗しました: {e}")
        return False

def submit_score():
    """スコアをサーバーに送信"""
    try:
        accuracy = (shots_hit / shots_fired * 100) if shots_fired > 0 else 0
        data = {
            'player_name': player_name,
            'score': score,
            'accuracy': accuracy
        }
        response = requests.post(f"{URL}/submit_score", json=data)
        if response.status_code == 200:
            print("スコアを送信しました")
    except Exception as e:
        print(f"スコアの送信に失敗しました: {e}")

def get_scoreboard():
    """スコアボードデータを取得"""
    global scoreboard_data
    try:
        response = requests.get(f"{URL}/get_scores")
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                scoreboard_data = data['scores']
            else:
                print(f"スコアボード更新エラー: {data.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"スコアボードの取得に失敗しました: {e}")

def spawn_target():
    """ランダムな位置と大きさでターゲットを生成"""
    size = random.randint(target_size_min, target_size_max)
    # 40%の確率で最小サイズに近いターゲットを生成
    if random.random() < 0.4:
        size = random.randint(target_size_min, target_size_min + 10)
    
    x = random.randint(0, SCREEN_WIDTH - size)
    y = random.randint(0, SCREEN_HEIGHT - size - crosshair_size * 2)
    
    # normal: 通常ターゲット(赤), minus: マイナススコアターゲット(青)
    target_type = "normal" if random.random() > 0.3 else "minus"
    
    speed_x = random.choice([-3, -2, -1, 1, 2, 3])
    speed_y = random.choice([-3, -2, -1, 1, 2, 3])
    
    if target_type == "normal":
        points = max(2, int((target_size_max - size) / 4))
    else:
        points = -5
    
    targets.append({
        "rect": pygame.Rect(x, y, size, size),
        "color": RED if target_type == "normal" else BLUE,
        "speed_x": speed_x,
        "speed_y": speed_y,
        "type": target_type,
        "points": points,
        "last_shot_time": 0
    })

def update_targets():
    """ターゲットの移動と画面外チェック"""
    global enemy_bullets
    
    current_time = pygame.time.get_ticks()
    
    for target in targets:
        # ターゲットを移動
        target["rect"].x += target["speed_x"]
        target["rect"].y += target["speed_y"]
        
        # ランダムで移動方向を少し変える
        if random.random() < 0.02:  # 2%の確率で
            target["speed_x"] += random.choice([-0.5, 0.5])
            target["speed_y"] += random.choice([-0.5, 0.5])
            # 速度の上限を設定
            target["speed_x"] = max(min(target["speed_x"], 4), -4)
            target["speed_y"] = max(min(target["speed_y"], 4), -4)
        
        # 画面端で跳ね返る
        # 端で-1をかけることで方向を反対にする
        if target["rect"].left < 0 or target["rect"].right > SCREEN_WIDTH:
            target["speed_x"] *= -1
        if target["rect"].top < 0 or target["rect"].bottom > crosshair_y_position - 10:
            target["speed_y"] *= -1
        
        # 敵の攻撃（攻撃確率を上げる）
        if current_time - target["last_shot_time"] > enemy_shoot_cooldown:
            if random.random() < 0.4:  # 40%の確率で攻撃
                # 弾を3発発射
                for i in range(3):
                    spread = random.randint(-10, 10)  # 弾をばらつかせる
                    enemy_bullets.append(pygame.Rect(
                        target["rect"].centerx - enemy_bullet_size // 2 + spread,
                        target["rect"].bottom,
                        enemy_bullet_size,
                        enemy_bullet_size
                    ))
                target["last_shot_time"] = current_time

def draw_text(text, x, y, color=WHITE):
    """テキストを描画する"""
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))
    return text_surface

def draw_game():
    """ゲーム画面の描画"""
    screen.fill(BLACK)
    
    # ターゲットの描画
    for target in targets:
        pygame.draw.rect(screen, target["color"], target["rect"])
    
    # 弾の描画
    for bullet in bullets:
        pygame.draw.rect(screen, YELLOW, bullet)
    
    # 敵の弾の描画
    for bullet in enemy_bullets:
        pygame.draw.rect(screen, RED, bullet)
    
    # 照準の描画
    pygame.draw.rect(screen, GREEN, crosshair, 2)
    
    # 体力バーの描画
    health_bar_width = 200
    health_bar_height = 20
    health_bar_x = SCREEN_WIDTH - health_bar_width - 20
    health_bar_y = 20
    
    # 体力バーの背景
    pygame.draw.rect(screen, (100, 100, 100), 
                    (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
    
    # 現在の体力
    current_health_width = int((player_health / PLAYER_HEALTH) * health_bar_width)
    health_color = (0, 255, 0) if player_health > PLAYER_HEALTH * 0.5 else (255, 0, 0)
    pygame.draw.rect(screen, health_color,
                    (health_bar_x, health_bar_y, current_health_width, health_bar_height))
    
    # 体力バーの枠
    pygame.draw.rect(screen, WHITE,
                    (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 2)
    
    # スコアと残り時間の表示
    remaining_time = max(0, GAME_TIME - (pygame.time.get_ticks() - start_time))
    draw_text(f"残り時間: {remaining_time // 1000}秒", 10, 10)
    draw_text(f"スコア: {score}", 10, 50)
    
    # 命中率の表示
    if shots_fired > 0:
        accuracy = (shots_hit / shots_fired) * 100
        draw_text(f"命中率: {accuracy:.1f}%", 10, 90)
    
    draw_scoreboard()

def draw_game_over():
    """ゲームオーバー画面の描画"""
    screen.fill(BLACK)
    
    # テキスト位置を調整するための計算
    center_x = SCREEN_WIDTH // 2
    
    # ゲームオーバーテキスト
    draw_text("ゲーム終了！", center_x - 100, SCREEN_HEIGHT // 2 - 60)

    # スコアテキスト
    draw_text(f"最終スコア: {score}", center_x - 100, SCREEN_HEIGHT // 2)
    
    # 命中率テキスト
    if shots_fired > 0:
        accuracy = (shots_hit / shots_fired) * 100
        draw_text(f"命中率: {accuracy:.1f}%", center_x - 100, SCREEN_HEIGHT // 2 + 40)
    
    # リスタート時のテキスト
    draw_text("Rキーでリスタート", center_x - 100, SCREEN_HEIGHT // 2 + 80)

def draw_scoreboard_text(text, x, y, color, font_type='text'):
    """スコアボード用テキスト"""
    if font_type == 'title':
        font_obj = scoreboard_title_font
    elif font_type == 'header':
        font_obj = scoreboard_header_font
    else:
        font_obj = scoreboard_text_font
    
    text_surface = font_obj.render(text, True, color)
    screen.blit(text_surface, (x, y))
    return text_surface

def draw_scoreboard():
    """スコアボードを描画"""
    if not scoreboard_visible:
        return

    # スコアボードの枠
    board_width = 250
    board_height = 180
    board_x = SCREEN_WIDTH - board_width - 10
    board_y = 50
    
    # 半透明の黒い背景
    overlay = pygame.Surface((board_width, board_height))
    overlay.set_alpha(180)
    overlay.fill(BLACK)
    screen.blit(overlay, (board_x, board_y))
    
    # 枠線
    pygame.draw.rect(screen, WHITE, (board_x, board_y, board_width, board_height), 2)

    # タイトル
    draw_scoreboard_text("スコアボード (TABで更新)", board_x + 10, board_y + 10, WHITE, 'title')

    # ヘッダー
    y = board_y + 40
    header_color = (200, 200, 200)
    draw_scoreboard_text("順位", board_x + 10, y, header_color, 'header')
    draw_scoreboard_text("プレイヤー", board_x + 50, y, header_color, 'header')
    draw_scoreboard_text("スコア", board_x + 150, y, header_color, 'header')
    draw_scoreboard_text("命中率", board_x + 190, y, header_color, 'header')

    # スコアデータ（上位5件のみ表示）
    for i, score_data in enumerate(scoreboard_data[:5]):
        y = board_y + 65 + i * 22
        color = (255, 255, 0) if score_data['player_name'] == player_name else WHITE
        draw_scoreboard_text(f"{i+1}", board_x + 10, y, color)
        draw_scoreboard_text(score_data['player_name'][:8], board_x + 50, y, color)
        draw_scoreboard_text(str(score_data['score']), board_x + 150, y, color)
        draw_scoreboard_text(f"{score_data['accuracy']:.1f}%", board_x + 190, y, color)

def restart_game():
    """ゲームをリスタート"""
    global game_state, score, targets, bullets, enemy_bullets, start_time
    global shots_fired, shots_hit, crosshair, player_health
    game_state = "playing"
    score = 0
    targets = []
    bullets = []
    enemy_bullets = []
    shots_fired = 0
    shots_hit = 0
    player_health = PLAYER_HEALTH
    crosshair.x = SCREEN_WIDTH // 2 - crosshair_size // 2
    crosshair.y = crosshair_y_position
    start_time = pygame.time.get_ticks()

# メインゲームループの前にサーバー接続を初期化
print("スコアボードサーバーに接続しています...")  # デバッグ用
if not connect_to_scoreboard():
    print("スコアボード機能は利用できません")
else:
    print("スコアボードサーバーに接続しました")  # デバッグ用
    get_scoreboard()  # 初期データを取得

# メインゲームループ
while True:
    current_time = pygame.time.get_ticks()
    
    # イベント処理
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        
        #キーが押されたときの動作
        if event.type == KEYDOWN:
            if event.key == K_r and game_state == "game_over":
                restart_game()
            elif event.key == K_SPACE and game_state == "playing":
                if current_time - last_shot_time > cooldown_time:
                    bullets.append(pygame.Rect(
                        crosshair.centerx - bullet_size // 2,
                        crosshair.centery - bullet_size // 2,
                        bullet_size, bullet_size
                    ))
                    last_shot_time = current_time
                    shots_fired += 1
            elif event.key == K_TAB:
                get_scoreboard()
            elif event.key == K_ESCAPE:
                scoreboard_visible = not scoreboard_visible
    
    # スコアボードの自動更新
    if current_time - last_scoreboard_update > scoreboard_update_interval:
        get_scoreboard()
        last_scoreboard_update = current_time
    
    #ゲーム中の処理
    if game_state == "playing":
        # 既存のゲームロジック
        keys = pygame.key.get_pressed()
        # 左矢印が押された場合
        if keys[K_LEFT]:
            crosshair.x = max(0, crosshair.x - crosshair_speed)
        # 右矢印が押された場合
        if keys[K_RIGHT]:
            crosshair.x = min(SCREEN_WIDTH - crosshair.width, crosshair.x + crosshair_speed)
        
        # プレイヤーの弾の移動
        # :をつけることでリストの先頭から順に処理
        for bullet in bullets[:]:
            bullet.y -= bullet_speed
            if bullet.bottom < 0:
                bullets.remove(bullet)
        
        # 敵の弾の移動
        for bullet in enemy_bullets[:]: #[:]で新しくリストを作成 -> オリジナルのリストの内容を変更しないため
            bullet.y += enemy_bullet_speed
            if bullet.top > SCREEN_HEIGHT:
                enemy_bullets.remove(bullet)
            # プレイヤーとの当たり判定
            elif not player_invincible and bullet.colliderect(crosshair):
                player_health -= 10
                enemy_bullets.remove(bullet)
                player_invincible = True
                last_hit_time = current_time
                if player_health <= 0:
                    game_state = "game_over"
                    submit_score()
        
        # 無敵時間の処理
        if player_invincible and current_time - last_hit_time > invincible_time:
            player_invincible = False
        
        if current_time - last_spawn_time > spawn_time and len(targets) < max_targets:
            spawn_target()
            last_spawn_time = current_time
        
        update_targets()
        
        # プレイヤーの弾とターゲットの当たり判定
        for bullet in bullets[:]:
            for target in targets[:]:
                if bullet in bullets and target in targets and bullet.colliderect(target["rect"]):
                    score += target["points"]
                    targets.remove(target)
                    bullets.remove(bullet)
                    shots_hit += 1
        
        if current_time - start_time >= GAME_TIME:
            game_state = "game_over"
            submit_score()
        
        draw_game()
    else:  # game_over状態
        draw_game_over()
    
    pygame.display.flip()
    clock.tick(FPS)
