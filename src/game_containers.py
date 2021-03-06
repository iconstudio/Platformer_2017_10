from pico2d import *
from functions import *
from constants import *

import math
import framework
from camera import *
from framework import io
import game_over

from game_solid import *
from game_doodad import *
from game_item import *
from gobject_header import *
from game_variables import *

from sprite import *
from audio import *

__all__ = [
    "oPlayer", "oSoldier", "oManBeard", "oSnake", "oCobra", "oSpider", "oToad"
]


# ==================================================================================================
#                                               게임
# ==================================================================================================


# ==================================================================================================
#                                    사용자 정의 객체 / 함수
# ==================================================================================================
# Declaring of Special Objects ( Need a canvas )
# Definitions of Special Objects


# Player
class oPlayer(GObject):
    name = "Player"
    depth = 0
    image_speed = 0

    # anitem what to hold on
    held: object = None

    # time of invincible (seconds)
    invincible: float = 0
    # time of uncontrollable (seconds)
    controllable: float = 0
    laddercount: float = 0
    attack_delay: float = 0
    pin_index = 0
    door_popup = None

    ability_jump_count = 1
    ability_dash_count = 1
    ability_jump_velocity = 90

    key_jump = ord('z')
    key_attack = ord('x')
    key_action = ord('c')

    # real-scale: 54 km per hour
    xVelMin, xVelMax = -54, 54

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_index = sprite_get("Player")

        player_instance_set(self)
        Camera.set_taget(self)

        print("Player Created!")
        Camera.set_pos(self.x, self.y)
        self.startx, self.starty = self.x, self.y

    def __del__(self):
        Camera.set_taget(None)

        print("Player Destroyed!")

    def get_bbox(self):
        return self.x - 8, self.y - 8, 16, 16

    def phy_thud(self, how: float or int):
        super().phy_thud(how)

        # PLAYER ABILITY : DOUBLE JUMP
        if player_ability_get_status(PLAYER_AB_DOUBLEJUMP):
            self.ability_jump_count = 2
        else:
            self.ability_jump_count = 1

    def status_change(self, what):
        self.oStatus = what

    def die(self):
        io.clear()
        audio_play("sndDie")
        framework.change_state(game_over)

    def get_dmg(self, how: int = 1, dir = 1):
        player_got_damage(how)
        if player_get_lives() <= 0:  # GAME OVER
            self.status_change(oStatusContainer.DEAD)
            self.xVel = 0

            self.die()
        else:
            if self.oStatus is oStatusContainer.LADDERING:
                self.status_change(oStatusContainer.IDLE)
            self.invincible = 3  # 3 seconds
            io.clear()
            self.xVel = -dir * 20
            self.yVel += 15  # Bounces
            self.controllable = 0.5  # 0.5 seconds
            audio_play("sndHurt")

    def event_step(self, frame_time) -> None:
        Camera.set_pos(self.x, self.y)
        if self.oStatus is oStatusContainer.LADDERING:
            self.gravity_default = 0
            self.gravity = 0
        else:
            self.gravity_default = delta_gravity()
            self.yFric = 0
        super().event_step(frame_time)
        self.x = clamp(0, self.x, Camera.get_scene_width())

        # Pinned by spike trap
        if self.yVel < 0:
            ydist = delta_velocity(self.yVel) * frame_time
            thornsObj = instance_place_single(oThorns, self.x, self.y + ydist)
            if thornsObj != None:
                if self.y > thornsObj.y + 10:
                    self.die()
                    return

        # Fall through void
        if self.y <= 15:
            self.die()
            return

        # Use cheat of death
        if io.key_check_pressed(ord('9')):
            self.die()
            return

        # Use cheat of going exit
        if io.key_check_pressed(ord('8')):
            clist = get_instance_list(ID_DOODAD)
            door = None
            for inst in clist:
                if type(inst) == oDoor:  # isinstance(inst, oDoor):
                    door = inst
                    break
            if door is not None:
                self.x = door.x + 10
                self.y = door.y + 20
            return

        if self.invincible > 0:
            self.invincible -= frame_time
            self.image_alpha = 0.5
        else:
            self.image_alpha = 1
        if self.controllable > 0:
            self.controllable -= frame_time
        if self.laddercount > 0:
            self.laddercount -= frame_time

        # ===============================================================================================
        elist, ecount = instance_place(oEnemyParent, self.x, self.y)
        if ecount > 0:
            for enemy in elist:
                if not enemy.collide_with_player and enemy.oStatus < oStatusContainer.STUNNED:
                    enemy.collide_with_player = true
                    if enemy.name in (
                            "ManEater", "Lavaman",):  # Cannot ignore getting damages from these kind of enemies.
                        self.get_dmg(1, enemy.image_xscale)
                    elif self.invincible <= 0 and self.y <= enemy.y:
                        self.get_dmg(1, enemy.image_xscale)
                        Camera.screen_shake(6)
                    enemy.collide_with_player = true

        # ===============================================================================================
        if self.oStatus < oStatusContainer.CHANNELING:  # Player can control its character.
            # Stomps enemies under the character
            whothere, howmany = instance_place(oEnemyParent, self.x, self.y - 9)
            if howmany > 0 > self.yVel and self.onAir:
                for enemy in whothere:
                    if enemy.oStatus < oStatusContainer.STUNNED:
                        if enemy.name not in ("ManEater", "Yeti",):  # Cannot stomping these kind of enemies.
                            self.yVel = 60
                            if player_ability_get_status(PLAYER_AB_SPIKESHOES):
                                enemy.hp -= 3
                            else:
                                enemy.hp -= 1
                            enemy.yVel = 30
                            enemy.collide_with_player = false
                            if enemy.hp <= 0:  # Kzill the enemy
                                enemy.status_change(oStatusContainer.DEAD)

                                killcount_increase()
                            else:  # Just make stunned
                                enemy.status_change(oStatusContainer.STUNNED)
                                enemy.stunned = 5
                            audio_play("sndHit")
                        else:
                            enemy.collide_with_player = true
                            self.get_dmg(1, enemy.image_xscale)
            elif howmany > 0:  # Cannot Stomp but collide with enemy
                for enemy in whothere:
                    enemy.collide_with_player = false
                    if enemy.oStatus < oStatusContainer.STUNNED:
                        if enemy.name in ("ManEater", "Lavaman",):
                            # Cannot ignore getting damages from these kind of enemies.
                            self.get_dmg(1, enemy.image_xscale)
                        elif self.invincible <= 0:
                            self.get_dmg(1, enemy.image_xscale)
                        enemy.collide_with_player = true

            # ===============================================================================================
            mx, my = 0, 0
            if self.controllable <= 0:  # Player can controllable
                itemget = false

                instCape: oItemParent = instance_place_single(oCape, self.x, self.y)
                if instCape != None:
                    instCape.destroy()
                    player_ability_activate(PLAYER_AB_DOUBLEJUMP)
                    itemget = true

                instSpringShoes: oItemParent = instance_place_single(oSpringShoes, self.x, self.y)
                if instSpringShoes != None:
                    instSpringShoes.destroy()
                    player_ability_activate(PLAYER_AB_SPRINSHOES)
                    oPlayer.ability_jump_velocity = 105
                    itemget = true

                instSpikeShoes: oItemParent = instance_place_single(oSpikeShoes, self.x, self.y)
                if instSpikeShoes != None:
                    instSpikeShoes.destroy()
                    player_ability_activate(PLAYER_AB_SPIKESHOES)
                    itemget = true

                instAnkh: oItemParent = instance_place_single(oAnkh, self.x, self.y)
                if instAnkh != None:
                    instAnkh.destroy()
                    player_lives_increase()
                    itemget = true

                if itemget:
                    Camera.screen_shake(5)
                    audio_play("sndCollect")

                instdoor = instance_place_single(oDoor, self.x, self.y)
                self.door_popup = instdoor
                if instdoor != None:
                    if not self.onAir and io.key_check_pressed(ord('c')):
                        audio_play("sndEnterDoor")
                        self.destroy()
                        from game_executor import stage_complete
                        stage_complete()
                        return
                    self.pin_index = (self.pin_index + 0.5) % 4

                instdoor = instance_place_single(oDoorMetalic, self.x, self.y)
                if instdoor != None:
                    isOn = false
                    clist = get_instance_list(ID_SOLID)
                    for inst in clist:
                        if isinstance(inst, oBlockMetal):  # isinstance(inst, oDoor):
                            inst.destroy()
                            inst.x = -100000
                            isOn = true
                    if isOn:
                        Camera.screen_shake(30)

                # Move
                if io.key_check(SDLK_LEFT): mx -= 1
                if io.key_check(SDLK_RIGHT): mx += 1
                if io.key_check(SDLK_UP): my += 1
                if io.key_check(SDLK_DOWN): my -= 1

                if self.oStatus != oStatusContainer.LADDERING:
                    if my != 0 and self.laddercount <= 0:  # Get on a ladder
                        instl, cl = instance_place(oLadder, self.x, self.y)
                        if cl > 0:  # get stick to the ladder
                            if abs(instl[0].x + 10 - self.x) <= 4 and abs(instl[0].y + 10 - self.y) <= 6:
                                self.x = instl[0].x + 10
                                # self.y = self.wladder.y + 10
                                self.xVel, self.yVel = 0, 0
                                self.status_change(oStatusContainer.LADDERING)
                                self.sprite_set("Player")
                                return  # change attributes only one time

                    if mx != 0:  # Move horizontal
                        self.xFric = 0
                        if not self.onAir:
                            self.xVel += mx * 5
                        else:
                            self.xVel += mx * 2
                        self.image_xscale = mx
                    else:
                        self.xFric = 0.6

                    if io.key_check_pressed(self.key_jump):  # Jump
                        do_jump: bool = false
                        if not self.onAir:  # On ground
                            do_jump = true
                        else:
                            if self.ability_jump_count == 2:  # Can jump while on air if player can double-jump!
                                self.ability_jump_count = 0
                                do_jump = true

                        if do_jump:
                            self.yVel = oPlayer.ability_jump_velocity
                            audio_play("sndJump")

                    # ==========================================================================================
                    if not self.onAir:  # Play Moving sprite
                        if self.xVel != 0:
                            self.image_speed = 0.8
                            self.sprite_index = sprite_get("PlayerRun")
                        else:  # Play Idle sprite
                            self.sprite_set("Player")
                    else:  # Play Jumping sprite
                        self.sprite_set("PlayerJump")

                else:  # On the ladder
                    if mx != 0:
                        self.image_xscale = mx

                    if io.key_check_pressed(self.key_jump):  # Jump on Ladder
                        if self.place_free(0, my + 4):
                            if mx != 0:
                                distance = delta_velocity(self.xVelMax / 2) * mx
                                if self.place_free(distance, 0):
                                    self.xVel = self.xVelMax / 2 * mx
                            if my != -1:
                                self.yVel = oPlayer.ability_jump_velocity * 0.75  # Jumps lower
                            self.status_change(oStatusContainer.IDLE)
                            self.sprite_set("PlayerJump")
                            audio_play("sndJump")
                            self.y += 1
                            self.laddercount = 0.3  # seconds
                            return

                    if my != 0:
                        self.yFric = 0
                        self.yVel = clamp(-20, self.yVel + my, 20)  # Climing slowly
                    else:
                        self.yFric = 1

                    if self.yVel != 0:  # Get off the ladder
                        instl = instance_place_single(oLadder, self.x, self.y)
                        if instl is None \
                                or (my <= 0 and not self.onAir):  # If there is no ladder or it is grounded.
                            self.status_change(oStatusContainer.IDLE)
                            self.sprite_set("Player")
                            self.y += 1
                            self.laddercount = 0.2

        else:  # It would be eventual, and uncontrollable
            self.image_alpha = 1

            if self.oStatus == oStatusContainer.DEAD:
                self.sprite_set("PlayerDead")


# =======================================================
# Parent of Enemies
class oEnemyParent(GObject):
    """
            모든 적 객체의 부모 객체
    """
    name = "NPC"
    identify = ID_ENEMY
    # sprite_index = sprite_get("Snake")
    depth = 500

    hp, maxhp = 1, 1
    mp, maxmp = 0, 0
    oStatus = oStatusContainer.IDLE
    image_speed = 0
    collide_with_player: bool = false
    attack_delay = 0
    sound_attack_delay = 0

    def handle_sound_attack(self, snd_delay):
        pass

    def handle_none(self, *args):
        pass

    def handle_be_idle(self, *args):
        pass

    def handle_be_patrol(self, *args):
        pass

    def handle_be_walk(self, *args):
        pass

    def handle_be_track(self, *args):
        pass

    def handle_be_attack(self, *args):
        pass

    def handle_be_stunned(self, *args):
        pass

    def handle_be_dead(self, *args):
        pass

    def handle_idle(self, *args):
        pass

    def handle_patrol(self, *args):
        pass

    def handle_walk(self, *args):
        pass

    def handle_track(self, *args):
        pass

    def handle_attack(self, *args):
        pass

    def handle_dead(self, *args):
        pass

    def handle_stunned(self, frame_time):
        if self.stunned <= 0:
            if self.hp > 0:
                self.status_change(oStatusContainer.IDLE)
            else:
                self.status_change(oStatusContainer.DEAD)
        if not self.onAir:
            self.stunned -= frame_time

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.table = {
            oStatusContainer.IDLE: (self.handle_idle, self.handle_be_idle),
            oStatusContainer.WALK: (self.handle_walk, self.handle_be_walk),
            oStatusContainer.PATROL: (self.handle_patrol, self.handle_be_patrol),
            oStatusContainer.TRACKING: (self.handle_track, self.handle_be_track),
            oStatusContainer.ATTACKING: (self.handle_attack, self.handle_be_attack),
            oStatusContainer.STUNNED: (self.handle_stunned, self.handle_be_stunned),
            oStatusContainer.DEAD: (self.handle_dead, self.handle_be_dead)
        }

    def status_change(self, what):
        if self.oStatus != what:
            (self.table[what])[1]()
        self.oStatus = what

    def event_step(self, frame_time):
        super().event_step(frame_time)

        if self.visible:
            (self.table[self.oStatus])[0](frame_time)
            if self.sound_attack_delay > 0:
                self.sound_attack_delay -= frame_time


# =======================================================
class oManBeard(oEnemyParent):
    hp, maxhp = 3, 3
    name = "Human"
    xVelMin, xVelMax = -32, 32
    count = 0

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("ManBeardIdle")
        self.runspr = sprite_get("ManBeardRun")
        self.image_speed = 0
        self.image_xscale = choose(-1, 1)

    def phy_collide(self, how: float or int):
        super().phy_collide(how)
        if self.oStatus < oStatusContainer.STUNNED and abs(how) > 1:
            self.xVel *= -1
            self.image_xscale *= -1

    def handle_be_idle(self):
        self.sprite_set("ManBeardIdle")

    def handle_be_walk(self, *args):
        self.sprite_index = self.runspr
        self.image_speed = 0.7

    def handle_be_stunned(self):
        self.sprite_set("ManBeardStunned")

    def handle_be_dead(self):
        self.sprite_set("ManBeardDead")

    def handle_idle(self, *args):
        """
            This method does not mean literally stopping when idle.
            Some gobjects can move while idle status.
        """
        self.count += args[0]
        if self.count >= 1 and probability_test(100):
            self.status_change(oStatusContainer.WALK)
            self.count = 0
            if irandom(4) == 0:
                self.image_xscale *= -1

    # moves slowly
    def handle_walk(self, *args):
        checkl, checkr = self.place_free(-10, -10), self.place_free(10, -10)
        if checkl and checkr:
            self.status_change(oStatusContainer.IDLE)
            return

        distance = delta_velocity(10) * args[0]
        if self.image_xscale == 1:
            if self.place_free(distance + 10, 0) and not self.place_free(distance + 10, -10):
                self.xVel = 10
            else:
                self.image_xscale = -1
                self.xVel = -10
        else:
            if self.place_free(distance - 10, 0) and not self.place_free(distance - 10, -10):
                self.xVel = -10
            else:
                self.image_xscale = 1
                self.xVel = 10

        if probability_test(100):
            self.xVel = 0
            self.status_change(oStatusContainer.IDLE)

    def handle_dead(self, *args):
        pass

    def handle_stunned(self, frame_time):
        super().handle_stunned(frame_time)


class oSoldier(oEnemyParent):
    hp, maxhp = 4, 4
    name = "Soldier"
    xVelMin, xVelMax = -45, 45
    count = 0

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("SoldierIdle")
        self.runspr = sprite_get("SoldierRun")
        self.image_speed = 0
        self.image_xscale = choose(-1, 1)

    def phy_collide(self, how: float or int):
        super().phy_collide(how)
        if self.oStatus < oStatusContainer.STUNNED and abs(how) > 1:
            self.xVel *= -1
            self.image_xscale *= -1

    def handle_be_idle(self):
        self.sprite_set("SoldierIdle")

    def handle_be_walk(self, *args):
        self.sprite_index = self.runspr
        self.image_speed = 0.7

    def handle_be_stunned(self):
        self.sprite_set("SoldierStunned")

    def handle_be_dead(self):
        self.sprite_set("SoldierDead")

    def handle_idle(self, *args):
        """
            This method does not mean literally stopping when idle.
            Some gobjects can move while idle status.
        """
        self.count += args[0]
        if self.count >= 1 and probability_test(100):
            self.status_change(oStatusContainer.WALK)
            self.count = 0
            if irandom(4) == 0:
                self.image_xscale *= -1

    # moves slowly
    def handle_walk(self, *args):
        checkl, checkr = self.place_free(-10, -10), self.place_free(10, -10)
        if checkl and checkr:
            self.status_change(oStatusContainer.IDLE)
            return

        distance = delta_velocity(10) * args[0]
        # self.count += delta_velocity() * args[0]
        if self.image_xscale == 1:
            if self.place_free(distance + 10, 0) and not self.place_free(distance + 10, -10):
                self.xVel = 10
            else:
                if self.place_free(distance - 10, 0):
                    self.image_xscale = -1
                    self.xVel = -10
                else:
                    self.xVel = 0
        else:
            if self.place_free(distance - 10, 0) and not self.place_free(distance - 10, -10):
                self.xVel = -10
            else:
                if self.place_free(distance + 10, 0):
                    self.image_xscale = 1
                    self.xVel = 10
                else:
                    self.xVel = 0

        if probability_test(100):
            self.xVel = 0
            self.status_change(oStatusContainer.IDLE)

    def handle_dead(self, *args):
        pass

    def handle_stunned(self, frame_time):
        super().handle_stunned(frame_time)


# =======================================================
class oSnake(oEnemyParent):
    hp, maxhp = 1, 1
    name = "Snake"
    count = 5

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("SnakeIdle")
        self.runspr = sprite_get("SnakeRun")
        self.image_speed = 0
        self.image_xscale = choose(-1, 1)

    def handle_sound_attack(self, snd_delay):
        if self.sound_attack_delay <= 0:
            self.sound_attack_delay = snd_delay
            audio_play("sndSnakeAttack")

    def handle_be_idle(self):
        self.sprite_set("SnakeIdle")

    def handle_be_walk(self, *args):
        self.sprite_set(self.runspr)
        self.image_speed = 0.65

    def handle_idle(self, *args):
        self.count += args[0]
        if self.count >= irandom_range(4, 12) and irandom(99) == 0:
            self.status_change(oStatusContainer.WALK)
            self.count = 0

    def handle_walk(self, *args):
        checkl, checkr = self.place_free(-10, -10), self.place_free(+10, -10)
        if checkl and checkr:
            self.xVel = 0
            self.status_change(oStatusContainer.IDLE)
            return

        vel = 15
        distance = delta_velocity(vel) * args[0]
        self.count += args[0]

        if self.image_xscale == 1:
            if self.place_free(distance + 5, 0) and not self.place_free(distance + 5, -10):
                self.xVel = vel
            elif self.place_free(-distance - 5, 0):
                self.image_xscale = -1
                self.xVel = -vel
            else:
                self.xVel = 0
        else:
            if self.place_free(-distance - 5, 0) and not self.place_free(-distance - 5, -10):
                self.xVel = -vel
            elif self.place_free(distance + 5, 0):
                self.image_xscale = 1
                self.xVel = vel
            else:
                self.xVel = 0

        if self.count >= 20:
            if probability_test(100):
                self.xVel = 0
                self.status_change(oStatusContainer.IDLE)
                self.count = 0

    def handle_be_dead(self, *args):
        self.destroy()


# =======================================================
class oCobra(oSnake):
    name = "Cobra"

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("CobraIdle")
        self.runspr = sprite_get("CobraRun")
        self.image_speed = 0

    def handle_be_idle(self):
        self.sprite_set("CobraIdle")


# =======================================================
class oSpider(oEnemyParent):
    hp, maxhp = 1, 1
    name = "Spider"
    count = 0
    xFric = 1
    gravity_default = 0

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.idlespr = sprite_get("SpiderHang")
        self.flipspr = sprite_get("SpiderFlipping")
        self.attkspr = sprite_get("SpiderIdle")
        self.sprite_set(self.idlespr)
        self.image_speed = 0.1
        self.y -= 4
        self.y = math.floor(self.y)

    def phy_collide(self, how: float or int):
        if self.xVel != 0:
            self.move_contact_x(abs(how), how > 0)
            if self.xVel >= 3:
                self.xVel *= -0.3
            else:
                self.xVel = -sign(self.xVel) * 12
        self.x = math.floor(self.x)

    def handle_be_track(self, *args):
        self.sprite_set(self.flipspr)
        self.yVel = -30
        self.gravity_default = delta_gravity()

    def handle_be_attack(self, *args):
        self.sprite_set(self.attkspr)
        self.gravity_default = delta_gravity()
        self.image_speed = 0.7

    def handle_idle(self, *args):
        self.yVel = 0

        cplayer = player_instance_get()
        if cplayer is None:
            return

        if cplayer.y <= self.y and self.y - cplayer.y < 320 \
                and abs(self.x - cplayer.x) <= 16:
            self.status_change(oStatusContainer.TRACKING)
            self.y -= 2

    def handle_track(self, *args):
        if round(self.image_index) >= self.sprite_index.number:
            self.image_speed = 0
            self.sprite_set(self.attkspr)

        if not self.onAir:
            self.status_change(oStatusContainer.ATTACKING)

    def handle_attack(self, *args):
        cplayer = player_instance_get()
        if cplayer is None:
            return

        if not self.onAir:
            self.count += args[0]
            if self.count >= 3:
                defVel = 30
                if probability_test(5):
                    defVel = 15
                    self.count = 2.5
                else:
                    self.count = 0

                self.yVel = 80
                audio_play("sndSpiderJump")
                if cplayer.x > self.x:
                    self.xVel = defVel
                elif cplayer.x < self.x:
                    self.xVel = -defVel

    def handle_be_dead(self, *args):
        self.destroy()


# =======================================================
class oToad(oEnemyParent):
    hp, maxhp = 1, 1
    name = "Toad"
    count = 0
    xFric = 1

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("ToadIdle")
        self.jumpspr = sprite_get("ToadJump")
        self.image_speed = 0.6

    def phy_collide(self, how: float or int):
        if self.xVel != 0:
            self.move_contact_x(abs(how), how > 0)
            if self.xVel >= 3:
                self.xVel *= -0.3
            else:
                self.xVel = -sign(self.xVel) * 10
        self.x = math.floor(self.x)

    def handle_be_idle(self):
        self.sprite_set("ToadIdle")
        self.image_speed = 0.6

    def handle_be_attack(self, *args):
        cplayer = player_instance_get()

        self.sprite_set(self.jumpspr)
        if cplayer.x > self.x:
            self.image_xscale = 1
        elif cplayer.x < self.x:
            self.image_xscale = -1
        self.image_speed = 0
        audio_play("sndFrogJump")

    def handle_idle(self, *args):
        cplayer = player_instance_get()
        if cplayer is None:
            return

        if not self.onAir:
            self.count += args[0]
            if self.count >= 4:
                self.status_change(oStatusContainer.ATTACKING)
                self.count = 0
                self.yVel = 70
                if cplayer.x > self.x:
                    self.xVel = 40
                elif cplayer.x < self.x:
                    self.xVel = -40
            elif self.sound_attack_delay <= 0 and probability_test(200):
                audio_play("sndFrog")
                self.sound_attack_delay = 2

    def handle_attack(self, *args):
        if not self.onAir:
            self.xVel = 0
            self.status_change(oStatusContainer.IDLE)
            self.sound_attack_delay = 1

    def handle_be_dead(self, *args):
        self.destroy()


# =======================================================
class oBlood(oEffectParent):
    name = "Blood"
    depth = 700

    def event_step(self, frame_time):
        super().event_step(frame_time)
