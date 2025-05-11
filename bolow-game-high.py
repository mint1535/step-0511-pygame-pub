import pygame
from pygame.locals import *
import sys
import random

pygame.init()

screen_width = 600
screen_height = 800
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("ブロック避けゲーム")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
COLORS = [RED, BLUE, GREEN]

player_width = 50
player_height = 50
player_x = screen_width // 2 - player_width // 2
player_y = screen_height - player_height - 20
player_speed = 8
player = pygame.Rect(player_x, player_y, player_width, player_height)

block_width = 80
block_height = 20
block_speed = 5
blocks = []
block_spawn_time = 1000

score = 0
game_over = False
clock = pygame.time.Clock()
last_block_time = pygame.time.get_ticks()
font = pygame.font.SysFont(None, 36)

high_scores = []
SERVER_HOST = "localhost"
SERVER_PORT = 5000
client_socket = None
scoreboard_font = pygame.font.SysFont(None, 24)
scoreboard_width = 150
scoreboard_height = 150
scoreboard_margin = 10
scoreboard_bg_color = (0, 0, 0, 128)

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

        # プレイヤーの移動 (追加)

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

        screen.fill(BLACK)

        pygame.draw.rect(screen, WHITE, player)

        for block_data in blocks:
            pygame.draw.rect(screen, block_data[1], block_data[0])

        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

    pygame.display.flip()
    clock.tick(60)
