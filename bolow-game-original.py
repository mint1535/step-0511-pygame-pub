import pygame
from pygame.locals import *
import sys
import random
import socket
import json
import threading
import time

# ゲームの初期化
pygame.init()

# 画面の設定
screen_width = 600
screen_height = 800
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("ブロック避けゲーム")

# 色の設定
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
COLORS = [RED, BLUE, GREEN]

# プレイヤーの設定
player_width = 50
player_height = 50
player_x = screen_width // 2 - player_width // 2
player_y = screen_height - player_height - 20
player_speed = 8
player = pygame.Rect(player_x, player_y, player_width, player_height)

# ブロックの設定
block_width = 80
block_height = 20
block_speed = 5
blocks = []
block_spawn_time = 1000

# スコアの設定
score = 0
game_over = False
clock = pygame.time.Clock()
last_block_time = pygame.time.get_ticks()
font = pygame.font.SysFont(None, 36)

# スコアボードの設定
high_scores = []
SERVER_HOST = "localhost"
SERVER_PORT = 5000
client_socket = None
scoreboard_font = pygame.font.SysFont(None, 24)
scoreboard_width = 150
scoreboard_height = 150
scoreboard_margin = 10
scoreboard_bg_color = (0, 0, 0, 128)

# サーバーへ接続する
def connect_to_server():
    """スコアサーバーへ接続する"""
    global client_socket
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        return True
    except:
        return False

# サーバーからスコアを受信する
def receive_scores():
    """サーバーからスコアを受信する"""
    global high_scores, client_socket
    while True:
        try:
            if client_socket:
                data = client_socket.recv(1024).decode()
                if data:
                    message = json.loads(data)
                    if message["type"] == "scores":
                        high_scores = message["data"]
        except:
            time.sleep(1)  # 失敗時は少し待つ

# 新しいスコアをサーバーに送信する
def update_high_scores(new_score):
    """新しいスコアをサーバーに送信する"""
    global client_socket
    if client_socket:
        try:
            message = json.dumps({"type": "new_score", "score": new_score})
            client_socket.send(message.encode())
        except:
            # サーバーに送信できない場合はローカルで管理
            high_scores.append(new_score)
            high_scores.sort(reverse=True)
            high_scores = high_scores[:5]

# スコアボードを描画する
def draw_scoreboard():
    """画面右上にスコアボードを描画する"""
    # アルファチャンネル付きのサーフェスを作成
    scoreboard_surface = pygame.Surface((scoreboard_width, scoreboard_height), pygame.SRCALPHA)
    
    # 半透明の背景を塗る
    pygame.draw.rect(scoreboard_surface, scoreboard_bg_color, 
                    (0, 0, scoreboard_width, scoreboard_height))
    
    # 枠線を描画
    pygame.draw.rect(scoreboard_surface, WHITE, 
                    (0, 0, scoreboard_width, scoreboard_height), 1)
    
    # タイトル描画
    title = scoreboard_font.render("Top Scores", True, WHITE)
    scoreboard_surface.blit(title, (scoreboard_margin, scoreboard_margin))
    
    # スコアを描画
    for i, score in enumerate(high_scores[:5]):
        score_text = scoreboard_font.render(f"{i+1}. {score}", True, WHITE)
        scoreboard_surface.blit(score_text, 
                              (scoreboard_margin, 
                               scoreboard_margin + 25 + i * 20))
    
    # 画面右上にスコアボードを合成
    screen.blit(scoreboard_surface, 
                (screen_width - scoreboard_width - scoreboard_margin, 
                 scoreboard_margin))

# サーバーに接続してスコアを受信する
if connect_to_server():
    receive_thread = threading.Thread(target=receive_scores)
    receive_thread.daemon = True
    receive_thread.start()
else:
    print("Could not connect to server. Running in offline mode.")

while True:
    current_time = pygame.time.get_ticks()
    
    for event in pygame.event.get():
        if event.type == QUIT:
            if client_socket:
                client_socket.close()
            pygame.quit()
            sys.exit()
        
        if game_over and event.type == KEYDOWN:
            if event.key == K_SPACE:
                game_over = False
                blocks = []
                score = 0
                player.x = screen_width // 2 - player_width // 2
                player.y = screen_height - player_height - 20
                block_speed = 5
                last_block_time = current_time
    
    if not game_over:
        keys = pygame.key.get_pressed()
        if keys[K_LEFT] and player.left > 0:
            player.x -= player_speed
        if keys[K_RIGHT] and player.right < screen_width:
            player.x += player_speed
        
        if current_time - last_block_time > block_spawn_time:
            block_x = random.randint(0, screen_width - block_width)
            block_width_random = random.randint(60, 120)
            new_block = pygame.Rect(block_x, 0, block_width_random, block_height)
            blocks.append([new_block, random.choice(COLORS)])
            last_block_time = current_time
            
            if score > 0 and score % 10 == 0:
                block_speed += 0.5
                if block_spawn_time > 500:
                    block_spawn_time -= 50
        
        for block_data in blocks[:]:
            block = block_data[0]
            block.y += block_speed
            
            if block.y > screen_height:
                blocks.remove(block_data)
                score += 1
            
            if block.colliderect(player):
                game_over = True
                update_high_scores(score)
        
        screen.fill(BLACK)
        
        pygame.draw.rect(screen, WHITE, player)
        
        for block_data in blocks:
            pygame.draw.rect(screen, block_data[1], block_data[0])
        
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        draw_scoreboard()
        
    else:
        screen.fill(BLACK)
        game_over_text = font.render("GAME OVER", True, RED)
        final_score_text = font.render(f"Final Score: {score}", True, WHITE)
        restart_text = font.render("Press SPACE to restart", True, WHITE)
        
        screen.blit(game_over_text, (screen_width // 2 - game_over_text.get_width() // 2, 
                                     screen_height // 2 - 100))
        screen.blit(final_score_text, (screen_width // 2 - final_score_text.get_width() // 2, 
                                       screen_height // 2 - 50))
        screen.blit(restart_text, (screen_width // 2 - restart_text.get_width() // 2, 
                                   screen_height // 2))
        
        draw_scoreboard()
    
    pygame.display.flip()
    clock.tick(60)
