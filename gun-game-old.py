import pygame
from pygame.locals import *
import sys
import random
import os
import platform
# import requests  # スコアボード機能削除のためコメントアウト

pygame.init()

# URL = 'http://localhost:5050'  # スコアボード機能削除

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

# ターゲット設定
targets = []
target_size_fixed = 30
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

# ゲームの状態
game_state = "playing"
start_time = pygame.time.get_ticks()

def spawn_target():
    """ランダムな位置と大きさでターゲットを生成"""
    size = target_size_fixed  # 固定サイズ
    x = random.randint(0, SCREEN_WIDTH - size)
    y = random.randint(0, SCREEN_HEIGHT - size - crosshair_size * 2)
    target_type = "normal"
    speed_x = random.choice([-3, -2, -1, 1, 2, 3])
    speed_y = random.choice([-3, -2, -1, 1, 2, 3])
    points = 10  # 固定ポイント
    targets.append({
        "rect": pygame.Rect(x, y, size, size),
        "color": RED,
        "speed_x": speed_x,
        "speed_y": speed_y,
        "type": target_type,
        "points": points,
    })

def update_targets():
    """ターゲットの移動と画面外チェック"""
    for target in targets:
        # ターゲットの移動速度が徐々に速くなるバグ
        target["speed_x"] *= 1.01
        target["speed_y"] *= 1.01
        target["rect"].x += int(target["speed_x"])
        target["rect"].y += int(target["speed_y"])
        # ランダムで移動方向を少し変える（より予測しにくい動きに）
        if random.random() < 0.02:
            target["speed_x"] += random.choice([-0.5, 0.5])
            target["speed_y"] += random.choice([-0.5, 0.5])
            target["speed_x"] = max(min(target["speed_x"], 4), -4)
            target["speed_y"] = max(min(target["speed_y"], 4), -4)
        # 画面端で跳ね返る
        if target["rect"].left < 0 or target["rect"].right > SCREEN_WIDTH:
            target["speed_x"] *= -1
        if target["rect"].top < 0 or target["rect"].bottom > crosshair_y_position - 10:
            target["speed_y"] *= -1
        # 敵の攻撃処理削除
        # if current_time - target["last_shot_time"] > enemy_shoot_cooldown:
        #     if random.random() < 0.4:
        #         for i in range(3):
        #             spread = random.randint(-10, 10)
        #             enemy_bullets.append(pygame.Rect(
        #                 target["rect"].centerx - enemy_bullet_size // 2 + spread,
        #                 target["rect"].bottom,
        #                 enemy_bullet_size,
        #                 enemy_bullet_size
        #             ))
        #         target["last_shot_time"] = current_time

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
    
    # 照準の描画
    pygame.draw.rect(screen, GREEN, crosshair, 2)
    
    # スコアと残り時間の表示
    remaining_time = max(0, GAME_TIME - (pygame.time.get_ticks() - start_time))
    draw_text(f"残り時間: {remaining_time // 1000}秒", 10, 10)
    draw_text(f"スコア: {score}", 10, 50)

def draw_game_over():
    """ゲームオーバー画面の描画"""
    screen.fill(BLACK)
    
    # テキスト位置を調整するための計算
    center_x = SCREEN_WIDTH // 2
    
    # ゲームオーバーテキスト
    game_over_text = draw_text("ゲーム終了！", center_x - 100, SCREEN_HEIGHT // 2 - 60)
    
    # スコアテキスト
    score_text = draw_text(f"最終スコア: {score}", center_x - 100, SCREEN_HEIGHT // 2)
    
    # リスタート時のテキスト
    draw_text("Rキーでリスタート", center_x - 100, SCREEN_HEIGHT // 2 + 80)

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
                game_state = "playing"
                score = 0
                targets.clear()
                bullets.clear()
                shots_fired = 0
                shots_hit = 0
                crosshair.x = SCREEN_WIDTH // 2 - crosshair_size // 2
                crosshair.y = crosshair_y_position
                start_time = current_time
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
                pass
            elif event.key == K_ESCAPE:
                pass
    
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
        for bullet in bullets[:]:
            bullet.y -= bullet_speed
            if bullet.bottom < 0:
                bullets.remove(bullet)
        
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
        
        draw_game()
    else:  # game_over状態
        draw_game_over()
    
    pygame.display.flip()
    clock.tick(FPS)
