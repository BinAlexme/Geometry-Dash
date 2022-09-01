#  filename: main.py
#  author: Yonah Aviv
#  date created: 2020-11-10 6:21 p.m.
#  last modified: 2020-11-18
#  Pydash: Similar to Geometry Dash, a rhythm based platform game, but programmed using the pygame library in Python


"""CONTROLS
Anywhere -> ESC: exit
Main menu -> 1: go to previous level. 2: go to next level. SPACE: start game.
Game -> SPACE/UP: jump, and activate orb
    orb: jump in midair when activated
If you die or beat the level, press SPACE to restart or go to the next level

"""

import csv
import os
import random
import neat
import math
import sys

# import the pygame module
import pygame

# will make it easier to use pygame functions
from pygame.math import Vector2
from pygame.draw import rect

# initializes the pygame module
pygame.init()

# creates a screen variable of size 800 x 600
width = 800
height = 600
screen = pygame.display.set_mode([800, 600])

# controls the main game while loop
done = False

# controls whether or not to start the game from the main menu
start = True

# sets the frame rate of the program
clock = pygame.time.Clock()

# N of generation
generation = 0

"""
CONSTANTS
"""
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

"""lambda functions are anonymous functions that you can assign to a variable.
e.g.
1. x = lambda x: x + 2  # takes a parameter x and adds 2 to it
2. print(x(4))
>>6
"""
color = lambda: tuple([random.randint(0, 255) for i in range(3)])  # lambda function for random color, not a constant.
GRAVITY = Vector2(0, 0.96)  # Vector2 is a pygame

"""
Main player class
"""


class Player(pygame.sprite.Sprite):
    """Class for player. Holds update method, win and die variables, collisions and more."""
    win: bool
    died: bool

    def __init__(self, name, image, platforms, pos, *groups):
        """
        :param image: block face avatar
        :param platforms: obstacles such as coins, blocks, spikes, and orbs
        :param pos: starting position
        :param groups: takes any number of sprite groups.
        """
        super().__init__(*groups)
        self.onGround = False  # player on ground?
        self.platforms = platforms  # obstacles but create a class variable for it
        self.died = False  # player died?
        self.win = False  # player beat level?

        self.name = name
        self.image = pygame.transform.smoothscale(image, (32, 32))
        self.rect = self.image.get_rect(center=pos)  # get rect gets a Rect object from the image
        self.jump_amount = 12  # jump strength
        self.particles = []  # player trail
        self.isjump = False  # is the player jumping?
        self.vel = Vector2(0, 0)  # velocity starts at zero
        self.angle = 0
        self.jumps_count = 0

    def draw_particle_trail(self, x, y, color=(255, 255, 255)):
        """draws a trail of particle-rects in a line at random positions behind the player"""

        self.particles.append(
            [[x - 5, y - 8], [random.randint(0, 25) / 10 - 1, random.choice([0, 0])],
             random.randint(5, 8)])

        for particle in self.particles:
            particle[0][0] += particle[1][0]
            particle[0][1] += particle[1][1]
            particle[2] -= 0.5
            particle[1][0] -= 0.4
            rect(alpha_surf, color,
                 ([int(particle[0][0]), int(particle[0][1])], [int(particle[2]) for i in range(2)]))
            if particle[2] <= 0:
                self.particles.remove(particle)

    def collide(self, yvel, platforms):
        global coins

        for p in platforms:
            if pygame.sprite.collide_rect(self, p):
                """pygame sprite builtin collision method,
                sees if player is colliding with any obstacles"""
                if isinstance(p, Spike):
                    self.died = True  # die on spike

                if isinstance(p, Platform) or isinstance(p, HalfBlock):  # these are the blocks (may be confusing due to self.platforms)

                    if yvel > 0:
                        """if player is going down(yvel is +)"""
                        self.rect.bottom = p.rect.top  # dont let the player go through the ground
                        self.vel.y = 0  # rest y velocity because player is on ground

                        # set self.onGround to true because player collided with the ground
                        self.onGround = True

                        # reset jump
                        self.isjump = False
                    elif yvel < 0:
                        """if yvel is (-),player collided while jumping"""
                        self.rect.top = p.rect.bottom  # player top is set the bottom of block like it hits it head
                    else:
                        """otherwise, if player collides with a block, he/she dies."""
                        self.vel.x = 0
                        self.rect.right = p.rect.left  # dont let player go through walls
                        self.died = True

    def jump(self):
        self.vel.y = -self.jump_amount  # players vertical velocity is negative so ^

    def doJump(self):
        self.isjump = True
        self.jumps_count += 1

    def update(self):
        """update player"""
        if self.isjump:
            if self.onGround:
                """if player wants to jump and player is on the ground: only then is jump allowed"""
                self.jump()

        if not self.onGround:  # only accelerate with gravity if in the air
            self.vel += GRAVITY  # Gravity falls

            # max falling speed
            if self.vel.y > 100: self.vel.y = 100

        # do x-axis collisions
        self.collide(0, self.platforms)

        # increment in y direction
        self.rect.top += self.vel.y

        # assuming player in the air, and if not it will be set to inversed after collide
        self.onGround = False

        # do y-axis collisions
        self.collide(self.vel.y, self.platforms)

        # check if we won or if player won
    # eval_outcome(self.win, self.died)


"""
Obstacle classes
"""


# Parent class
class Draw(pygame.sprite.Sprite):
    """parent class to all obstacle classes; Sprite class"""

    def __init__(self, image, pos, *groups):
        super().__init__(*groups)
        self.image = image
        self.rect = self.image.get_rect(topleft=(pos[0], pos[1]))
        self.pos = pos


#  ====================================================================================================================#
#  classes of all obstacles. this may seem repetitive but it is useful(to my knowledge)
#  ====================================================================================================================#
# children
class Platform(Draw):
    """block"""

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


class Spike(Draw):
    """spike"""

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


class HalfBlock(Draw):
    """spike"""

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


"""
Functions
"""


def calc_dist(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]

    return math.sqrt(dx ** 2 + dy ** 2)


spikes = []
spike_groups = []

def init_level(map):
    """this is similar to 2d lists. it goes through a list of lists, and creates instances of certain obstacles
    depending on the item in the list"""
    x = 0
    y = 0

    for row in map:
        for col in row:

            if col == "0":
                Platform(block, (x, y), elements)

            if col == "1":
                HalfBlock(half_block, (x, y), elements)

            if col == "2":
                s = Spike(spike, [x, y, 1], elements)

                if spike_groups:
                    last_spike = spikes[-1]
                    # print(f"{last_spike.pos[0]} - {x}")
                    if x - last_spike.pos[0] == 32:
                        # joined (count as one)
                        spike_groups[-1].pos[2] += 1
                        pass
                    else:
                        spike_groups.append(s)
                else:
                    spike_groups.append(s)

                spikes.append(s)

            x += 32
        y += 32
        x = 0

    spike_groups.sort(key=lambda x: x.pos[0])
    #for sp in spike_groups:
    #    print(sp.pos)
    #sys.exit()


def get_closest_spike(player_x):
    for s in spike_groups:
        # print(f"{s.pos[0]} > {player_x}")
        if s.pos[0] > player_x:
            return s.pos

    return None


def blitRotate(surf, image, pos, originpos: tuple, angle: float):
    """
    rotate the player
    :param surf: Surface
    :param image: image to rotate
    :param pos: position of image
    :param originpos: x, y of the origin to rotate about
    :param angle: angle to rotate
    """
    # calcaulate the axis aligned bounding box of the rotated image
    w, h = image.get_size()
    box = [Vector2(p) for p in [(0, 0), (w, 0), (w, -h), (0, -h)]]
    box_rotate = [p.rotate(angle) for p in box]

    # make sure the player does not overlap, uses a few lambda functions(new things that we did not learn about number1)
    min_box = (min(box_rotate, key=lambda p: p[0])[0], min(box_rotate, key=lambda p: p[1])[1])
    max_box = (max(box_rotate, key=lambda p: p[0])[0], max(box_rotate, key=lambda p: p[1])[1])
    # calculate the translation of the pivot
    pivot = Vector2(originpos[0], -originpos[1])
    pivot_rotate = pivot.rotate(angle)
    pivot_move = pivot_rotate - pivot

    # calculate the upper left origin of the rotated image
    origin = (pos[0] - originpos[0] + min_box[0] - pivot_move[0], pos[1] - originpos[1] - max_box[1] + pivot_move[1])

    # get a rotated image
    rotated_image = pygame.transform.rotozoom(image, angle, 1)

    # rotate and blit the image
    surf.blit(rotated_image, origin)


def block_map(level_num):
    """
    :type level_num: rect(screen, BLACK, (0, 0, 32, 32))
    open a csv file that contains the right level map
    """
    lvl = []
    with open(level_num, newline='') as csvfile:
        trash = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in trash:
            lvl.append(row)
    return lvl


def reset():
    """resets the sprite groups, music, etc. for death and new level"""
    global avatars, p_c, tomato_in, spikes, spike_groups, TravelDist, elements, player_sprite, level

    if level == 1:
        pygame.mixer.music.load(os.path.join("music", "castle-town.mp3"))
    # player_sprite = pygame.sprite.Group()
    elements = pygame.sprite.Group()
    TravelDist = 150
    spikes = []
    spike_groups = []
    tomato_in = False

    avatars = ["Bloody", "Ghost", "Haze", "Ice", "Lime", "Orange", "Samurai", "Sub-Zero", "Sunny", "Vampire", "Tomato"]
    p_c = random.choice(avatars)
    avatars.remove(p_c)

    init_level(
        block_map(
            level_num=levels[level]))


def move_map():
    """moves obstacles along the screen"""

    global TravelDist
    TravelDist += CameraX

    for sprite in elements:
        sprite.rect.x -= CameraX


def draw_stats(surf, money=0):
    """
    draws progress bar for level, number of attempts, displays coins collected, and progressively changes progress bar
    colors
    """
    global fill
    progress_colors = [pygame.Color("red"), pygame.Color("orange"), pygame.Color("yellow"), pygame.Color("lightgreen"),
                       pygame.Color("green")]

    tries = font.render(f" Attempt {str(attempts)}", True, WHITE)
    BAR_LENGTH = 600
    BAR_HEIGHT = 10

    fill += 0.5
    outline_rect = pygame.Rect(0, 0, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pygame.Rect(0, 0, fill, BAR_HEIGHT)
    col = progress_colors[int(fill / 100)]
    rect(surf, col, fill_rect, 0, 4)
    rect(surf, WHITE, outline_rect, 3, 4)
    screen.blit(tries, (BAR_LENGTH, 0))


def resize(img, size=(32, 32)):
    """resize images
    :param img: image to resize
    :type img: im not sure, probably an object
    :param size: default is 32 because that is the tile size
    :type size: tuple
    :return: resized img

    :rtype:object?
    """
    resized = pygame.transform.smoothscale(img, size)
    return resized


"""
Global variables
"""
font = pygame.font.SysFont("lucidaconsole", 20)
dname_font = pygame.font.SysFont("Roboto Condensed", 30)
heading_font = pygame.font.SysFont("Roboto Condensed", 70)

# square block face is main character the icon of the window is the block face
avatar = pygame.image.load(os.path.join("images", "avatar.png"))  # load the main character
pygame.display.set_icon(avatar)
#  this surface has an alpha value with the colors, so the player trail will fade away using opacity
alpha_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

# sprite groups
# player_sprite = pygame.sprite.Group()
elements = pygame.sprite.Group()

# images
spike = pygame.image.load(os.path.join("images", "spike-up.png"))
spike = resize(spike)

block = pygame.image.load(os.path.join("images", "block.png"))
block = pygame.transform.smoothscale(block, (32, 32))

half_block = pygame.image.load(os.path.join("images", "half-block.png"))
half_block = pygame.transform.smoothscale(half_block, (32, 32))

#  ints
fill = 0
num = 0
CameraX = 0
TravelDist = 150
attempts = 0
coins = 0
angle = 0
level = 0

# list
particles = []
orbs = []
win_cubes = []

# initialize level with
levels = ["GD1.csv"]
level_list = block_map(levels[level])
level_width = (len(level_list[0]) * 32)
level_height = len(level_list) * 32
init_level(level_list)

# set window title suitable for game
pygame.display.set_caption('Pydash: Geometry Dash in Python')

# initialize the font variable to draw text later
text = font.render('image', False, (255, 255, 0))

# bg image
bg = pygame.image.load(os.path.join("images", "bg.png"))

# avatars
avatars = ["Bloody", "Ghost", "Haze", "Ice", "Lime", "Orange", "Samurai", "Sub-Zero", "Sunny", "Vampire", "Tomato"]
p_c = random.choice(avatars)
avatars.remove(p_c)
tomato_in = False
players = []


def run_game(genomes, config):
    global tomato_in, CameraX, done, players, generation

    generation += 1
    players = []
    nets = []

    # init genomes
    for i, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0  # every genome is not successfull at the start

        if not tomato_in:
            tomato_in = True
            rand_av = p_c
            avatar = pygame.image.load(os.path.join("images", f"avatars/{rand_av}.png"))
        else:
            rand_av = random.choice(avatars)
            avatar = pygame.image.load(os.path.join("images", f"avatars/{rand_av}.png"))
        players.append(Player(rand_av, avatar, elements, (150, 150)))

    # init
    while not done:
        screen.blit(bg, (0, 0))  # Clear the screen(with the bg)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # quit if there is no players left
        if len(players) == 0:
            reset()
            break

        # controls
        for i, player in enumerate(players):
            closest_spike = get_closest_spike(TravelDist)
            output = nets[i].activate((
                closest_spike[0] - TravelDist,  # Расстояние до ближайшего шипа по X
                abs(closest_spike[1] - player.rect.y),  # Разница в высоте по Y между игроком и ближайшим шипом
                closest_spike[2] * 32,  # Ширина ближайшего шипа
            ))

            # pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(player.rect.x, player.rect.y, 20, 20))
            # pygame.draw.rect(screen, (255,0,0), pygame.Rect(closest_spike[0] - TravelDist + 150, closest_spike[1], 20, 20))

            genomes[i][1].fitness = int((TravelDist - 150) / 100)

            if output[0] < 0.5 and player.isjump == False:
                player.doJump()
                genomes[i][1].fitness -= 5

        for j, player in enumerate(players):
            players[j].vel.x = 6

            # Reduce the alpha of all pixels on this surface each frame.
            # Control the fade2 speed with the alpha value.
            # alpha_surf.fill((255, 255, 255, 1), special_flags=pygame.BLEND_RGBA_MULT)

            player.update()
            CameraX = player.vel.x  # for moving obstacles

            # player.draw_particle_trail(player.rect.left - 1, player.rect.bottom + 2,
            #                           WHITE)
            #screen.blit(alpha_surf, (0, 0))  # Blit the alpha_surf onto the screen.

            if player.isjump:
                """rotate the player by an angle and blit it if player is jumping"""
                players[j].angle -= 8.1712  # this may be the angle needed to do a 360 deg turn in the length covered in one jump by player
                blitRotate(screen, player.image, player.rect.center, (16, 16), player.angle)
            else:
                """if player.isjump is false, then just blit it normally(by using Group().draw() for sprites"""
                # player_sprite.draw(screen)  # draw player sprite group
                screen.blit(player.image, player.rect)

            if player.died:
                genomes[j][1].fitness -= 50
                players.pop(j)

                genomes.pop(j)
                nets.pop(j)

        move_map()  # apply CameraX to all elements
        elements.draw(screen)  # draw all other obstacles

        # display players names
        for i, player in enumerate(players):
            if(player.died):
                continue

            dname_label = dname_font.render(player.name, True, (170, 238, 187))
            dname_label_rect = dname_label.get_rect()
            dname_label_rect.center = (player.rect.x + 20, player.rect.y - 20)
            screen.blit(dname_label, dname_label_rect)

        # display generation
        label = heading_font.render("Поколение: " + str(generation), True, (255, 255, 255))
        label_rect = label.get_rect()
        label_rect.center = (width / 2, 150)
        screen.blit(label, label_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    """User friendly exit"""
                    done = True

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    # setup config
    config_path = "./config-feedforward.txt"
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, config_path)

    # init NEAT
    p = neat.Population(config)

    # run NEAT
    p.run(run_game, 1000)

pygame.quit()
