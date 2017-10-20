from pico2d import *
from functions import *

import framework

name = "game_state"

# Global : Variables 2
instance_last:object= None                          # 마지막 개체
instance_list:list = []                             # 개체는 순서가 있다.
"""
        <List> instance_list_spec:

            목적: 객체를 종류 별로 담기 위한 리스트
            용법:
                instance_list_spec[객체 이름] = []
                instance_list_spec[객체 이름].append(객체 ID)

            비고: 객체 이름 외에도 "Solid", "Particle" 등의 구별자 사용.
"""
instance_list_spec:dict = {}                         # 객체 종류 별 목록
instance_draw_list:list = []                         # 개체 그리기 목록
instance_update:bool = false                         # 개체 갱신 여부
#event_queue = []                                    # 이벤트 목록

ID_SOLID:str= "Solid"
ID_PARTICLE:str = "Particle"
ID_DOODAD:str = "Doodad"
ID_DMG_PLAYER:str = "HurtPlayer"
ID_DMG_ENEMY:str = "HurtEnemy"
instance_list_spec[ID_SOLID] = []
instance_list_spec[ID_PARTICLE] = []
instance_list_spec[ID_DOODAD] = []
instance_list_spec[ID_DMG_PLAYER] = []
instance_list_spec[ID_DMG_ENEMY] = []

# Object : Gravitons
class __Graviton(object):
    name = "None"
    identify = ""
    next = None

    # Properties of sprite
    sprite_index = None
    image_index = float(0)
    image_speed = float(0)
    visible = true
    depth = 0

    # for optimization
    step_enable = true

    x, y = 0, 0
    xVel, yVel = 0, 0
    xFric, yFric = 0.4, 1
    gravity_default = 0.4
    gravity = 0
    onAir = false

    def __init__(self, ndepth = int(0), nx = int(0), ny = int(0)):
        self.depth = ndepth
        self.x, self.y = nx, ny

        global instance_list_spec
        if self.identify != "":
            instance_list_spec[self.identify].append(self)

    def __str__(self):
        return self.name

    def __del__(self):
        global instance_last, instance_list, instance_list_spec, instance_draw_list, instance_update

    # Below methods are common-functions for all object that inherites graviton.
    def collide(self):
        self.xVel = 0

    def thud(self):
        self.yVel = 0
        self.onAir = false

    def draw_self(self): # Simply draws its sprite on its position.
        if (self.sprite_index != None):
            draw_sprite(self.sprite_index, self.image_index, self.x, self.y)

    def event_step(self): # The basic machanism of objects.
        if self.xVel != 0:
            xc = self.x + self.xVel + sign(self.xVel)
            if place_free(xc, self.y):
                self.x += self.xVel
            else:
                self.collide()

        if self.yVel > 0:   # Going up higher
            yc = self.y + self.yVel + 1
        else:               # Going down
            yc = self.y + self.yVel - 1

        if place_free(self.x, yc):
            self.y += self.yVel                     # let it moves first.
            self.gravity = self.gravity_default
            self.yVel -= self.gravity
            self.onAir = true
        else:
            self.gravity = 0
            if self.xVel != 0:                      # horizontal friction works only when it is on the ground
                self.xVel *= self.xFric
            self.thud()

    def event_draw(self): # This will be working for drawing.
        self.draw_self()

# Object : Solid Objects
class __Solid(__Graviton):
    # reset some inherited variables
    name = "Solid"
    identify = ID_SOLID
    step_enable = false
    gravity_default = 0
    xFric, yFric = 0, 0

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)

# Object : Functions
def instance_create(Ty, depth = int(0), x = int(0), y = int(0)):
    global Game, instance_update, instance_last

    temp = Ty.__new__(Ty)
    temp.depth = depth
    temp.x = x
    temp.y = y

    if instance_last != None:
        instance_last.next = temp
    instance_last = temp
    instance_list.append(instance_last)
    instance_update = true

    return instance_last

def place_free(dx, dy):
    global instance_list_spec
    clist = instance_list_spec["Solid"]  # 고체 개체 목록 불러오기
    length = len(clist)
    if length > 0:
        for inst in clist:
            tempspr: Sprite = inst.sprite_index
            if point_in_rectangle(dx, dy, inst.x - tempspr.width / 2, inst.y - tempspr.height / 2,
                                      inst.x + tempspr.width / 2, inst.y + tempspr.height / 2):
                return true
    else:
        return false

class oBrick(__Solid):
    name = "Brick of Mine"
    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_index = sprite_get("CastleBrick")
        self.image_index = irandom_range(0, 3);

def enter():
    global hwnd
    hwnd = open_canvas(screen_width, screen_height, true)
    SDL_SetWindowTitle(hwnd, ctypes.c_char_p("Vampire Exodus".encode("UTF-8")))
    SDL_SetWindowSize(hwnd, screen_width * screen_scale, screen_height * screen_scale)

    # x, y = ctypes.c_int(), ctypes.c_int()
    # SDL_GetWindowPosition(self.hwnd, ctypes.byref(x), ctypes.byref(y))
    # x, y = x.value, y.value
    # vscl = screen_scale * 2
    # dx, dy = int(x - scr_defw * screen_scale / vscl), int(y - scr_defh * screen_scale / vscl)

    # SDL_SetWindowPosition(self.hwnd, c_int(dx), c_int(dy))
    # SDL_SetWindowFullscreen(self.hwnd, ctypes.c_uint32(1))
    hide_cursor()
    hide_lattice()

    # TODO: Definite more objects.
    # Definitions of Special Objects ( Need a canvas )
    sprite_load("..\\res\\img\\theme\\brick_castle.png", "CastleBrick", 4)
    #sprite_load("..\\res\\img\\theme\\brick_mine_0.png", "MineBrick1")
    #sprite_load("..\\res\\img\\theme\\brick_mine_1.png", "MineBrick2")
    #sprite_load("..\\res\\img\\theme\\brick_mine_bot.png", "MineBrickB")

    testo = instance_create(oBrick, 0, 100, 100)
    instance_create(oBrick, 0, 100, 200)
    instance_create(oBrick, 0, 100, 300)
    instance_create(oBrick, 0, 200, 100)
    instance_create(oBrick, 0, 300, 100)
    instance_create(oBrick, 0, 400, 400)
    pass

def exit():
    close_canvas()
    pass

def update():
    if len(instance_list) > 0:
        for inst in instance_list:
            if inst.step_enable:
                inst.event_step()
    delay(0.01)
    pass

def draw():
    clear_canvas()
    instance_draw_update()
    for inst in instance_draw_list:
        if inst.visible:
            inst.event_draw()
    update_canvas()
    pass

def instance_draw_update():
    global instance_draw_list, instance_update
    if instance_update:
        del instance_draw_list
        instance_update = false
        instance_draw_list = []
        for inst in instance_list:
            instance_draw_list.append(inst)

def handle_events():
    global event_queue
    event_queue = get_events()
    for event in event_queue:
        if (event.type == SDL_QUIT):
            framework.quit()
        elif (event.type, event.key) == (SDL_KEYDOWN, SDLK_ESCAPE):
            framework.quit()

def pause():
    pass

def resume():
    pass