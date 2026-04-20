import pygame as pg
import math as m
import random as rd
import time as tm

from calculations import (profiling_sect, chars, chars_symbol, lerp, wraptext)

# Module-level state - set via init() from main.py before use
win = None
screenw = 768
jr = True
oldgrad = False
widescreen = False
old = {""}

# Colors
bg_c = []
ban_c = []
box_c = []
bg_g = None
al_g = None
ldl_c = None
outer_c = None
white = (215, 215, 215)
yeller = (187, 182, 45)

# Fonts (pygame font objects)
smallfont = None
largefont32 = None
startitlefont = None
starfont32 = None
extendedfont = None

# JR fonts
jrfontnormal = None
jrfontsmall = None
jrfonticon = None
jrfonttravel = None
jrfontsymbol = None
jrfonttall = None
jrfontradaralert = None

# Font metrics
font_tallest = {}

# Per-frame state (updated by main.py each frame)
ldl_y = 0

# Constants
linespacing = 40.25
gmono = 18.15
fw = 1.1
char_offsets_default = {
    ":": -3,
    ".": -6
}

# Caches
char_list = {}
charset_col = {}


def init(**kwargs):
    g = globals()
    for k, v in kwargs.items():
        g[k] = v


def draw_palette_gradient(rect : pg.Rect, colors, fuzzy=0.5):
    surface = pg.Surface(rect.size)
    x, y, w, h = rect
    num_steps = len(colors) - 1
    if num_steps <= 0:
        pg.draw.rect(surface, colors[0], rect)
        return

    step_height = h / num_steps

    for step in range(num_steps):
        c1 = colors[step]
        c2 = colors[step + 1]
        y_start = int(y + step * step_height)
        y_end = int(y + (step + 1) * step_height)

        for j in range(y_start, y_end):
            # how far along we are between the two step colors
            t = (j - y_start) / (y_end - y_start)
            # probability of using the second color increases with t
            prob_c2 = t

            for i in range(x, x + w):
                if rd.random() < prob_c2:
                    surface.set_at((i, j), c2)
                else:
                    surface.set_at((i, j), c1)

    return surface


def draw_bg(top_offset=0, bh_offset=0, all_offset=0, special=None, box=True):
    win.fill((104, 104, 104))
    if special == "al":
        win.fill((64, 64, 64))
    if special != "al":
        if oldgrad:
            pg.draw.rect(win, bg_c[0], pg.Rect(0, 90-all_offset, screenw, 45))
            pg.draw.rect(win, bg_c[1], pg.Rect(0, 135-all_offset, screenw, 45))
            pg.draw.rect(win, bg_c[2], pg.Rect(0, 180-all_offset, screenw, 45))
            pg.draw.rect(win, bg_c[3], pg.Rect(0, 225-all_offset, screenw, 45))
            pg.draw.rect(win, bg_c[4], pg.Rect(0, 270-all_offset, screenw, 45))
            pg.draw.rect(win, bg_c[5], pg.Rect(0, 315-all_offset, screenw, 45))
            pg.draw.rect(win, bg_c[6], pg.Rect(0, 360-all_offset, screenw, 45))
        else:
            win.blit(bg_g, (0, 90-all_offset))
    if not special and box:
        xoff = (screenw-768)//2
        pg.draw.rect(win, box_c[0], pg.Rect(62+xoff, 90-all_offset, 622, 310-bh_offset))
        pg.draw.rect(win, box_c[1], pg.Rect(66+xoff, 94-all_offset, 614, 302-bh_offset))
        pg.draw.rect(win, box_c[2], pg.Rect(70+xoff, 98-all_offset, 606, 294-bh_offset))
        pg.draw.rect(win, box_c[3], pg.Rect(74+xoff, 102-all_offset, 598, 286-bh_offset))
        pg.draw.rect(win, box_c[4], pg.Rect(78+xoff, 106-all_offset, 590, 278-bh_offset))
    if special == "al":
        if "oldal" not in old:
            win.blit(al_g, (0, 91-all_offset))
        else:
            pg.draw.rect(win, bg_c[1], pg.Rect(0, 91-all_offset, screenw, 48+3))
            pg.draw.rect(win, bg_c[2], pg.Rect(0, 91+48+3-all_offset, screenw, 48+3))
    if special == "df":
        xoff = (screenw-768)//2
        adjust = -6
        for i  in range(4):
            yoo = (ldl_y//4)
            pg.draw.rect(win, box_c[0], pg.Rect(62+xoff, 90- all_offset+(77+yoo)*i+9, 622, 76+adjust))
            pg.draw.rect(win, box_c[1], pg.Rect(65+xoff, 93- all_offset+(77+yoo)*i+9, 616, 70+adjust))
            pg.draw.rect(win, box_c[2], pg.Rect(68+xoff, 96- all_offset+(77+yoo)*i+9, 610, 64+adjust))
            pg.draw.rect(win, box_c[3], pg.Rect(71+xoff, 99- all_offset+(77+yoo)*i+9, 604, 58+adjust))
            pg.draw.rect(win, box_c[4], pg.Rect(74+xoff, 102-all_offset+(77+yoo)*i+9, 598, 52+adjust))


def draw_ldl(top_offset=0, bh_offset=0, all_offset=0):
    pg.draw.rect(win, ldl_c, pg.Rect(0, 400-all_offset-bh_offset, screenw, 80+all_offset+bh_offset))
    pg.draw.rect(win, (33, 26, 20), pg.Rect(0, 400-all_offset-bh_offset, screenw, 2))
    pg.draw.rect(win, (230, 230, 230), pg.Rect(0, 402-all_offset-bh_offset, screenw, 2))

def draw_banner(top_offset=0, bh_offset=0, all_offset=0):
    pg.draw.rect(win, outer_c, pg.Rect(0, 0-all_offset, screenw, 90))
    pg.draw.rect(win, ban_c[0], pg.Rect(0, 30-all_offset, screenw, 9))
    pg.draw.rect(win, ban_c[1], pg.Rect(0, 38-all_offset, screenw, 9))
    pg.draw.rect(win, ban_c[2], pg.Rect(0, 46-all_offset, screenw, 9))
    pg.draw.rect(win, ban_c[3], pg.Rect(0, 54-all_offset, screenw, 9))
    pg.draw.rect(win, ban_c[4], pg.Rect(0, 62-all_offset, screenw, 11))
    pg.draw.rect(win, ban_c[5], pg.Rect(0, 72-all_offset, screenw, 9))
    pg.draw.rect(win, ban_c[6], pg.Rect(0, 80-all_offset, screenw, 7))
    pg.draw.rect(win, ban_c[7], pg.Rect(0, 85-all_offset, screenw, 6))

    pg.draw.polygon(win, outer_c, [[screenw-148-top_offset, -all_offset], [screenw, -all_offset], [screenw, 90-all_offset], [screenw-238-top_offset,90-all_offset]])


def frender(font, text, aa, color):
    if (font, text, aa, color) in char_list:
        return char_list[(font, text, aa, color)]
    r = font.render(text, aa, color)
    char_list[(font, text, aa, color)] = r
    return r


def scalec(og, font, text, color, w):
    sl = pg.transform.smoothscale_by(og, w)
    return sl


def renderoutline(font, text, x, y, width, color=(0, 0, 0), surface=None, og=None, ofw=None):
    if surface is None:
        surface = win
    if og is None:
        og = frender(font, text, True, (0, 0, 0))
        og = scalec(og, font, text, color, (fw if ofw is None else ofw, 1))
    surface.blit(og, (x-width, y-width))
    surface.blit(og, (x+width, y-width))
    surface.blit(og, (x-width, y+width))
    surface.blit(og, (x+width, y+width))


def drawchar(char, cset, x, y, color, half=0):
    if char.strip() == "":
        return
    if char in chars:
        ix = chars.index(char)
    elif char in chars_symbol:
        ix = chars_symbol.index(char)
    else:
        ix = 0

    if color is None:
        cset2 = cset
    else:
        if (cset, color) in charset_col:
            cset2 = charset_col[(cset, color)]
        else:
            cset2 = cset.copy()
            cset2.fill(color, special_flags=pg.BLEND_RGBA_MULT)
            charset_col[(cset, color)] = cset2
    cheight = cset.get_height()//6
    if half == 1:
        cheight /= 2
    win.blit(cset2, (x, y), pg.Rect((ix*32)%cset.get_width(), int(ix*32//cset.get_width())*(cset.get_height()//6), 32, cheight))


@profiling_sect("text")
def drawshadow(font, text, x, y, offset, color=None, surface=None, mono=0, ofw=None, bs=False, char_offsets=None, upper=False, jr_override=None, shadow=True, variable=None, leftalign=False):
    if color is None:
        color = white
    if surface is None:
        surface = win
    if char_offsets is None:
        char_offsets = char_offsets_default
    if text == "":
        return
    if upper:
        text = text.upper()
    if not jr:
        t = [c for ch in text if c not in "±≠"]
        text = "".join(t)
    if jr:
        offsetx = 0
        if leftalign:
            for i, char in enumerate(text):
                if char in "±≠":
                    continue
                if variable:
                    offsetx -= (variable[chars.index(char)]+1) if variable[chars.index(char)] else 15
                else:
                    offsetx -= m.floor(mono)
        fx = [[], []] #shake, nofill
        fxa = [False, False]
        sheet = jrfontnormal
        y += 6
        if font == largefont32:
            sheet = jrfonttravel
        elif font == smallfont:
            sheet = jrfontsmall
            y += 10
        elif font == extendedfont:
            sheet = jrfonticon
        if jr_override:
            sheet = jr_override
        xx = offsetx*1
        if bs:
            if shadow:
                for i, char in enumerate(text):
                    drawchar(char, sheet[1], x+xx+2+char_offsets.get(char, 0), y+2, None)
                    if variable:
                        xx += (variable[chars.index(char)]+1) if variable[chars.index(char)] else 15
                    else:
                        xx += m.floor(mono)
            xx = offsetx*1
            for i, char in enumerate(text):
                drawchar(char, sheet[0], x+xx+2+char_offsets.get(char, 0), y+2, color if type(color) != list else color[i])
                if variable:
                    xx += (variable[chars.index(char)]+1) if variable[chars.index(char)] else 15
                else:
                    xx += m.floor(mono)
        io = 0
        ic = 0
        if shadow:
            xx = offsetx*1
            for i, char in enumerate(text):
                if char == "±":
                    io += 1
                    fxa[0] = not fxa[0]
                    continue
                if char == "≠":
                    io += 1
                    fxa[1] = not fxa[1]
                    continue
                fxo = (0, 0)
                if fxa[0]:
                    fxo = (rd.randint(-1, 1), rd.randint(-1, 1))
                    fx[0].append(fxo)
                drawchar(char, sheet[1], x+fxo[0]+xx+char_offsets.get(char, 0), y+fxo[1], None, half=fxa[1])
                if variable:
                    xx += (variable[chars.index(char)]+1) if variable[chars.index(char)] else 15
                else:
                    xx += m.floor(mono)
        fxa = [False, False]
        io = 0
        xx = offsetx*1
        for i, char in enumerate(text):
            if char == "±":
                io += 1
                fxa[0] = not fxa[0]
                continue
            if char == "≠":
                io += 1
                fxa[1] = not fxa[1]
                continue
            fxo = (0, 0)
            if fxa[0]:
                fxo = fx[0][ic]
                ic += 1
            drawchar(char, sheet[0], x+fxo[0]+xx+char_offsets.get(char, 0), y+fxo[1], color if type(color) != list else color[i], half=fxa[1])
            if variable:
                xx += (variable[chars.index(char)]+1) if variable[chars.index(char)] else 15
            else:
                xx += m.floor(mono)
        return

    text=str(text)
    if upper:
        text = text.upper()
    if mono == 0:
        og = frender(font, text, True, (0, 0, 0))
        og = scalec(og, font, text, (0, 0, 0), (fw if ofw is None else ofw, 1))
        if not bs:
            surface.blit(og, (x+offset, y+offset))
        else:
            for i in range(offset):
                surface.blit(og, (x+i+1, y+i+1))
        renderoutline(font, text, x, y, 1, og=og, ofw=ofw, surface=surface)
        surface.blit(scalec(frender(font, text, True, color), font, text, color, (fw if ofw is None else ofw, 1)), (x, y))
    else:
        if type(color[0]) in [int, float]:
            col = color
        for i, char in enumerate(text):
            if char == " ":
                continue
            coffset = 0
            if char in char_offsets:
                coffset = char_offsets[char]
            og = frender(font, char, True, (0, 0, 0))
            og = scalec(og, font, char, (0, 0, 0), (fw if ofw is None else ofw, 1))
            coffset2 = 0
            if font in font_tallest:
                coffset2 = font_tallest[font] - font.size(char)[1]
            if not bs:
                surface.blit(og, (x+mono*i+offset+coffset, y+offset+coffset2))
            else:
                for j in range(offset):
                    surface.blit(og, (x+mono*i+j+2+coffset, y+j+2+coffset2))
                    surface.blit(og, (x+mono*i+j+2+coffset, y+j+coffset2))
                    surface.blit(og, (x+mono*i+j+coffset, y+j+2+coffset2))
            renderoutline(font, char, x+mono*i+coffset, y+coffset2, 1, og=og, ofw=ofw, surface=surface)
            #surface.blit(scalec(frender(font, char, True, col), font, char, col, (fw if ofw is None else ofw, 1)), (x+mono*i, y))
        for i, char in enumerate(text):
            if type(color[0]) in [list, tuple]:
                col = color[i]
            if char == " ":
                continue
            coffset = 0
            if char in char_offsets:
                coffset = char_offsets[char]
            coffset2 = 0
            if font in font_tallest:
                coffset2 = font_tallest[font] - font.size(char)[1]
            surface.blit(scalec(frender(font, char, True, col), font, char, col, (fw if ofw is None else ofw, 1)), (x+mono*i+coffset, y+coffset2))


def drawpage_fmt(lines : list, formatting : list):
    yy = 109-linespacing*4
    fmt = [1, "W"]
    colors = {
        "W": white,
        "R": (255, 0, 0),
        "G": (0, 255, 0),
        "B": (0, 0, 255),
        "C": (0, 255, 255),
        "M": (255, 0, 255),
        "K": (0, 0, 0)
    }
    if len(formatting) < len(lines):
        formatting.extend([None for _ in range(len(lines)-len(formatting))])
    xoff = (screenw-768)//2
    for i, line in enumerate(lines):
        yo = 0

        if formatting[i]:
            fmmt = formatting[i].split("_")
            fmt = [int(fmmt[0]), fmmt[1]]

        coll = colors[fmt[1]]

        if fmt[0] == 1:
            drawshadow(starfont32, line, 80+xoff, 109+yy+ldl_y*1.25+yo, 3, mono=gmono, char_offsets={}, color=coll)
            yy += linespacing
        elif fmt[0] == 0:
            yo = -8
            drawshadow(smallfont, line, 80+xoff, 109+yy+ldl_y*1.25+yo, 3, mono=gmono, char_offsets={}, color=coll)
            yy += linespacing/2
        elif fmt[0] == 2:
            drawshadow(largefont32, line, 80+xoff, 109+yy+ldl_y*1.25+yo, 3, mono=gmono, char_offsets={}, color=coll, jr_override=jrfonttall)
            yy += linespacing


def drawpage(lines : list, smalltext="", shift=0, vshift=0):
    clines : list = lines.copy()
    ss = 0
    st = True
    xoff = (screenw-768)//2
    ld = 0
    for i, line in enumerate(clines):
        if line == '' and st:
            ss += 1
        else:
            st = False
            ld += 1
        if ld == 8:
            break
        drawshadow(starfont32, line, 80+xoff, 109+linespacing*(i-ss)+ldl_y*1.25+vshift, 3, mono=gmono, char_offsets={})
    if smalltext:
        drawshadow(smallfont, smalltext, 80+xoff, 109-32+ldl_y+vshift, 3, mono=gmono, char_offsets={})


def drawpage2(lines : list, smalltext="", shift=0):
    clines : list = lines[(shift*7):(shift*7+7)].copy()
    ss = 0
    st = True

    startline = 109+ldl_y*1.25
    endline = 109+linespacing*(6)+ldl_y*1.25
    xoff = (screenw-768)//2
    for i, line in enumerate(clines):
        if line == '' and st:
            ss += 1
        else:
            st = False
        drawshadow(starfont32, line, 80+xoff, lerp(endline, startline, i/(len(lines)-1)), 3, mono=gmono, char_offsets={})
    if smalltext:
        drawshadow(smallfont, smalltext, 80+xoff, 109-32+ldl_y, 3, mono=gmono, char_offsets={})


def drawreg(surf, pos, ix=0):
    if surf:
        #win.blit(surf[ix][0], (pos[0]-surf[ix][0].get_width()//2, pos[1]-surf[ix][0].get_height()//2))
        win.blit(pg.transform.smoothscale_by(surf[ix][0], (1.2, 1)), (pos[0]-32, pos[1]-19))
