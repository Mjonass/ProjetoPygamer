import pygame
from pygame import mixer
import os
import random
import csv
import button

mixer.init()
pygame.init()


tela_largura = 800
tela_altura = int(tela_largura * 0.8)

tela = pygame.display.set_mode((tela_largura, tela_altura))
pygame.display.set_caption('Jogo de Tiro - Projeto Pygame')

#definir taxa de quadros
clock = pygame.time.Clock()
FPS = 60

#definir variáveis ​​de jogo
GRAVITY = 0.75
SCROLL_THRESH = 200
ROWS = 16
COLS = 150
TILE_SIZE = tela_altura // ROWS
TILE_TYPES = 21
MAX_LEVELS = 3
tela_scroll = 0
bg_scroll = 0
level = 1
start_game = False
start_intro = False


#definir variáveis ​​de ação do jogador
mover_esquerda = False
mover_direita = False
shoot = False
grenade = False
grenade_thrown = False


#carregar música e sons
jump_fx = pygame.mixer.Sound('audio/jump.wav')
jump_fx.set_volume(0.05)
shot_fx = pygame.mixer.Sound('audio/shot.wav')
shot_fx.set_volume(0.05)
grenade_fx = pygame.mixer.Sound('audio/grenade.wav')
grenade_fx.set_volume(0.05)


#carregar imagens
#imagens de botão
start_img = pygame.image.load('img/start_btn.png').convert_alpha()
exit_img = pygame.image.load('img/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('img/restart_btn.png').convert_alpha()
#fundo
pine1_img = pygame.image.load('img/Background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('img/Background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('img/Background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/Background/sky_cloud.png').convert_alpha()
#armazenar blocos em uma lista
img_list = []
for x in range(TILE_TYPES):
	img = pygame.image.load(f'img/Tile/{x}.png')
	img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
	img_list.append(img)
#bala
bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()
#granada
grenade_img = pygame.image.load('img/icons/grenade.png').convert_alpha()
#pegar caixas
health_box_img = pygame.image.load('img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('img/icons/grenade_box.png').convert_alpha()
item_boxes = {
	'Health'	: health_box_img,
	'Ammo'		: ammo_box_img,
	'Grenade'	: grenade_box_img
}


#definir cores
BG = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
PINK = (235, 65, 54)

#definir fonte
font = pygame.font.SysFont('Futura', 30)

def draw_text(text, font, text_col, x, y):
	img = font.render(text, True, text_col)
	tela.blit(img, (x, y))


def draw_bg():
	tela.fill(BG)
	width = sky_img.get_width()
	for x in range(5):
		tela.blit(sky_img, ((x * width) - bg_scroll * 0.5, 0))
		tela.blit(mountain_img, ((x * width) - bg_scroll * 0.6, tela_altura - mountain_img.get_height() - 300))
		tela.blit(pine1_img, ((x * width) - bg_scroll * 0.7, tela_altura - pine1_img.get_height() - 150))
		tela.blit(pine2_img, ((x * width) - bg_scroll * 0.8, tela_altura - pine2_img.get_height()))


#função para redefinir o nível
def reset_level():
	enemy_group.empty()
	bullet_group.empty()
	grenade_group.empty()
	explosion_group.empty()
	item_box_group.empty()
	decoration_group.empty()
	water_group.empty()
	exit_group.empty()

	#criar lista de blocos vazia
	data = []
	for row in range(ROWS):
		r = [-1] * COLS
		data.append(r)

	return data




class Soldier(pygame.sprite.Sprite):
	def __init__(self, char_type, x, y, scale, speed, ammo, grenades):
		pygame.sprite.Sprite.__init__(self)
		self.alive = True
		self.char_type = char_type
		self.speed = speed
		self.ammo = ammo
		self.start_ammo = ammo
		self.shoot_cooldown = 0
		self.grenades = grenades
		self.health = 100
		self.max_health = self.health
		self.direction = 1
		self.vel_y = 0
		self.jump = False
		self.in_air = True
		self.flip = False
		self.animation_list = []
		self.frame_index = 0
		self.action = 0
		self.update_time = pygame.time.get_ticks()
		#variáveis ​​específicas de IA
		self.move_counter = 0
		self.vision = pygame.Rect(0, 0, 150, 20)
		self.idling = False
		self.idling_counter = 0
		
		#carregue todas as imagens para os jogadores
		animation_types = ['Idle', 'Run', 'Jump', 'Death']
		for animation in animation_types:
			#redefinir lista temporária de imagens
			temp_list = []
			#conte o número de arquivos na pasta
			num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
			for i in range(num_of_frames):
				img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha()
				img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
				temp_list.append(img)
			self.animation_list.append(temp_list)

		self.image = self.animation_list[self.action][self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()


	def update(self):
		self.update_animation()
		self.check_alive()
		#atualizar o tempo de espera
		if self.shoot_cooldown > 0:
			self.shoot_cooldown -= 1


	def move(self, mover_esquerda, mover_direita):
		#redefinir variáveis ​​de movimento
		tela_scroll = 0
		dx = 0
		dy = 0

		#atribuir variáveis ​​de movimento se mover para a esquerda ou direita
		if mover_esquerda:
			dx = -self.speed
			self.flip = True
			self.direction = -1
		if mover_direita:
			dx = self.speed
			self.flip = False
			self.direction = 1

		#pulo
		if self.jump == True and self.in_air == False:
			self.vel_y = -11
			self.jump = False
			self.in_air = True

		#aplicar gravidade
		self.vel_y += GRAVITY
		if self.vel_y > 10:
			self.vel_y
		dy += self.vel_y

		#verificar se há colisão
		for tile in world.obstacle_list:
			#verifique a colisão na direção x
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				dx = 0
				#se o AI atingiu uma parede, faça-o virar
				if self.char_type == 'enemy':
					self.direction *= -1
					self.move_counter = 0
			#verifique se há colisão na direção y
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				#verifique se está abaixo do solo, ou seja, pulando
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top
				#verifique se está acima do solo, ou seja, caindo
				elif self.vel_y >= 0:
					self.vel_y = 0
					self.in_air = False
					dy = tile[1].top - self.rect.bottom


		#verificar se há colisão com água
		if pygame.sprite.spritecollide(self, water_group, False):
			self.health = 0

		#verifique se há colisão com a saída
		level_complete = False
		if pygame.sprite.spritecollide(self, exit_group, False):
			level_complete = True

		#cverifique se caiu do mapa
		if self.rect.bottom > tela_altura:
			self.health = 0


		#verifique se está saindo das bordas da tela
		if self.char_type == 'player':
			if self.rect.left + dx < 0 or self.rect.right + dx > tela_largura:
				dx = 0

		#update rectangle position
		self.rect.x += dx
		self.rect.y += dy

		#atualizar a rolagem com base na posição do jogador
		if self.char_type == 'player':
			if (self.rect.right > tela_largura - SCROLL_THRESH and bg_scroll < (world.level_length * TILE_SIZE) - tela_largura)\
				or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
				self.rect.x -= dx
				tela_scroll = -dx

		return tela_scroll, level_complete



	def shoot(self):
		if self.shoot_cooldown == 0 and self.ammo > 0:
			self.shoot_cooldown = 20
			bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
			bullet_group.add(bullet)
			#reduzir munição
			self.ammo -= 1
			shot_fx.play()


	def ai(self):
		if self.alive and player.alive:
			if self.idling == False and random.randint(1, 200) == 1:
				self.update_action(0)#0: idle
				self.idling = True
				self.idling_counter = 50
			#verifique se o AI está perto do jogador
			if self.vision.colliderect(player.rect):
				#pare de correr e enfrente o jogador
				self.update_action(0)
				#atirar
				self.shoot()
			else:
				if self.idling == False:
					if self.direction == 1:
						ai_mover_direita = True
					else:
						ai_mover_direita = False
					ai_mover_esquerda = not ai_mover_direita
					self.move(ai_mover_esquerda, ai_mover_direita)
					self.update_action(1)
					self.move_counter += 1
					#atualize a visão AI conforme o inimigo se move
					self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

					if self.move_counter > TILE_SIZE:
						self.direction *= -1
						self.move_counter *= -1
				else:
					self.idling_counter -= 1
					if self.idling_counter <= 0:
						self.idling = False

		#rolagem
		self.rect.x += tela_scroll


	def update_animation(self):
		#animação de atualização
		ANIMATION_COOLDOWN = 100
		#atualizar imagem dependendo do quadro atual
		self.image = self.animation_list[self.action][self.frame_index]
		#verifique se passou tempo suficiente desde a última atualização
		if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
			self.update_time = pygame.time.get_ticks()
			self.frame_index += 1
		#se a animação acabou, reinicie de volta ao início
		if self.frame_index >= len(self.animation_list[self.action]):
			if self.action == 3:
				self.frame_index = len(self.animation_list[self.action]) - 1
			else:
				self.frame_index = 0



	def update_action(self, new_action):
		#verifique se a nova ação é diferente da anterior
		if new_action != self.action:
			self.action = new_action
			#atualize as configurações de animação
			self.frame_index = 0
			self.update_time = pygame.time.get_ticks()



	def check_alive(self):
		if self.health <= 0:
			self.health = 0
			self.speed = 0
			self.alive = False
			self.update_action(3)


	def draw(self):
		tela.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


class World():
	def __init__(self):
		self.obstacle_list = []

	def process_data(self, data):
		self.level_length = len(data[0])
		#iterar através de cada valor no arquivo de dados de nível
		for y, row in enumerate(data):
			for x, tile in enumerate(row):
				if tile >= 0:
					img = img_list[tile]
					img_rect = img.get_rect()
					img_rect.x = x * TILE_SIZE
					img_rect.y = y * TILE_SIZE
					tile_data = (img, img_rect)
					if tile >= 0 and tile <= 8:
						self.obstacle_list.append(tile_data)
					elif tile >= 9 and tile <= 10:
						water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
						water_group.add(water)
					elif tile >= 11 and tile <= 14:
						decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
						decoration_group.add(decoration)
					elif tile == 15:#criar jogador
						player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 1.65, 5, 20, 5)
						health_bar = HealthBar(10, 10, player.health, player.health)
					elif tile == 16:#criar inimigos
						enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 1.65, 2, 20, 0)
						enemy_group.add(enemy)
					elif tile == 17:#criar caixa de munição
						item_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)
					elif tile == 18:#criar caixa de granadas
						item_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)
					elif tile == 19:#criar caixa de saúde
						item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)
					elif tile == 20:#criar saída
						exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
						exit_group.add(exit)

		return player, health_bar


	def draw(self):
		for tile in self.obstacle_list:
			tile[1][0] += tela_scroll
			tela.blit(tile[0], tile[1])


class Decoration(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += tela_scroll


class Water(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += tela_scroll

class Exit(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += tela_scroll


class ItemBox(pygame.sprite.Sprite):
	def __init__(self, item_type, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.item_type = item_type
		self.image = item_boxes[self.item_type]
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))


	def update(self):
		#rolagem
		self.rect.x += tela_scroll
		#verifique se o jogador pegou a caixa
		if pygame.sprite.collide_rect(self, player):
			#verifique que tipo de caixa era
			if self.item_type == 'Health':
				player.health += 25
				if player.health > player.max_health:
					player.health = player.max_health
			elif self.item_type == 'Ammo':
				player.ammo += 15
			elif self.item_type == 'Grenade':
				player.grenades += 3
			#apague a caixa de item
			self.kill()


class HealthBar():
	def __init__(self, x, y, health, max_health):
		self.x = x
		self.y = y
		self.health = health
		self.max_health = max_health

	def draw(self, health):
		#atualizar com nova saúde
		self.health = health
		#calcular proporção de saúde
		ratio = self.health / self.max_health
		pygame.draw.rect(tela, BLACK, (self.x - 2, self.y - 2, 154, 24))
		pygame.draw.rect(tela, RED, (self.x, self.y, 150, 20))
		pygame.draw.rect(tela, GREEN, (self.x, self.y, 150 * ratio, 20))


class Bullet(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.speed = 10
		self.image = bullet_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.direction = direction

	def update(self):
		#mover bala
		self.rect.x += (self.direction * self.speed) + tela_scroll
		#verifique se o marcador saiu da tela
		if self.rect.right < 0 or self.rect.left > tela_largura:
			self.kill()
		#verifique se há colisão com o nível
		for tile in world.obstacle_list:
			if tile[1].colliderect(self.rect):
				self.kill()

		#verificar colisão com personagens
		if pygame.sprite.spritecollide(player, bullet_group, False):
			if player.alive:
				player.health -= 5
				self.kill()
		for enemy in enemy_group:
			if pygame.sprite.spritecollide(enemy, bullet_group, False):
				if enemy.alive:
					enemy.health -= 25
					self.kill()



class Grenade(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.timer = 100
		self.vel_y = -11
		self.speed = 7
		self.image = grenade_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()
		self.direction = direction

	def update(self):
		self.vel_y += GRAVITY
		dx = self.direction * self.speed
		dy = self.vel_y

		#verifique se há colisão com o nível
		for tile in world.obstacle_list:
			#verificar colisão com paredes
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				self.direction *= -1
				dx = self.direction * self.speed
			#verifique se há colisão na direção y
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				self.speed = 0
				#verifique se está abaixo do solo, ou seja, jogado para cima
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top
				#verifique se está acima do solo, ou seja, caindo
				elif self.vel_y >= 0:
					self.vel_y = 0
					dy = tile[1].top - self.rect.bottom	


		#atualizar a posição da granada
		self.rect.x += dx + tela_scroll
		self.rect.y += dy

		#cronômetro de contagem regressiva
		self.timer -= 1
		if self.timer <= 0:
			self.kill()
			grenade_fx.play()
			explosion = Explosion(self.rect.x, self.rect.y, 0.5)
			explosion_group.add(explosion)
			#causar danos a qualquer pessoa que esteja por perto
			if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and \
				abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
				player.health -= 50
			for enemy in enemy_group:
				if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and \
					abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
					enemy.health -= 50



class Explosion(pygame.sprite.Sprite):
	def __init__(self, x, y, scale):
		pygame.sprite.Sprite.__init__(self)
		self.images = []
		for num in range(1, 6):
			img = pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()
			img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
			self.images.append(img)
		self.frame_index = 0
		self.image = self.images[self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.counter = 0


	def update(self):
		#rolagem
		self.rect.x += tela_scroll

		EXPLOSION_SPEED = 4
		#atualizar amimação de explosão
		self.counter += 1

		if self.counter >= EXPLOSION_SPEED:
			self.counter = 0
			self.frame_index += 1
			#se a animação estiver completa, exclua a explosão
			if self.frame_index >= len(self.images):
				self.kill()
			else:
				self.image = self.images[self.frame_index]


class telaFade():
	def __init__(self, direction, colour, speed):
		self.direction = direction
		self.colour = colour
		self.speed = speed
		self.fade_counter = 0


	def fade(self):
		fade_complete = False
		self.fade_counter += self.speed
		if self.direction == 1:#desvanecimento da tela inteira
			pygame.draw.rect(tela, self.colour, (0 - self.fade_counter, 0, tela_largura // 2, tela_altura))
			pygame.draw.rect(tela, self.colour, (tela_largura // 2 + self.fade_counter, 0, tela_largura, tela_altura))
			pygame.draw.rect(tela, self.colour, (0, 0 - self.fade_counter, tela_largura, tela_altura // 2))
			pygame.draw.rect(tela, self.colour, (0, tela_altura // 2 +self.fade_counter, tela_largura, tela_altura))
		if self.direction == 2:#desvanecimento da tela vertical
			pygame.draw.rect(tela, self.colour, (0, 0, tela_largura, 0 + self.fade_counter))
		if self.fade_counter >= tela_largura:
			fade_complete = True

		return fade_complete


#criar esmaecimento de tela
intro_fade = telaFade(1, BLACK, 4)
death_fade = telaFade(2, PINK, 4)


#criar botões
start_button = button.Button(tela_largura // 2 - 130, tela_altura // 2 - 150, start_img, 1)
exit_button = button.Button(tela_largura // 2 - 110, tela_altura // 2 + 50, exit_img, 1)
restart_button = button.Button(tela_largura // 2 - 100, tela_altura // 2 - 50, restart_img, 2)

#criar grupos de sprites
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()



#criar lista de blocos vazia
world_data = []
for row in range(ROWS):
	r = [-1] * COLS
	world_data.append(r)
#carregar dados de nível e criar mundo
with open(f'level{level}_data.csv', newline='') as csvfile:
	reader = csv.reader(csvfile, delimiter=',')
	for x, row in enumerate(reader):
		for y, tile in enumerate(row):
			world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data)



run = True
while run:

	clock.tick(FPS)

	if start_game == False:
		#desenhar menu
		tela.fill(BG)
		#adicionar botões
		if start_button.draw(tela):
			start_game = True
			start_intro = True
		if exit_button.draw(tela):
			run = False
	else:
		#atualizar fundo
		draw_bg()
		#desenhar o mapa do mundo
		world.draw()
		#mostrar a saúde do jogador
		health_bar.draw(player.health)
		#mostrar munição
		draw_text('AMMO: ', font, WHITE, 10, 35)
		for x in range(player.ammo):
			tela.blit(bullet_img, (90 + (x * 10), 40))
		#mostrar granada
		draw_text('GRENADES: ', font, WHITE, 10, 60)
		for x in range(player.grenades):
			tela.blit(grenade_img, (135 + (x * 15), 60))


		player.update()
		player.draw()

		for enemy in enemy_group:
			enemy.ai()
			enemy.update()
			enemy.draw()

		#atualizar e desenhar grupos
		bullet_group.update()
		grenade_group.update()
		explosion_group.update()
		item_box_group.update()
		decoration_group.update()
		water_group.update()
		exit_group.update()
		bullet_group.draw(tela)
		grenade_group.draw(tela)
		explosion_group.draw(tela)
		item_box_group.draw(tela)
		decoration_group.draw(tela)
		water_group.draw(tela)
		exit_group.draw(tela)

		#mostrar introdução
		if start_intro == True:
			if intro_fade.fade():
				start_intro = False
				intro_fade.fade_counter = 0


		#atualizar as ações do jogador
		if player.alive:
			#atirar balas
			if shoot:
				player.shoot()
			#jogar granadas
			elif grenade and grenade_thrown == False and player.grenades > 0:
				grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction),\
				 			player.rect.top, player.direction)
				grenade_group.add(grenade)
				#reduzir granadas
				player.grenades -= 1
				grenade_thrown = True
			if player.in_air:
				player.update_action(2)#2: pular
			elif mover_esquerda or mover_direita:
				player.update_action(1)#1: correr
			else:
				player.update_action(0)
			tela_scroll, level_complete = player.move(mover_esquerda, mover_direita)
			bg_scroll -= tela_scroll
			#verifique se o jogador completou o nível
			if level_complete:
				start_intro = True
				level += 1
				bg_scroll = 0
				world_data = reset_level()
				if level <= MAX_LEVELS:
					#carregar dados de nível e criar mundo
					with open(f'level{level}_data.csv', newline='') as csvfile:
						reader = csv.reader(csvfile, delimiter=',')
						for x, row in enumerate(reader):
							for y, tile in enumerate(row):
								world_data[x][y] = int(tile)
					world = World()
					player, health_bar = world.process_data(world_data)	
		else:
			tela_scroll = 0
			if death_fade.fade():
				if restart_button.draw(tela):
					death_fade.fade_counter = 0
					start_intro = True
					bg_scroll = 0
					world_data = reset_level()
					#carregar dados de nível e criar mundo
					with open(f'level{level}_data.csv', newline='') as csvfile:
						reader = csv.reader(csvfile, delimiter=',')
						for x, row in enumerate(reader):
							for y, tile in enumerate(row):
								world_data[x][y] = int(tile)
					world = World()
					player, health_bar = world.process_data(world_data)


	for event in pygame.event.get():
		#quit game
		if event.type == pygame.QUIT:
			run = False
		#teclado pressionado
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_a:
				mover_esquerda = True
			if event.key == pygame.K_d:
				mover_direita = True
			if event.key == pygame.K_SPACE:
				shoot = True
			if event.key == pygame.K_q:
				grenade = True
			if event.key == pygame.K_w and player.alive:
				player.jump = True
				jump_fx.play()
			if event.key == pygame.K_ESCAPE:
				run = False


		#botão do teclado liberado
		if event.type == pygame.KEYUP:
			if event.key == pygame.K_a:
				mover_esquerda = False
			if event.key == pygame.K_d:
				mover_direita = False
			if event.key == pygame.K_SPACE:
				shoot = False
			if event.key == pygame.K_q:
				grenade = False
				grenade_thrown = False


	pygame.display.update()

pygame.quit()