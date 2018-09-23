'''
pytris - simple Tetris game in PyGame

TODO
- DONE Model
- DONE Display board
- DONE Handle animation
- Show blocks
- DONE Handle key presses
- DONE Sediment blocks
- Collision detection
- Rotation
- Scoring

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

        
dump_model(model)

bs = 10
xoff, yoff = 50, 50
ssize = swidth, sheight = [640, 480]


def get_options(model, mx, my):
    # print('XXX get_options %s' % [mx, my])
    results = []
    if mx > 0 and not model[mx - 1][my]: results.append(Directions.LEFT)
    if mx < mwidth - 1 and not model[mx + 1][my]: results.append(Directions.RIGHT)
    if my < mheight - 1 and not model[mx][my + 1]: results.append(Directions.DOWN)
    
    return results


def sediment(model, mx, my):
    print('XXX Sediment %s' % [mx, my])
    model[mx][my] = True


def model_to_screen(mx, my):
    return [xoff + mx * bs, yoff + my * bs]


def display_board(screen):
    screen.fill(red)
    lw = 2
    ph = mheight * bs
    pw = mwidth * bs
    pygame.draw.lines(screen, black, True, [(xoff - lw, yoff - lw), (xoff - lw, yoff + ph),
                                            (xoff + pw, yoff + ph), (xoff + pw, yoff - lw)], lw)


def main():
    kup, kdown, kright, kleft = 273, 274, 275, 276
    screen = pygame.display.set_mode(ssize)

    block = pygame.image.load('block.gif')
    blockrect = block.get_rect()
    
    mx, my = 0, 0
    new_block = True
    
    cycle = 0
    cycles = 10
    
    while True:
        if new_block:
            mx, my = random.randrange(mwidth), 0
            new_block = False
            cycle = 0
            
        options = get_options(model, mx, my)
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            if event.type == pygame.KEYDOWN:
                print('Key: %s, %s' % (event.key, options))
                if event.key == kleft and Directions.LEFT in options:
                    mx -= 1
                if event.key == kright and Directions.RIGHT in options:
                    mx += 1
                    
            options = get_options(model, mx, my)
    
        if cycle > cycles:
            if Directions.DOWN not in options:
                sediment(model, mx, my)
                new_block = True
                continue
            my += 1
            cycle = 0
        
        blockrect.x, blockrect.y = model_to_screen(mx, my)
        
        display_board(screen)
        
        screen.blit(block, blockrect)

        for x in range(mwidth):
            for y in range(mheight):
                if model[x][y]:
                    blockrect.x, blockrect.y = model_to_screen(x, y)
                    screen.blit(block, blockrect)
          
        pygame.display.flip()
        
        cycle += 1

        
if __name__ == '__main__':
    main()
