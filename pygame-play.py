'''
Created on 23 Sep 2018

Create screen
Animate block dropping
Take user input

@author: fst
'''

import pygame


def main():
    kup, kdown, kright, kleft = 273, 274, 275, 276
    speed = [2, 2]
    red = 255, 0, 0
    size = swidth, sheight = [640,480]
    screen = pygame.display.set_mode(size)
    
    block = pygame.image.load('block.gif')
    blockrect = block.get_rect()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            if event.type == pygame.KEYDOWN:
                print('Key: %s' % event.key)
                if event.key == kup:
                    speed = [0, -2]
                if event.key == kdown:
                    speed = [0, 2]
                if event.key == kleft:
                    speed = [-2, 0]
                if event.key == kright:
                    speed = [2, 0]
            
        blockrect = blockrect.move(speed)
        if blockrect.left < 0 or blockrect.right > swidth:
            speed[0] = -speed[0]
            
        if blockrect.top < 0 or blockrect.bottom > sheight:
            speed[1] = -speed[1]
            
        screen.fill(red)
        screen.blit(block, blockrect)
        pygame.display.flip()
    
if __name__ == '__main__':
    main()