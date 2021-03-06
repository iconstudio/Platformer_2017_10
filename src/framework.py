from pico2d import *
from constants import *

import json

from sprite import *
from audio import *

__all__ = [
    "GameState", "change_state", "push_state", "pop_state", "quit", "run", "option_load",
    "io", "game_begin", "game_end", "current_time", "game_realtime", "uiframe",
    "hFont", "hFontLrg", "hFontRetro", "draw_text", "stage_number"
]

keylogger_list = []
hFont, hFontLrg = None, None
hFontRetro = None
stage_number = 0
optefx = true


def option_load():
    with open(path_data + "option.json") as opfile:
        global optefx
        data = json.load(opfile)
        volsfx = data["volume_sfx"]
        volmus = data["volume_mus"]
        optefx = data["effect"]

        audio_set_volume_sfx_global(volsfx)
        audio_set_volume_music_global(volmus)


# noinspection PyUnusedLocal
def game_begin():
    HWND = open_canvas(screen_width, screen_height, full = false)
    SDL_SetWindowTitle(HWND, "Vampire Exodus".encode("UTF-8"))
    # icon = load_texture(path_image + "icon.png")
    # SDL_SetWindowIcon(hwnd, icon)
    # SDL_SetWindowSize(hwnd, screen_width * screen_scale, screen_height * screen_scale)
    # SDL_SetWindowFullscreen(self.hwnd, ctypes.c_uint32(1))
    hide_cursor()
    hide_lattice()
    draw_background_color_set(0, 0, 0)

    global hFont, hFontLrg, hFontRetro
    hFont = load_font(path_font + "윤고딕_310.ttf")
    hFontLrg = load_font(path_font + "윤고딕_310.ttf", 28)

    fontlist = []
    for i in range(0, 58):
        tempstr = "sFont_" + str(i)
        fontlist.append(path_ui + tempstr + ".png")
    ft = Sprite(fontlist, 59, 0, 20)

    tempstr = str('!"' + "#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    hFontRetro = Font_sprite(ft, tempstr)

    option_load()


def draw_text(caption: str, dx, dy, font: int = 2, scale: float = 1.0):
    global hFont, hFontLrg, hFontRetro
    dfont = hFontRetro
    if font == 0:
        dfont = hFont
    elif font == 1:
        dfont = hFontLrg
    dfont.draw(dx, dy, caption, scale)


def game_end():
    close_canvas()

    global hFont, hFontLrg
    del hFont, hFontLrg


# Object : IO procedure
class oIOProc:
    key_list = []
    # This dictionary contains only the Node of keyboard.
    key_map = {}
    # list of checking obj.
    checker_list = {}

    class iochecker:
        code = None
        life = 2
        owner = None

        def __init__(self, nowner, key: SDL_Keycode):
            self.owner = nowner
            self.code = key

        def __del__(self):
            self.owner.timer = None
            try:
                global keylogger_list
                keylogger_list.remove(self)
            except ValueError:
                pass
            except AttributeError:
                pass

        def event_step(self):
            if self.life == 0:
                self.owner.check_pressed = false
                del self
            else:
                self.life -= 1

    class ionode:
        code = None
        timer = None
        check: bool = false
        check_pressed: bool = false

        def __init__(self, key: SDL_Keycode):
            self.code = key

        def enter(self):
            self.check = true
            self.check_pressed = true

            if self.timer is None:
                global io
                self.timer = io.iochecker(self, self.code)
                io.checker_list[self.code] = self.timer

                global keylogger_list
                keylogger_list.append(self.timer)

        def close(self):
            self.check = false
            self.check_pressed = false

            if self.timer is not None:
                del self.timer
                self.timer = None

    def key_add(self, key: SDL_Keycode):
        newnode = self.ionode(key)
        self.key_map[key] = newnode
        self.key_list.append(key)
        return newnode

    def key_check(self, key: SDL_Keycode) -> bool:
        try:
            return (self.key_map[key]).check
        except KeyError:
            return false

    def key_check_pressed(self, key: SDL_Keycode) -> bool:
        try:
            return (self.key_map[key]).check_pressed
        except KeyError:
            return false

    def proceed(self, kevent):
        try:
            node = self.key_map[kevent.key]

            if kevent.type == SDL_KEYDOWN:
                node.enter()
            elif kevent.type == SDL_KEYUP:
                node.close()
        except KeyError:
            return

    def clear(self):
        if len(self.key_list) > 0:
            for codes in self.key_list:
                node = self.key_map[codes]
                node.close()


def keyboard_update():
    global keylogger_list
    klen = len(keylogger_list)
    if klen > 0:
        for checker in keylogger_list:
            checker.event_step()


io = oIOProc()


class uiframe:
    name = "frame"
    x, y = 160, 90
    width, height = 320, 180
    depth = 0
    visible: bool = true
    clicked = false
    color = (255, 255, 255)
    color_inner = (255, 255, 255)

    def __init__(self, ntype: str = "ui", nx = 180, ny = 90, nw = 320, nh = 180):
        self.name = ntype
        self.x, self.y, self.width, self.height = nx, ny, nw, nh
        if self.name in ("button",):
            global ui_focus
            ui_focus = self
        elif self.name == "frame":
            global ui_top
            ui_top = self
        global ui_list
        ui_list.append(self)

    def get_bbox(self):
        return self.x, self.y, self.width, self.height

    def update(self, frame_time):
        pass

    def draw(self, frame_time):
        draw_set_alpha(1)
        draw_set_color(*self.color)
        draw_rectangle(self.x, self.y, self.x + self.width, self.y + self.height)


class uibutton(uiframe):
    caption: str = "button"
    depth = -100
    color_inner = (0, 0, 0)

    def __init__(self, caption: str, nx, ny, nw = 80, nh = 45):
        super().__init__("button", nx, ny, nw, nh)
        self.caption = caption

    def draw(self, frame_time):
        super().draw(frame_time)
        draw_set_color(*self.color_inner)


class GameState:
    def __init__(self, state):
        self.enter = state.enter
        self.exit = state.exit
        self.pause = state.pause
        self.resume = state.resume
        self.handle_events = state.handle_events
        self.update = state.update
        self.draw = state.draw


running = None
stack = None
current_time: float = 0.0
game_realtime: float = 0.0
paused = false
# Only UI frames
ui_top = None
# Only controllable component
ui_focus = None
ui_list = []


def ui_update(frame_time):
    global ui_list
    if len(ui_list) > 0:
        for inst in ui_list:
            inst.update(frame_time)


def ui_draw(frame_time):
    global ui_list
    if len(ui_list) > 0:
        for inst in ui_list:
            inst.draw(frame_time)


def get_frame_time():
    global current_time, game_realtime, paused

    frame_time = get_time() - current_time
    current_time += frame_time
    if not paused:
        game_realtime += frame_time
    return frame_time


def change_state(state):
    global stack
    pop_state()
    stack.append(state)
    state.enter()
    print(": " + state.name + " begins")
    io.clear()


def push_state(state):
    global stack
    if len(stack) > 0:
        stack[-1].pause()
    stack.append(state)
    state.enter()
    print(": " + state.name + " begins")
    io.clear()


def pop_state():
    global stack
    if len(stack) > 0:
        # execute the current state's exit function
        stack[-1].exit()
        # remove the current state
        stack.pop()

    # execute resume function of the previous state
    if len(stack) > 0:
        stack[-1].resume()
    io.clear()


def quit():
    global running
    running = False


def pause():
    global paused
    paused = true


def unpause():
    global paused
    paused = false


def run(start_state):
    global running, stack, io, current_time
    running = True

    io.key_add(SDLK_LEFT)
    io.key_add(SDLK_UP)
    io.key_add(SDLK_RIGHT)
    io.key_add(SDLK_DOWN)
    io.key_add(SDLK_RETURN)
    io.key_add(ord('z'))
    io.key_add(ord('x'))
    io.key_add(ord('c'))
    io.key_add(ord('9'))
    io.key_add(ord('8'))

    stack = [start_state]
    start_state.enter()
    current_time = get_time()
    while running:
        ftime = get_frame_time()
        keyboard_update()
        ui_update(ftime)
        stack[-1].handle_events(ftime)
        stack[-1].update(ftime)
        stack[-1].draw(ftime)
        ui_draw(ftime)
    # repeatedly delete the top of the stack
    while len(stack) > 0:
        stack[-1].exit()
        stack.pop()
