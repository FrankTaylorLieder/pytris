'''
pytris - simple Tetris game in PyGame

TODO
- DONE Model
- DONE Display board
- DONE Handle animation
- DONE Show shapes
- DONE Handle key presses
- DONE Sediment blocks
- DONE Collision detection
- DONE Rotation
- DONE Scoring
- Consistent timing
- Speed up
- DONE Line removal simple
- Line removal animate
- Game selection (new game, end game, repeat game)
- High scores
- Next piece
- DONE Drop piece
- DONE BUG Options is not right
- DONE End game detection
- Tidy up display

@author: fst AT lieder.me.uk
'''

import pygame
import random   
import sys

from enum import Enum


class Directions(Enum):
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    RLEFT = 4
    RRIGHT = 5

red = 255, 0, 0
black = 0, 0, 0

mwidth, mheight = 10, 20

# 2D array: list of columns
model = [x[:] for x in [[False] * mheight] * mwidth]

print('XXX model %d, %d, %s' % (len(model), len(model[0]), model))


def dump_model(model):
    for y in range(mheight):
        for x in range(mwidth):
            print('*' if model[x][y] else '.', end='')
        print('')

bs = 10
xoff, yoff = 50, 50
ssize = swidth, sheight = [640, 480]

block = pygame.image.load('block.gif')
blockrect = block.get_rect()

shapes = [
        [[-2, 0], [-1, 0], [0, 0], [1, 0]],  # I
        [[0, 0], [1, 0], [0, 1], [1, 1]],    # O
        [[0, -1], [0, 0], [0, 1], [-1, 0]],  # T
        [[0, -1], [0, 0], [0, 1], [1, -1]],  # J
        [[0, -1], [0, 0], [0, 1], [-1, -1]], # L
        [[-1, -1], [0, -1], [0, 0], [1, 0]], # S
        [[0, -1], [0, 0], [-1, 0], [-1, -1]] # Z
    ]

pygame.font.init()
font = pygame.font.SysFont('Comic Sans MS', 30)


class Shape(object):
    '''
    A shape.
    
    Positions: [ [x, y] ]
    '''
    
    def __init__(self, positions):
        self.positions = positions

    def rotate_left(self):
        np = []
        for i in range(len(self.positions)):
            np.append([self.positions[i][1], -self.positions[i][0]])
        self.positions = np
        
    def rotate_right(self):
        np = []
        for i in range(len(self.positions)):
            np.append([-self.positions[i][1], self.positions[i][0]])
        self.positions = np
        
    def get_points(self, mx, my):
        points = []
        for x, y in self.positions:
            points.append([mx + x, my + y])
        return points
    
def validate_rotated(model, shape, mx, my):
    for x, y in shape.get_points(mx, my):
        if x < 0: return False
        if x >= mwidth: return False
        if y >= mheight: return False
        if model[x][y]: return False
    
    return True

def get_options(model, shape, mx, my):
    # print('XXX get_options %s' % [mx, my, shape])
    options = { Directions.LEFT, Directions.RIGHT, Directions.DOWN, Directions.RLEFT, Directions.RRIGHT }
            
    for x, y in shape.get_points(mx, my):
        if x <= 0 or model[x-1][y]: options.discard(Directions.LEFT)
        if x >= (mwidth - 1) or model[x+1][y]: options.discard(Directions.RIGHT)
        if y > (mheight - 2) or model[x][y+1]: options.discard(Directions.DOWN)
        
    rs = Shape(shape.positions)
    rs.rotate_right()
    if not validate_rotated(model, rs, mx, my): options.discard(Directions.RRIGHT)
    
    ls = Shape(shape.positions)
    ls.rotate_left()
    if not validate_rotated(model, ls, mx, my): options.discard(Directions.RLEFT)
    
    return options


def sediment(model, shape, mx, my):
    print('XXX Sediment %s' % [mx, my])
    for x, y in shape.get_points(mx, my):
        if x >= 0 and x < mwidth and y >= 0 and y < mheight:
            model[x][y] = True

def lines_to_remove(model):
    lines = []
    for y in range(mheight):
        remove = True
        for x in range(mwidth):
            if not model[x][y]:
                remove = False
                break
        if remove: lines.append(y)
    
    print('XXX Removing: %s' % lines)
    return lines

def remove_lines(model, removals):
    print('XXX Removing lines')
    removals.sort()
    for l in removals:
        for y in range(l-1, -1, -1):
            for x in range(mwidth):
                model[x][y+1] = model[x][y]
        for x in range(mwidth):
            model[x][0] = False

def model_to_screen(mx, my):
    return [xoff + mx * bs, yoff + my * bs]


def display_board(screen, score):
    screen.fill(red)
    lw = 2
    ph = mheight * bs
    pw = mwidth * bs
    pygame.draw.lines(screen, black, True, [(xoff - lw, yoff - lw), (xoff - lw, yoff + ph),
                                            (xoff + pw, yoff + ph), (xoff + pw, yoff - lw)], lw)
    
    text = font.render('Score: %d' % score, False, black)
    screen.blit(text, (10, 10))

    
def display_shape(screen, shape, mx, my):
    for x, y in shape.get_points(mx, my):
        blockrect.x, blockrect.y = model_to_screen(x, y)
        screen.blit(block, blockrect)

        
def display_sediment(screen, model):
    for x in range(mwidth):
        for y in range(mheight):
            if model[x][y]:
                blockrect.x, blockrect.y = model_to_screen(x, y)
                screen.blit(block, blockrect)
                
def display_game_over(screen):
    text = font.render('GAME OVER!', False, black)
    screen.blit(text, (100, 100))

def main():    
    kup, kdown, kright, kleft, kspace = 273, 274, 275, 276, 32
    screen = pygame.display.set_mode(ssize)
    
    mx, my = 0, 0
    shape = None
    
    cycle = 0
    cycles = 20
    removals = []
    drop = False
    score = 0
    first = True
    
    while True:
        if shape is None:
            shape = Shape(random.choice(shapes))
            mx, my = 5, 0
            cycle = 0
            first = True
            
        options = get_options(model, shape, mx, my)
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            if event.type == pygame.KEYDOWN:
                print('Key: %s, %s' % (event.key, options))
                if event.key == kleft and Directions.LEFT in options:
                    mx -= 1
                if event.key == kright and Directions.RIGHT in options:
                    mx += 1
                if event.key == kdown and Directions.RLEFT in options:
                    shape.rotate_left()
                if event.key == kup and Directions.RRIGHT in options:
                    shape.rotate_right()
                if event.key == kspace and Directions.DOWN in options:
                    drop = True
                    
            options = get_options(model, shape, mx, my)
    
        if cycle > cycles or drop:
            if Directions.DOWN not in options:
                sediment(model, shape, mx, my)
                shape = None
                drop = False
                
                # TODO Properly animate and score this.
                removals = lines_to_remove(model)
                if removals:
                    remove_lines(model, removals)
                    score += 2 ** (len(removals) - 1)
                    
                continue
            my += 1
            cycle = 0

        display_board(screen, score)
        display_shape(screen, shape, mx, my)
        display_sediment(screen, model)
        
        if first:
            if not options:
                break;
            first = False
          
        pygame.display.flip()
        
        cycle += 1
        
    print('Game over!')
    display_board(screen, score)
    display_shape(screen, shape, mx, my)
    display_sediment(screen, model)
    display_game_over(screen)
    pygame.display.flip()

    input()
        
if __name__ == '__main__':
    main()
