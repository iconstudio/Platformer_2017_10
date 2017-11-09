from module.pico2d import *
from module.functions import *
from module.constants import *

import math
from module.framework import io
from module.framework import Camera

from module.sprite import *
from module.terrain import *

import math
import sys

__all__ = [
    "instance_last", "instance_list_spec", "instance_draw_list", "instance_update", "instance_list",
    "container_player", "instance_create",
    "GObject", "Solid", "oBrick", "oPlayer", "oSoldier",
    "ID_SOLID", "ID_DMG_PLAYER", "ID_DMG_ENEMY", "ID_ITEM", "ID_PARTICLE", "ID_DOODAD"
]

# Global : Variables
instance_last = None  # 마지막 개체
instance_list: list = []  # 개체는 순서가 있다.
"""
            <List> instance_list_spec:

                목적: 객체를 종류 별로 담기 위한 리스트
                용법:
                    instance_list_spec[객체 이름] = []
                    instance_list_spec[객체 이름].append(객체 ID)

                비고: 객체 이름 외에도 "Solid", "Particle" 등의 구별자 사용.
"""
instance_list_spec: dict = {}  # 객체 종류 별 목록
instance_draw_list: list = []  # 개체 그리기 목록
instance_update: bool = false  # 개체 갱신 여부

player_lives = 3

ID_SOLID: str = "Solid"
ID_PARTICLE: str = "Particle"
ID_DOODAD: str = "Doodad"
ID_DMG_PLAYER: str = "HurtPlayer"
ID_DMG_ENEMY: str = "HurtEnemy"
ID_ENEMY: str = "Enemy"
ID_ITEM: str = "Items"
instance_list_spec[ID_SOLID] = []
instance_list_spec[ID_PARTICLE] = []
instance_list_spec[ID_DOODAD] = []
instance_list_spec[ID_DMG_PLAYER] = []
instance_list_spec[ID_DMG_ENEMY] = []
instance_list_spec[ID_ENEMY] = []
instance_list_spec[ID_ITEM] = []

container_player = None


# TODO: Definite more objects.
# Declaring of Special Objects ( Need a canvas )

# ==================================================================================================
#                                               게임
# ==================================================================================================
# Object : A container of Status
class oStatusContainer:
    NONE = 0
    IDLE = 1
    WALK = 8
    RUNNING = 10
    ATTACKING = 40
    ATTACKING_END = 45
    CHANNELING = 60
    STUNNED = 80
    DEAD = 98
    DISAPPEAR = 99


# Object : Game Object
class GObject(object):
    # Basis properties of object
    name: str = "None"
    identify: str = ""
    next: object = None
    
    # Advanced properties of object
    oStatus = oStatusContainer.IDLE
    stunned: int = 0
    
    # Properties of sprite
    sprite_index: Sprite = None
    image_alpha: float = 1.0
    image_index = float(0)
    image_speed = float(0)
    visible: bool = true
    depth: int = 0
    image_xscale: float = 1
    
    # for optimization
    step_enable: bool = true
    
    # Physics
    x, y = 0, 0
    xVel, yVel = 0, 0
    xVelMin, xVelMax = -10, 10
    yVelMin, yVelMax = -8, 16
    xFric, yFric = 0.6, 0
    gravity_default: float = 0.4
    gravity: float = 0
    onAir: bool = false
    bbox = SDL_Rect()
    
    def __init__(self, ndepth=int(0), nx=int(0), ny=int(0)):
        if ndepth is not None:
            self.depth = ndepth
        self.x = nx
        self.y = ny
        self.bbox.x = self.x
        self.bbox.y = self.y
        
        global instance_list, instance_update, instance_list_spec
        instance_list.append(self)
        instance_update = true
        if self.identify != "":
            instance_list_spec[self.identify].append(self)
    
    def __str__(self):
        return self.name
    
    def __del__(self):
        global instance_list, instance_list_spec, instance_draw_list, instance_update
        instance_update = true
        
        if self.identify != "":
            instance_list_spec[self.identify].remove(self)
    
    def bbox_update(self):
        sdata = self.sprite_index
        self.bbox.x = int(self.x - sdata.xoffset)
        self.bbox.y = int(self.y - sdata.yoffset)
    
    def sprite_set(self, spr: Sprite or str):
        if type(spr) == str:
            self.sprite_index = sprite_get(spr)
        else:
            self.sprite_index = spr
        self.image_index = 0
        sdata = self.sprite_index
        self.bbox.w = sdata.width
        self.bbox.h = sdata.height
        self.bbox.x = self.x - sdata.xoffset
        self.bbox.y = self.y - sdata.yoffset
    
    # Below methods are common-functions for all object that inherits graviton.
    # Check the place fits to self
    def place_free(self, vx, vy, olist=None) -> bool:
        self.bbox_update()
        def __toback(msign):
            self.bbox.x += int(vx * msign)
            self.bbox.y += int(vy * msign)
        if olist is None:
            global instance_list_spec
            clist = instance_list_spec["Solid"]  # 고체 개체 목록 불러오기
        else:
            clist = olist
        length = len(clist)
        if length > 0:
            # print("Checking Place for one")
            __toback(1)
            temprect = SDL_Rect()

            for inst in clist:
                tempspr: Sprite = inst.sprite_index
                otho_left = int(inst.x - tempspr.xoffset)
                otho_top = int(inst.y - tempspr.yoffset)
                temprect.x, temprect.y, temprect.w, temprect.h = otho_left, otho_top + 2, tempspr.width, tempspr.height
                if rect_in_rectangle_opt(self.bbox, temprect):
                    __toback(-1)
                    return false
            __toback(-1)
            return true
        else:
            return true
    
    def move_contact_x(self, dist: float or int = 1, right: bool = false) -> bool:
        tdist = dist
        if dist < 0:
            tdist = 1000000
        if dist == 0:
            return false
        
        global instance_list_spec
        clist = instance_list_spec["Solid"]
        length = len(clist)
        xprog = 0
        cx = 0
        if length > 0:
            while xprog <= tdist:
                if right:
                    cx += 1
                else:
                    cx -= 1
                if not self.place_free(cx + sign(cx), 0):
                    self.x += cx
                    return true
                
                xprog += 1
            self.bbox_update()
            return false
        else:
            return false
    
    def collide(self, how: float or int):
        if self.xVel is not 0:
            self.move_contact_x(abs(how), how > 0)
            if self.oStatus >= oStatusContainer.STUNNED:
                self.xVel *= -0.4
            else:
                self.xVel = 0
            self.x = math.floor(self.x)
    
    def move_contact_y(self, dist: float or int = 1, up: bool = false) -> bool:
        tdist = math.ceil(dist)
        if dist < 0:
            tdist = 1000000
        if dist == 0:
            return false
        
        global instance_list_spec
        clist = instance_list_spec["Solid"]
        length = len(clist)
        yprog = 0
        cy = 0
        if length > 0:
            templist = []
            for inst in clist:
                if bool(inst.y + inst.sprite_index.yoffset <= int(
                                        self.y - self.sprite_index.yoffset + self.sprite_index.height)) != up:
                    templist.append(inst)
            
            while yprog <= tdist:
                if up:
                    cy += 1
                else:
                    cy -= 1
                if not self.place_free(0, cy + sign(cy), templist):
                    self.y += cy
                    return true
                
                yprog += 1
            self.bbox_update()
            return false
        else:
            return false
    
    def thud(self, how: float or int):
        if self.yVel != 0:
            self.move_contact_y(abs(how) + 1, how > 0)
            if self.oStatus >= oStatusContainer.STUNNED:
                self.yVel *= -0.4
            elif self.yVel > 0:
                self.yVel *= -0.2
            else:
                self.yVel = 0
            self.y = math.floor(self.y)
        self.onAir = false
    
    def draw_self(self):  # Simply draws its sprite on its position.
        data = self.sprite_index
        if not data.__eq__(None):
            if Camera.x <= self.x - data.xoffset and Camera.y <= self.y - data.yoffset:
                draw_sprite(self.sprite_index, self.image_index, self.x, self.y, self.image_xscale, 1, 0.0,
                        self.image_alpha)
    
    def event_step(self, frame_time):  # The basic mechanisms of objects.
        if not self.step_enable:
            return
        
        count = self.sprite_index.number
        if count > 1:
            if self.image_speed > 0:
                self.image_index += count / self.image_speed * frame_time / 2
                if self.image_index >= count:
                    self.image_index -= count
        
        if self.xVel != 0:
            xdist = delta_velocity(self.xVel * 10) * frame_time
            xc = xdist + sign(xdist)
            if self.place_free(xc, 0):
                self.x += xdist
            else:
                self.collide(xdist)

        ydist = delta_velocity(self.yVel * 10) * frame_time
        if ydist > 0:  # Going up higher
            yc = ydist + 1
        else:  # Going down
            yc = ydist - 1
        if self.place_free(0, yc):
            self.y += ydist  # let it moves first.
            self.gravity = self.gravity_default
            self.yVel -= self.gravity
            self.onAir = true
        else:
            self.gravity = 0
            if self.xVel != 0:  # horizontal friction works only when it is on the ground
                if abs(self.xVel) > self.xFric:
                    self.xVel -= self.xFric * sign(self.xVel)
                else:
                    self.xVel = 0
            self.thud(ydist)
      
        self.xVel = clamp(self.xVelMin, self.xVel, self.xVelMax)
        self.yVel = clamp(self.yVelMin, self.yVel, self.yVelMax)

    
    def event_draw(self):  # This will be working for drawing.
        self.draw_self()


# Object : Solid Objects
class Solid(GObject):
    # reset some inherited variables
    name = "Solid"
    identify = ID_SOLID
    
    image_speed = 0
    depth = 1000
    step_enable = false
    gravity_default = 0
    xFric, yFric = 0, 0


# ==================================================================================================
#                                    사용자 정의 객체 / 함수
# ==================================================================================================
# Object : Functions
def instance_create(Ty, depth=int(0), x=int(0), y=int(0)) -> object:
    temp = Ty(depth, x, y)
    global instance_last
    instance_last = temp
    return temp


def instance_place(Ty, fx, fy) -> object or list:
    try:
        ibj = Ty.identify
    except AttributeError:
        print("Cannot find variable 'identify' in %s" % (str(Ty)))
        sys.exit(-1)

    global instance_list_spec
    clist = instance_list_spec["Solid"]  # 고체 개체 목록 불러오기
    length = len(clist)
    if length > 0:
        temprect = SDL_Rect()
    
    for inst in clist:
        pass

    return Ty()


# Definitions of Special Objects
# Brick
class oBrick(Solid):
    name = "Brick of Mine"
    
    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("sCastleBrick")
        self.image_index = choose(0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 3)


# Player
class oPlayer(GObject):
    name = "Player"
    depth = 0
    image_speed = 0

    xVelMin, xVelMax = -3, 3
    
    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("Player")

        global container_player
        container_player = self
    
    def event_step(self, frame_time):
        super().event_step(frame_time)
        if self.oStatus < oStatusContainer.CHANNELING:  # Player can control its character.
            mx = 0
            if io.key_check(SDLK_LEFT): mx -= 1
            if io.key_check(SDLK_RIGHT): mx += 1
            if not self.onAir:
                if mx != 0:
                    self.xVel += mx * 0.6
                else:
                    self.xFric = 0.4
            else:
                if mx != 0:
                    self.xVel += mx * 0.2
                else:
                    self.xFric = 0.2
            if mx != 0:
                self.image_xscale = mx
            
            if io.key_check_pressed(SDLK_UP):
                if not self.onAir:
                    self.yVel = 6
            
            if not self.onAir:
                if self.xVel != 0:
                    self.image_speed = 0.3
                    self.sprite_index = sprite_get("PlayerRun")
                else:
                    self.image_speed, self.image_index = 0, 0
                    self.sprite_index = sprite_get("Player")
            else:
                self.image_speed, self.image_index = 0, 0
                self.sprite_index = sprite_get("PlayerJump")
        else:  # It would be eventual, and uncontrollable
            self.image_speed, self.image_index = 0, 0
            if self.oStatus == oStatusContainer.DEAD:
                self.sprite_index = sprite_get("PlayerDead")


# Parent of Enemies
class oEnemyParent(GObject):
    """
            모든 적 객체의 부모 객체
    """
    name = "NPC"
    identify = ID_ENEMY
    depth = 100
    
    hp, maxhp = 1, 1
    mp, maxmp = 0, 0
    oStatus = oStatusContainer.IDLE
    image_speed = 0
    collide_with_player: bool = false


class oSoldier(oEnemyParent):
    hp, maxhp = 4, 4
    name = "Soldier"
    xVelMin, xVelMax = -2, 2
    
    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("SoldierIdle")
        self.runspr = sprite_get("SoldierRun")
        self.image_speed = 0


# Damage caused by Player
class oPlayerDamage(GObject):
    name = "DamageP"
    identify = ID_DMG_PLAYER
    gravity_default = 0
    life = fps_target


# Damage caused by Enemy
class oEnemyDamage(GObject):
    name = "DamageE"
    identify = ID_DMG_ENEMY
    gravity_default = 0
    life = fps_target


# Parent of Items
class oItemParent(GObject):
    name = "Item"
    identify = ID_ITEM
    gravity_default = 0


# Parent of Terrain Doodads
class oDoodadParent(GObject):
    name = "Doodad"
    identify = ID_DOODAD
    gravity_default = 0
