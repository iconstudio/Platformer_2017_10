from functions import *
from constants import *

from gobject_header import *

__all__ = [
    "oDoor", "oDoorMetalic", "oLushDecoration", "oDirtBrickDecoration",
    "oMillHousechip", "oMillHousestone", "oMillHousechipL", "oMillHousechipR",
    "oMillHousechipM", "oTorch", "oLadder", "oLamp", "oWeb", "oThorns",
    "oIce", "oIceBlock",
]


# Door
class oDoor(oDoodadParent):
    name = "Door"
    depth = 1000
    image_speed = 0

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("sDoor")


# Metal Door
class oDoorMetalic(oDoodadParent):
    name = "Metal Door"
    depth = 1000
    identify = ID_DOODAD_DECO

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("sDoorMetal")


# A Decorator of Dirt
class oDirtBrickDecoration(oDoodadParent):
    name = "Dirt Decoration"
    identify = ID_DOODAD_DECO

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("sDirtBrickDoodad")
        self.image_index = choose(0, 0, 0, 0, 0, 0, 0, 1, 1)


# A Decorator of Lush
class oLushDecoration(oDoodadParent):
    name = "Lush Decoration"
    identify = ID_DOODAD_DECO

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("sLushDoodad")
        self.image_index = choose(0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 2)


# Tiki Torch
class oTorch(oDoodadParent):
    name = "Torch"
    image_speed = 0.6
    step_enable = true

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("sTorch")
        self.image_index = irandom(4)


# Ladder
class oLadder(oDoodadParent):
    name = "Ladder"
    depth = 900

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("sLadder")
        self.image_speed = 0


# Lamp
class oLamp(oDoodadParent):
    name = "Lamp"
    depth = 900

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("sLamp")
        self.image_speed = 0.6


# Trap : Web
class oWeb(oDoodadParent):
    name = "Web"
    depth = 10
    identify = ID_TRAP

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("sWeb")
        self.image_speed = 0


# Trap : Thorns
class oThorns(oDoodadParent):
    name = "Lamp"
    depth = -50
    identify = ID_TRAP

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("sThorns")
        self.image_speed = 0

    def get_bbox(self):
        return self.x + 2, self.y, 16, 12


# A tile of mil at intro
class oMillHousechip(oDoodadParent):
    name = "Wood"
    depth = 900

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("sWood")
        self.image_speed = 0


# A tile of mil at intro
class oMillHousestone(oDoodadParent):
    name = "Stone"
    depth = 900
    image_index = 0

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("sStonewall")


# A tile of mil at intro
class oMillHousechipL(oMillHousechip):
    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.image_index = 1


# A tile of mil at intro
class oMillHousechipR(oMillHousechip):
    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.image_index = 2


# A tile of mil at intro
class oMillHousechipM(oMillHousechip):
    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.image_index = 3


# Ice at boss
class oIce(oDoodadParent):
    name = "Ice"

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("sIce")


class oIceBlock(oEffectParent):
    name = "Ice Block"
    depth = 900
    image_index = 0
    gravity_default = delta_gravity()

    def __init__(self, ndepth, nx, ny):
        super().__init__(ndepth, nx, ny)
        self.sprite_set("sBlockIce")
