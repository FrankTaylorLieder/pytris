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
- DONE Consistent timing
- DONE Speed up
- DONE Line removal simple
- Line removal animate
- DONE Game selection (new game, end game, repeat game)
- DONE Next piece
- DONE Drop piece
- DONE BUG Options is not right
- DONE End game detection
- DONE Tidy up display
- DONE Pause
- DONE BUG Game Over not displaying!
- DONE BUG O shape wobbles on rotate
- DONE Show column indicator
- DONE Sort out the pygame installation on M1 mac. GIF support not by default.
- DONE Port to pygame 2.3

@author: fst AT lieder.me.uk
'''

import pygame
import random
import sys

from enum import Enum

pygame.init()


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


def new_model():
    return [x[:] for x in [[False] * mheight] * mwidth]


def dump_model(model):
    for y in range(mheight):
        for x in range(mwidth):
            print('*' if model[x][y] else '.', end='')
        print('')


bs = 10
xoff, yoff = 50, 50
ssize = swidth, sheight = [300, 300]
shadowy = yoff + ((mheight + 1) * bs)

block = pygame.image.load('block.gif')
blockrect = block.get_rect()

'''
Shape definition: dict
  rotate = Bool
  points = [[x,y]]
'''
shapes = [
    {'name': 'I', 'positions': [
        [-2, 0], [-1, 0], [0, 0], [1, 0]], 'rotate': True},
    {'name': 'O', 'positions': [[0, 0], [1, 0],
                                [0, 1], [1, 1]], 'rotate': False},
    {'name': 'T', 'positions': [[0, -1], [0, 0],
                                [0, 1], [-1, 0]], 'rotate': True},
    {'name': 'J', 'positions': [[0, -1], [0, 0],
                                [0, 1], [1, -1]], 'rotate': True},
    {'name': 'L', 'positions': [[0, -1], [0, 0], [0, 1],
                                [-1, -1]], 'rotate': True},
    {'name': 'S', 'positions': [[-1, -1], [0, -1], [0, 0], [1, 0]],
     'rotate': True},
    {'name': 'Z', 'positions': [[0, -1], [0, 0], [-1, 0],
                                [-1, -1]], 'rotate': True}
]

pygame.font.init()
font = pygame.font.SysFont('Comic Sans MS', 30)


class Shape(object):
    '''
    A shape.

    Positions: [ [x, y] ]
    '''

    def __init__(self, shape_defn):
        self.name = shape_defn['name']
        self.positions = shape_defn['positions']
        self.rotate = shape_defn['rotate']

    def can_rotate(self):
        return self.rotate

    def rotate_left(self):
        if not self.rotate:
            return
        np = []
        for i in range(len(self.positions)):
            np.append([self.positions[i][1], -self.positions[i][0]])
        self.positions = np

    def rotate_right(self):
        if not self.rotate:
            return
        np = []
        for i in range(len(self.positions)):
            np.append([-self.positions[i][1], self.positions[i][0]])
        self.positions = np

    def get_points(self, mx, my):
        points = []
        for x, y in self.positions:
            points.append([mx + x, my + y])
        return points

    def get_shadow(self):
        minx = 0
        maxx = 0
        for x, y in self.positions:
            if x < minx:
                minx = x
            if x > maxx:
                maxx = x
        return (minx, maxx)

    def duplicate(self):
        return Shape({'name': self.name, 'positions': self.positions, 'rotate': self.rotate})


def validate_rotated(model, shape, mx, my):
    for x, y in shape.get_points(mx, my):
        if x < 0:
            return False
        if x >= mwidth:
            return False
        if y >= mheight:
            return False
        if model[x][y]:
            return False

    return True


def get_options(model, shape, mx, my):
    # print('XXX get_options %s' % [mx, my, shape.name])
    options = {Directions.LEFT, Directions.RIGHT,
               Directions.DOWN, Directions.RLEFT, Directions.RRIGHT}

    for x, y in shape.get_points(mx, my):
        if x <= 0 or model[x - 1][y]:
            options.discard(Directions.LEFT)
        if x >= (mwidth - 1) or model[x + 1][y]:
            options.discard(Directions.RIGHT)
        if y > (mheight - 2) or model[x][y + 1]:
            options.discard(Directions.DOWN)

    if shape.can_rotate():
        rs = shape.duplicate()
        rs.rotate_right()
        if not validate_rotated(model, rs, mx, my):
            options.discard(Directions.RRIGHT)

        ls = shape.duplicate()
        ls.rotate_left()
        if not validate_rotated(model, ls, mx, my):
            options.discard(Directions.RLEFT)
    else:
        options.discard(Directions.RLEFT)
        options.discard(Directions.RRIGHT)

    # print("XXX options: %s" % options)

    return options


def sediment(model, shape, mx, my):
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
        if remove:
            lines.append(y)

    return lines


def remove_lines(model, removals):
    removals.sort()
    for line in removals:
        for y in range(line - 1, -1, -1):
            for x in range(mwidth):
                model[x][y + 1] = model[x][y]
        for x in range(mwidth):
            model[x][0] = False


def model_to_screen(mx, my, xoff, yoff):
    return [xoff + mx * bs, yoff + my * bs]


def display_board(screen, score, paused, next_shape):
    screen.fill(red)
    lw = 2
    ph = mheight * bs
    pw = mwidth * bs
    pygame.draw.lines(screen, black, True,
                      [(xoff - lw, yoff - lw), (xoff - lw, yoff + ph),
                       (xoff + pw, yoff + ph), (xoff + pw, yoff - lw)], lw)

    text = font.render('Score: %d%s' %
                       (score, ' - PAUSED' if paused else ''), True, black)

    if next_shape:
        display_shape(screen, next_shape, 0, 0, 200, 200)

    screen.blit(text, (10, 10))


def display_shape(screen, shape, mx, my, xoff, yoff):
    for x, y in shape.get_points(mx, my):
        blockrect.x, blockrect.y = model_to_screen(x, y, xoff, yoff)
        screen.blit(block, blockrect)


def display_sediment(screen, model):
    for x in range(mwidth):
        for y in range(mheight):
            if model[x][y]:
                blockrect.x, blockrect.y = model_to_screen(x, y, xoff, yoff)
                screen.blit(block, blockrect)


def display_game_over(screen):
    text = font.render('GAME OVER!', True, black)
    screen.blit(text, (20, 100))


def display_shadow(screen, model, mx, xoff):
    (min, max) = model.get_shadow()
    for x in range(min, max + 1):
        sx, sy = model_to_screen(mx + x, 0, xoff, 0)
        pygame.draw.line(screen, black, (sx, shadowy), (sx + bs, shadowy))


def main():
    screen = pygame.display.set_mode(ssize)

    cycle_time = 50
    level_up = 20
    done = False

    last_time = pygame.time.get_ticks()

    while not done:
        display_board(screen, 0, False, None)
        pygame.display.flip()

        while True:
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    done = True
                    break
                if event.key == pygame.K_s:
                    break

        if done:
            continue

        mx, my = 0, 0
        shape = None
        first = True
        paused = False
        next_shape = Shape(random.choice(shapes))
        cycle = 0
        cycles = 10
        removals = []
        drop = False
        score = 0
        next_level = level_up
        model = new_model()

        while True:
            new_time = pygame.time.get_ticks()
            delay = (last_time + cycle_time) - new_time
            # print('XXX Cycle %d time: %d - %d' % (cycle, new_time - last_time, delay))
            if delay > 0:
                # print('NOTE: cycle OK')
                pygame.time.wait(delay)
            # else:
            #     print('WARNING: cycle took too long: %d' % delay)
            last_time = new_time

            if shape is None:
                shape = next_shape
                next_shape = Shape(random.choice(shapes))
                mx, my = 5, 0
                cycle = 0
                first = True

            options = get_options(model, shape, mx, my)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    print('Key: %s, %s' % (event.key, options))
                    if event.key == pygame.K_p:
                        paused = not paused
                    handled = False
                    if not paused:
                        if event.key == pygame.K_LEFT:
                            print("Left")
                            if Directions.LEFT in options:
                                mx -= 1
                            handled = True
                        if event.key == pygame.K_RIGHT:
                            print("Right")
                            if Directions.RIGHT in options:
                                mx += 1
                            handled = True
                        if event.key == pygame.K_DOWN:
                            print("Down")
                            if Directions.RLEFT in options:
                                shape.rotate_left()
                            handled = True
                        if event.key == pygame.K_UP:
                            print("Up")
                            if Directions.RRIGHT in options:
                                shape.rotate_right()
                            handled = True
                        if event.key == pygame.K_SPACE:
                            print("Space")
                            if Directions.DOWN in options:
                                drop = True
                            handled = True

                        if not handled:
                            print('WARNING: Key not handled: %s' % event.key)

                options = get_options(model, shape, mx, my)

            if not paused:
                if cycle > cycles or drop:
                    if Directions.DOWN not in options:
                        sediment(model, shape, mx, my)
                        shape = None
                        drop = False

                        removals = lines_to_remove(model)
                        if removals:
                            remove_lines(model, removals)
                            points = 2 ** (len(removals) - 1)
                            score += points
                            print("Score: %d lines, %d points, %d score" %
                                  (len(removals), points, score))
                            if cycles > 1 and score >= next_level:
                                print('Next level!')
                                next_level += level_up
                                cycles -= 1

                        continue
                    my += 1
                    cycle = 0

            display_board(screen, score, paused, next_shape)
            display_shape(screen, shape, mx, my, xoff, yoff)
            display_sediment(screen, model)
            display_shadow(screen, shape, mx, xoff)

            pygame.display.flip()

            if first:
                if not options:
                    break
                first = False

            cycle += 1

        print('Game over!')
        display_board(screen, score, paused, None)
        display_shape(screen, shape, mx, my, xoff, yoff)
        display_sediment(screen, model)
        display_game_over(screen)
        pygame.display.flip()

        while True:
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    done = True
                    break
                if event.key == pygame.K_s:
                    break

    print('Goodbye...')


if __name__ == '__main__':
    main()
