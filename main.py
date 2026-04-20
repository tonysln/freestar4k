#!/usr/bin/env python3
import datetime as dt
import os
import random as rd
import threading as th
import time as tm
import math as m
import pygame as pg
import requests as r
from io import BytesIO
import runpy
import gc

from calculations import (
    seconds, minutes, hours, profiling_start, profiling_end, clear_profile,
    splubby_the_return, padtext, textmerge, wraptext, drawing, windreduce,
    shorten_phrase, mapper, lerp, safedivide, time_fmt, AccurateClock,
    chars
)
import drawing as draw_mod
from drawing import (
    draw_palette_gradient, draw_bg, draw_ldl, draw_banner,
    drawshadow, drawpage, drawpage2, drawpage_fmt, drawreg
)
import resources as res
from resources import icontable, regionalicontable, xficontable, icon_offset, loadjrfont, quickread

VERSION = "1.2.3 Unstable A"

audiorate = 44100
widescreen = False
lfmusic = False
lsort = False
smoothscale = False
efullscreen = False

pg.display.init()
pg.font.init()

###options###

##time text position
#0    post-1993
#1    1991-1993
#2    pre-1991 (4k)
#3    pre-1991 (3000/jr)

textpos = 0

##star time drawing delay
timedrawing = True

##ldl drawing delay
ldldrawing = True

##1993 uppercase text
veryuppercase = False

##mesonet climate product id
afos_climate = "CLIJFK"

##music path
musicpath = None

##ldl over video
ldlmode = False
ldlfeed = "udp://@:1234"
##ldl mode static background (set to None for chroma key)
ldlbg = "4000bg.jpg"

##shows pressure as XX.XX in if false, otherwise XX.XX R/F/S depending on pressure trend
pressuretrend = True

##various misc old settings

old = {
    ""
}

##main location
loc="John F. Kennedy International Airport"
locname = "Kennedy Arpt"
efname = "New York Metro"

##Local Observations locations ["search name", "display name"]
obsloc = [
    ["Bridgeport, CT", "Bridgeport"],
    ["Islip, NY", "Islip"],
    ["John F. Kennedy International Airport", "Kennedy Arpt"],
    ["La Guardia Airport", "La Guardia Apt"],
    ["Newark, NJ", "Newark"],
    ["Teterboro, NJ", "Teterboro"],
    ["Westchester County, NY", "Westchester Co"]
]

outputs = None
extensions = []

crawls = []

extraldltext = ""

#############

framerate = 60

crawlintervaltime = 15*minutes
crawlinterval = crawlintervaltime*1

forever = False

schedule = []

sm2 = True

compress = False

jr = True

radarint = 0.26
radarhold = 2.74

ldllf = False

adevice = None

vencoder = "libx264"

tcflocs = [
    ("Atlanta, GA", "Atlanta"),
    ("Boston, MA", "Boston"),
    ("Chicago, IL", "Chicago"),
    ("Cleveland, OH", "Cleveland"),
    ("Dallas, TX", "Dallas"),
    ("Denver, CO", "Denver"),
    ("Detroit, MI", "Detroit"),
    ("Hartford, CT", "Hartford"),
    ("Houston, TX", "Houston"),
    ("Indianapolis, IN", "Indianapolis"),
    ("Los Angeles, CA", "Los Angeles"),
    ("Miami, FL", "Miami"),
    ("Minneapolis, MN", "Minneapolis"),
    ("New York, NY", "New York"),
    ("Norfolk, VA", "Norfolk"),
    ("Orlando, FL", "Orlando"),
    ("Philadelphia, PA", "Philadelphia"),
    ("Pittsburgh, PA", "Pittsburgh"),
    ("St. Louis, MO", "St. Louis"),
    ("San Francisco, CA", "San Francisco"),
    ("Seattle, WA", "Seattle"),
    ("Syracuse, NY", "Syracuse"),
    ("Tampa, FL", "Tampa"),
    ("Washington DC", "Washington DC")
]
tcflocs = [[*e, None, None] for e in tcflocs]

mute = False

crawllen = 40

try:
    import conf
    #you can sorta tell what order we implemented these in
    textpos = conf.textpos
    timedrawing = conf.timedrawing
    ldldrawing = conf.ldldrawing
    veryuppercase = conf.veryuppercase
    pressuretrend = conf.pressuretrend
    loc = conf.mainloc
    locname = conf.mainloc2
    flavor = conf.flavor
    flavor_times = conf.flavor_times
    flavor_un = [(f, flavor_times[i]) for i, f in enumerate(flavor) if not f.startswith("disabled")]
    flavor = [f[0] for f in flavor_un]
    flavor_times = [f[1] for f in flavor_un]
    musicpath = conf.musicdir
    afos_climate = conf.mesoid
    extraldltext = conf.extra
    crawlintervaltime = [15*minutes, 30*minutes, 1*hours, 2*hours, 3*hours, 4*hours, 6*hours, 8*hours, 12*hours, 24*hours][conf.crawlint]
    crawlinterval = crawlintervaltime*1
    crawls = [c[0] for c in conf.crawls if (c[1] and c[0])]

    lsort = getattr(conf, "lsort", False)
    obsloc = [o for o in conf.obsloc if o[0] and o[1]]
    if lsort:
        obsloc = sorted(obsloc, key=lambda o : o[1])
    rl = getattr(conf, "reglocs", [])
    rn = getattr(conf, "regnames", [])
    reglocs = [[rl[i], rn[i], None, None] for i in range(min(len(rl), len(rn)))]
    ldlfeed = conf.ldlfeed
    ldlbg = conf.ldlbg
    old = conf.old
    ldlmode = conf.ldlmode
    forever = conf.forever
    foreverldl = conf.foreverldl
    schedule = conf.schedule
    sm2 = conf.aspect
    smode = conf.smode
    radarint = conf.radarint
    radarhold = conf.radarhold
    ldllf = conf.ldllf
    efname = conf.efname
    mainlogo = conf.mainlogo
    radarlogo = conf.radarlogo
    extensions = conf.extensions
    adevice = conf.audiodevice
    borderless = conf.borderless
    vencoder = conf.vencoder
    mute = conf.mute
    widescreen = conf.widescreen
    #all of these were added after release, so i actually have to check for them. fun!
    compress = getattr(conf, "compress", False)
    radarsetting = getattr(conf, "radarsetting", False)
    lfmusic = getattr(conf, "musicsetting", 0)
    smoothscale = getattr(conf, "smoothscale", True)
    crawllen = getattr(conf, "crawllen", 40)
    tidal = getattr(conf, "tidal", ("", "", "", ""))
    framerate = getattr(conf, "framerate", 60)
    efullscreen = getattr(conf, "efullscreen", False)
except ModuleNotFoundError:
    print("Configuration not found! Try saving your configuration again.")
    exit(1)
os.chdir(os.path.dirname(os.path.abspath(__file__))) #do this or everything explodes
if not mute:
    pg.mixer.init(audiorate, devicename=(adevice if adevice != "Default" else None))

colorbug_started = False
colorbug_nat = (flavor[-1] in ["lr", "cr"])

temp_symbol = "F"
speed_unit = "MPH"
long_dist = "mi."
short_dist = "ft."

screenw = 768 if not widescreen else 1024

win = pg.Surface((screenw, 480))
rwidth = screenw if not compress else int(screenw//1.2)
if efullscreen:
    info = pg.display.Info()
    w, h = info.current_w, info.current_h
    rwin = pg.display.set_mode((w, h), pg.FULLSCREEN)
else:
    rwin = pg.display.set_mode((rwidth, 480), flags=(borderless*pg.NOFRAME)|pg.RESIZABLE)

pg.display.set_caption(f"FreeStar 4000 v{VERSION}")
icon = pg.image.load("assets/mwsicon.png")
pg.display.set_icon(icon)

ldlfeedactive = (ldlfeed is not None and ldlfeed)

avscale = (640 if not widescreen else 853, 480)

showing = 0

#4000 colors
_gray = [104, 104, 104]
_smptewhite = [180, 180, 180]
_yellow = [180, 180, 16]
_cyan = [16, 180, 180]
_green = [16, 180, 16]
_magenta = [180, 16, 180]
_red = [180, 16, 16]
_blue = [16, 16, 180]
_black = [16, 16, 16]
_white = [235, 235, 235]

test_grad = [_yellow, _white, _black, _blue, _red, _magenta, _green, _cyan, _yellow, _white, _white]

for l in obsloc:
    l.append(None)

#theme
bg_c = [(64, 33, 98),  (80, 39, 88), (98, 47, 75), (117, 55, 62), (134, 62, 51), (153, 70, 38), (168, 77, 28), (184, 83, 17), (209, 94, 0)]
ban_c = [(209, 94, 0), (184, 83, 17), (168, 77, 28), (153, 70, 38), (117, 55, 62), (98, 47, 75), (80, 39, 88), (64, 33, 98)]
ban_c = list(reversed(bg_c))
box_c = [(60, 104, 192), (52, 88, 168), (48, 72, 140), (40, 56, 112), (40, 44, 96)]
tcf_c = [(22, 59, 133), (18, 47, 119), (13, 35, 105), (9, 24, 92), (4, 12, 78), (4, 12, 78), (4, 12, 78), (9, 24, 92), (13, 35, 105), (18, 47, 119), (22, 59, 133)]
tcf_bg = draw_palette_gradient(pg.Rect(0, 0, screenw, 72*4), tcf_c)
ldl_c = (40, 56, 112)
outer_c = (44, 24, 112)

bg_g = draw_palette_gradient(pg.Rect(0, 0, screenw, 315), [*bg_c, bg_c[-1]])
al_g = draw_palette_gradient(pg.Rect(0, 0, screenw, 96), bg_c)

alertdata = [None, []]
alertactive = 0

mainicon = pg.image.load_animation("icons/icons_cc/Partly-Cloudy.gif")
ldllficon = pg.image.load_animation("icons/icons_reg/Partly-Cloudy.gif")
xficons = [None, None, None, None, None, None]

regmap = pg.image.load("assets/regmap.png")
regmapcut = pg.Surface((screenw, 480), pg.SRCALPHA)
regmapcut.fill(_gray)

radardata = None

radar_provider = "apollo"

if "al" in flavor:
    import moon_calc

import traceback as tb

dficons = [[] for _ in range(12)]

#commercial pre-roll, commercial on-air, unused, warning, unused
switches = [False, False, False, False, False] #this emulates the 4000's logic switches. why? as baldi once said, historicality

connections = []

regmappos = ()

# Load fonts
smallfont = pg.font.Font("fonts/Small.ttf", 32)
largefont32 = pg.font.Font("fonts/Large.ttf", 33)
startitlefont = pg.font.Font("fonts/Main.ttf", 33)
starfont32 = pg.font.Font("fonts/Main.ttf", 34)
extendedfont = pg.font.Font("fonts/Extended.ttf", 33)

font_tallest = {largefont32: 0, smallfont: 0, starfont32: 0}
for char in "qwertyuiopasdfghjklzxcvbnm1234567890QWERTYUIOPASDFGHJKLZXCVBNM-":
    c = largefont32.size(char)[1]
    if c > font_tallest[largefont32]:
        font_tallest[largefont32] = c
for char in "qwertyuiopasdfghjklzxcvbnm1234567890QWERTYUIOPASDFGHJKLZXCVBNM-":
    c = smallfont.size(char)[1]
    if c > font_tallest[smallfont]:
        font_tallest[smallfont] = c
for char in "qwertyuiopasdfghjklzxcvbnm1234567890QWERTYUIOPASDFGHJKLZXCVBNM-":
    c = starfont32.size(char)[1]
    if c > font_tallest[starfont32]:
        font_tallest[starfont32] = c

# Load JR fonts
jrfontnormal, jrwidthsnormal, jroffsetsnormal = loadjrfont("normal")

jrfontradaralert, _, _ = loadjrfont("normal")
jrfontradaralert[0].fill((198, 178, 154, 255), special_flags=pg.BLEND_RGBA_MULT)
jrfontradaralert[1].fill((4, 68, 4, 0), special_flags=pg.BLEND_RGBA_ADD)

jrfonticon, jrwidthsison, jroffsetsicon = loadjrfont("icon")
jrfontsmall, jrwidthssmall, jroffsetssmall = loadjrfont("small")
jrfonttall, jrwidthstall, jroffsetstall = loadjrfont("tall")
jrfontsymbol, _, _ = loadjrfont("symbol")
jrfonttravel, jrwidthstravel, jroffsetstravel = loadjrfont("travel")

white = (215, 215, 215)
yeller = (187, 182, 45)
gmono = 18.15
linespacing = 40.25

# Initialize drawing module
draw_mod.init(
    win=win, screenw=screenw, jr=jr, widescreen=widescreen, old=old,
    bg_c=bg_c, ban_c=ban_c, box_c=box_c, bg_g=bg_g, al_g=al_g, ldl_c=ldl_c, outer_c=outer_c,
    smallfont=smallfont, largefont32=largefont32, startitlefont=startitlefont,
    starfont32=starfont32, extendedfont=extendedfont,
    jrfontnormal=jrfontnormal, jrfontsmall=jrfontsmall, jrfonticon=jrfonticon,
    jrfonttravel=jrfonttravel, jrfontsymbol=jrfontsymbol, jrfonttall=jrfonttall,
    jrfontradaralert=jrfontradaralert,
    font_tallest=font_tallest,
)

if ldlbg:
    ws2 = pg.image.load(ldlbg)
else:
    ws2 = pg.Surface((1, 1), pg.SRCALPHA)

noaa = pg.image.load("assets/noaa.gif").convert_alpha()

logo = pg.image.load(mainlogo)
logorad = pg.image.load(radarlogo)

logorad = pg.transform.scale(logorad, (768, 480))

ui = True

ldl_y = 0
if textpos >= 2:
    ldl_y = -16

ldlreps = 0

bbox = (-127.680, 21.649, -66.507, 50.434)
mappoint1 = [(bbox[3], bbox[0]), (-screenw//4, -120)]
mappoint2 = [(bbox[1], bbox[2]), (4100-screenw//4, 1920-120)]

rmappoint1 = [(bbox[3], bbox[0]), (-screenw//2, -240)]
rmappoint2 = [(bbox[1], bbox[2]), (4100-screenw//2, 1920-240)]

radartime = radarhold+radarint*6

# Initialize resources module
res.init(
    loc=loc, flavor=flavor, afos_climate=afos_climate,
    tidal=tidal, radar_provider=radar_provider, screenw=screenw,
    obsloc=obsloc, reglocs=reglocs, tcflocs=tcflocs,
    dficons=dficons, connections=connections,
    mainicon=mainicon, ldllficon=ldllficon,
    regmap=regmap, regmapcut=regmapcut,
    mappoint1=mappoint1, mappoint2=mappoint2,
    rmappoint1=rmappoint1, rmappoint2=rmappoint2,
    xficons=xficons,
    mute=mute, ldlfeedactive=ldlfeedactive, ldlfeed=ldlfeed,
    smode=smode, sm2=sm2, lfmusic=lfmusic,
    audiorate=audiorate, framerate=framerate, vencoder=vencoder, avscale=avscale
)

wxdata = None
clidata = None
aldata = {"sun": {}, "moon": [], "tidal": [None, None]}

# Start data thread
th.Thread(target=res.getdata, daemon=True).start()

musicfiles = []
if musicpath:
    for file in os.listdir(musicpath):
        if file.endswith((".mp3", ".wav", ".flac", ".xm", ".mod", ".ogg")) and not file.startswith("."):
            musicfiles.append(os.path.join(musicpath, file))

crawling = False

ldlon = not not foreverldl

crawlactive = 0
crawlscroll = 0

crawltime = 60*40
ldlidx = 0
ldlintervaltime = 4*seconds
ldlinterval = ldlintervaltime*1
slideinterval = flavor_times[0]*seconds
slideidx = 0

cl = pg.time.Clock()
lastlasttime = 0
lasttime = 0
ldldrawidx = 0
generaldrawidx = 0

slide = "cc"

noreport = [
    "",
    "",
    "       No Report Available"
]

nextcrawlready = False

quit_requested = False

if mute:
    musicch = None
    voicech = None
    beepch = None
else:
    musicch = pg.mixer.Channel(0)
    voicech = pg.mixer.Channel(1)
    beepch = pg.mixer.Channel(2)

if not mute:
    beep = pg.Sound("assets/beep.ogg")
radarx = ['', '99'][radarsetting]
radarHeader = pg.transform.scale(pg.image.load(f"assets/radar{radarx}.png"), (768, 480))
radarHeaderC = pg.transform.scale(pg.image.load(f"assets/radarc{radarx}.png"), (768, 480))
if screenw > 768:
    radarLeft = pg.transform.scale(radarHeader.subsurface(pg.Rect(0, 0, 1, radarHeader.get_height())), (m.ceil((screenw-768)/2), radarHeader.get_height()))
    radarRight = pg.transform.scale(radarHeader.subsurface(pg.Rect(radarHeader.get_width()-1, 0, 1, radarHeader.get_height())), (m.ceil((screenw-768)/2), radarHeader.get_height()))
if screenw > 768:
    radarLeftC = pg.transform.scale(radarHeaderC.subsurface(pg.Rect(0, 0, 1, radarHeaderC.get_height())), (m.ceil((screenw-768)/2), radarHeaderC.get_height()))
    radarRightC = pg.transform.scale(radarHeaderC.subsurface(pg.Rect(radarHeaderC.get_width()-1, 0, 1, radarHeaderC.get_height())), (m.ceil((screenw-768)/2), radarHeaderC.get_height()))

latestframe = pg.Surface((1, 1))
vidcap = None

moon_full = pg.image.load("assets/moon/Full-Moon.gif").convert_alpha()
moon_lq = pg.image.load("assets/moon/Last-Quarter.gif").convert_alpha()
moon_fq = pg.image.load("assets/moon/First-Quarter.gif").convert_alpha()
moon_new = pg.image.load("assets/moon/New-Moon.gif").convert_alpha()

# Set up music
res.musicfiles = musicfiles
res.musicch = musicch
res.ldlmode = ldlmode

import queue as q
audio_queue = q.Queue()

capframes = []

frame_idx_actual = 0
p_counter = 0

def domusic():
    if mute: return
    mus = None
    last = ""
    while True:
        musicon = True
        if ldlmode and lfmusic:
            musicon = False
        if musicon:
            if not musicch.get_busy():
                allowed_this_time = musicfiles.copy()
                if (len(musicfiles) > 1) and last:
                    allowed_this_time.remove(last)
                last = rd.choice(allowed_this_time)
                mus = pg.mixer.Sound(last)
                musicch.play(mus)
        else:
            musicch.stop()
        tm.sleep(0.02)

if musicpath:
    th.Thread(target=domusic, daemon=True).start()

xfbg = pg.image.load("assets/xfbg.png")

subpage = 0

testmov = 0

iconidx = 0
iconidx2 = 0
iconidx3 = 0

working = True
cl = AccurateClock()

serial = False
fired = False
diag = [0, tm.perf_counter()]
alerting = False
txoff = (screenw-768)//2
with open("introtext.txt") as f:
    intros = f.read().strip().rstrip().split("\n")

while working:
    for event in pg.event.get():
        if event.type == pg.MOUSEBUTTONDOWN:
            showing += 1
            showing %= 2
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_s:
                pg.image.save(win, "screenshot.png")
                pg.image.save(pg.transform.smoothscale_by(win, (1/1.2, 1)), "screenshot_scaled.png")
                continue
            elif event.key == pg.K_j:
                cl.drift = 0
            elif event.key == pg.K_ESCAPE:
                working = False
            elif event.key == pg.K_u:
                veryuppercase = not veryuppercase
            elif event.key == pg.K_t:
                textpos += 1
                textpos %= 4
            elif event.key == pg.K_F3:
                serial = not serial
            else:
                #ui = not ui
                pass
        elif event.type == pg.QUIT:
            working = False
    if not ldlmode:
        colorbug_started = True
    if schedule:
        mn = int(dt.datetime.now().strftime("%M"))
        if mn not in schedule:
            fired = False
        if not fired and mn in schedule:
            fired = True
            ldlmode = False
    your = "Your " if ("oldtitles" in old and (textpos > 1 or widescreen)) else ""
    delta = cl.tick(framerate) / 1000

    radartime -= delta
    if radartime < 0:
        radartime = radarint*6 + radarhold
    if radartime > radarint*6:
        radaridx = 0
    else:
        radaridx = m.ceil(6-radartime/radarint)

    if slide != "intro":
        intropicked = False

    # Sync shared state from resources module
    wxdata = res.wxdata
    clidata = res.clidata
    alertdata = res.alertdata
    mainicon = res.mainicon if res.mainicon else mainicon
    ldllficon = res.ldllficon if res.ldllficon else ldllficon
    radardata = res.radardata
    aldata = res.aldata
    dficons = res.dficons
    regmapcut = res.regmapcut
    regmappos = res.regmappos
    xficons = res.xficons
    latestframe = res.latestframe if res.latestframe else latestframe
    res.ldlmode = ldlmode

    def nextslide():
        global slideinterval
        global slideidx
        global ldlmode
        global bg_g
        global radartime
        global crawling
        global ldlon
        global generaldrawidx
        generaldrawidx = 0
        radartime = radarint*6 + radarhold
        slideidx += 1
        bg_g = draw_palette_gradient(pg.Rect(0, 0, screenw, 315), [*bg_c, bg_c[-1]])
        draw_mod.bg_g = bg_g
        if forever:
            slideidx %= len(flavor)
            slideinterval = flavor_times[slideidx]*seconds
        else:
            if slideidx >= len(flavor):
                ldlmode = True
                crawling = False
                if not foreverldl:
                    ldlon = False
                slideidx = 0
                slideinterval = flavor_times[0]*seconds
            else:
                slideinterval = flavor_times[slideidx]*seconds
    if slideinterval <= 0 and not ldlmode:
        if slide in ["lf", "df"]:
            subpage += 1
            if subpage > 2:
                subpage = 0
                nextslide()
            else:
                slideinterval = flavor_times[slideidx]*seconds
        else:
            nextslide()
    elif ldlmode:
        pass
    else:
        slideinterval -= delta*seconds

    slide = flavor[slideidx]

    if slide == "intro" and not intropicked:
        introtx = rd.choice(intros)
        intropicked = True

    try:
        sanitize = (lambda tx : tx.replace("in the Vicinity", "Near").replace("Thunderstorm", "T'Storm"))
        ccphrase = sanitize(wxdata["current"]["info"]["phraseLong"])
        if len(ccphrase) > len(" Partly Cloudy "): #sorry i had no better text reference
            ccphrase = sanitize(wxdata["current"]["info"]["phraseMedium"])
            if len(ccphrase) > len(" Partly Cloudy "):
                ccphrase = sanitize(wxdata["current"]["info"]["phraseShort"])
    except:
        ccphrase = ""

    iconidx += 0.125*delta*seconds
    iconidx %= len(mainicon)
    iconidx3 += 0.125*delta*seconds
    iconidx3 %= 7
    crawlinterval -= delta * seconds
    profiling_start()
    if crawlinterval <= 0 and nextcrawlready and crawls:
        crawlactive += 1
        crawlinterval = crawlintervaltime*1
    if crawls:
        crawlactive %= len(crawls)
    if not working or quit_requested:
        pg.quit()
        break
    ao = 0
    if textpos >= 2:
        ao = 16
    ldl_y = 0
    if textpos >= 2:
        ldl_y = -16
    draw_mod.ldl_y = ldl_y
    if ldlmode:
        win.fill((255, 0, 255))
        win.blit(ws2, (0, 0))
    else:
        if (slide == "oldcc"):
            draw_bg(top_offset=(192*("fullOldCC" not in old)), all_offset=ao, bh_offset=ao//2)
        else:
            spec = ["al", "df"]
            draw_bg(all_offset=ao, bh_offset=ao//2, special=(slide if slide in spec else None), box=(slide != "xf"))
            if slide == "xf":
                for i in range(3+widescreen):
                    win.blit(xfbg, (46+230*i+13*widescreen, 101-round(ao*1.5)))
    profiling_end("ops")

    if ui and not ldlmode:
        if slide in ["cc", "oldcc"]:
            if slide == "oldcc":
                if True:
                    ln = f"Now at {locname}"
                    if veryuppercase:
                        ln = ln.upper()
                    drawshadow(startitlefont, ln, 194+txoff//3, 30, 3, mono=18, ofw=1.07)
                if wxdata is None:
                    if veryuppercase:
                        drawpage(["No Current Report"])
                    else:
                        drawshadow(starfont32, "       No Report Available", 80+txoff, 109+linespacing*2.5+ldl_y, 3, mono=gmono)
                else:
                    page = [
                        ccphrase
                    ]
                    if wxdata["current"]["conditions"]["feelsLike"] == wxdata["current"]["conditions"]["temperature"]:
                        additional = ""
                    elif wxdata["current"]["conditions"]["feelsLike"] < wxdata["current"]["conditions"]["temperature"]:
                        additional = "               Wind Chill:"
                        additional += (padtext(wxdata["current"]["conditions"]["feelsLike"], 3) + "°"+temp_symbol)
                    else:
                        additional = "               Heat Index:"
                        additional += (padtext(wxdata["current"]["conditions"]["feelsLike"], 3) + "°"+temp_symbol)
                    page.append(textmerge(f'Temp:{padtext(wxdata["current"]["conditions"]["temperature"], 3)}°'+temp_symbol,
                                        additional))
                    page.append(textmerge(f'Humidity: {wxdata["current"]["conditions"]["humidity"]}%',
                                    f'                 Dewpoint:{padtext(wxdata["current"]["conditions"]["dewPoint"], 3)}°'+temp_symbol))

                    bp = f'{wxdata["current"]["conditions"]["pressure"]:5.2f}'
                    bptext = f'Barometric Pressure: {bp}'
                    pt = wxdata["current"]["conditions"]["pressureTendency"]
                    if pressuretrend == False:
                        bptext += " in."
                    elif pt == 0:
                        bptext += " S"
                    elif pt in [1, 3]:
                        bptext += " R"
                    elif pt in [2, 4]:
                        bptext += " F"
                    page.append(bptext)

                    wndtext = textmerge(f'Wind: {padtext(wxdata["current"]["conditions"]["windCardinal"], 3)}',
                                    f'          {wxdata["current"]["conditions"]["windSpeed"]} {speed_unit}')
                    if wxdata["current"]["conditions"]["windSpeed"] == 0:
                        wndtext = "Wind: Calm"

                    if wxdata["current"]["conditions"]["windGusts"] is not None:
                        wndtext = textmerge(wndtext, f'                  Gusts to  {wxdata["current"]["conditions"]["windGusts"]}')
                    page.append(wndtext)

                    ceil = f':{padtext(wxdata["current"]["conditions"]["cloudCeiling"], 5)}{short_dist}'
                    if wxdata["current"]["conditions"]["cloudCeiling"] is None:
                        ceil = " Unlimited"
                        if "ceiling_colon" in old:
                            ceil = ":" + ceil[1:]
                    else:
                        ceil = padtext(f'{wxdata["current"]["conditions"]["cloudCeiling"]} {short_dist}', 10)
                    cltext = f'Visib:  {padtext(int(wxdata["current"]["conditions"]["visibility"]), 2)} {long_dist} Ceiling' + ceil
                    page.append(cltext)

                    if veryuppercase:
                        page = [p.upper() for p in page]
                    drawpage(page)

            else:
                if textpos >= 2:
                    ln = f"Now at {locname}"
                    if veryuppercase:
                        ln = ln.upper()
                    drawshadow(startitlefont, ln, 194+txoff//3, 46+ldl_y, 3, mono=18, ofw=1.07, upper=veryuppercase)
                else:
                    drawshadow(startitlefont, "Current", 194+txoff//3, 25+ldl_y, 3, color=yeller, mono=18, ofw=1.07, bs=True, upper=veryuppercase)
                    drawshadow(startitlefont, "Conditions", 194+txoff//3, 52+ldl_y, 3, color=yeller, mono=18, ofw=1.07, bs=True, upper=veryuppercase)

                if not wxdata:
                    drawshadow(starfont32, "       No Report Available", 80+txoff, 109+linespacing*2.5, 3, mono=gmono)
                else:
                    drawshadow(starfont32, locname, 367+txoff, 91+ldl_y, 3, color=yeller, ofw=1.07, mono=15, upper=veryuppercase)

                    drawshadow(starfont32, "Humidity:", 394+txoff, 133+ldl_y, 3, ofw=1.07, mono=15, upper=veryuppercase)
                    drawshadow(starfont32, f"{padtext(wxdata['current']['conditions']['humidity'], 3)}%", 576+txoff, 133+ldl_y, 3, mono=19, upper=veryuppercase)

                    drawshadow(starfont32, "Dewpoint:", 394+txoff, 176+ldl_y, 3, ofw=1.07, mono=15, upper=veryuppercase)
                    drawshadow(starfont32, f"{padtext(wxdata['current']['conditions']['dewPoint'], 3)}°", 576+txoff, 176+ldl_y, 3, mono=19, upper=veryuppercase)

                    drawshadow(starfont32, "Ceiling:", 394+txoff, 219+ldl_y, 3, ofw=1.07, mono=14.5, upper=veryuppercase)

                    if wxdata["current"]["conditions"]["cloudCeiling"] is None:
                        drawshadow(starfont32, "Unlimited", 519+txoff, 219+ldl_y, 3, ofw=1.07, mono=14.5, upper=veryuppercase, char_offsets={})
                    else:
                        ceil = padtext(f'{wxdata["current"]["conditions"]["cloudCeiling"]}{short_dist}', 9)
                        drawshadow(starfont32, ceil, 526+txoff, 219+ldl_y, 3, ofw=1.07, mono=14.5, upper=veryuppercase, char_offsets={})

                    drawshadow(starfont32, "Visibility:", 394+txoff, 261+ldl_y, 3, ofw=1.07, mono=14.5, upper=veryuppercase)
                    drawshadow(starfont32, f"  {padtext(round(wxdata['current']['conditions']['visibility']), 2)}{long_dist}", 540+txoff, 261+ldl_y, 3, mono=17.5, upper=veryuppercase)

                    bp = f'{wxdata["current"]["conditions"]["pressure"]:5.2f}'
                    drawshadow(starfont32, "Pressure :" if "ccspace" in old else "Pressure:", 394+txoff, 304+ldl_y, 3, ofw=1.07, mono=14.5, upper=veryuppercase)
                    drawshadow(starfont32, bp, 537+txoff, 304+ldl_y, 3, mono=18, char_offsets={}, upper=veryuppercase)
                    pt = wxdata["current"]["conditions"]["pressureTendency"]
                    if pt == 0:
                        drawshadow(starfont32, f"     S", 543+txoff, 304+ldl_y, 3, mono=18, color=yeller, char_offsets={}, upper=veryuppercase)
                    elif pt in [1, 3]:
                        drawshadow(starfont32, f"     ↑", 543+txoff, 304+ldl_y, 3, mono=18, color=yeller, char_offsets={}, upper=veryuppercase, jr_override=jrfontsymbol)
                    elif pt in [2, 4]:
                        drawshadow(starfont32, f"     ↓", 543+txoff, 304+ldl_y, 3, mono=18, color=yeller, char_offsets={}, upper=veryuppercase, jr_override=jrfontsymbol)

                    if wxdata["current"]["conditions"]["feelsLike"] == wxdata["current"]["conditions"]["temperature"]:
                        additional = ""
                    elif wxdata["current"]["conditions"]["feelsLike"] < wxdata["current"]["conditions"]["temperature"]:
                        additional = "Wind Chill:"
                    else:
                        additional = ""
                    if additional:
                        drawshadow(starfont32, additional, 394+txoff, 347+ldl_y, 3, ofw=1.07, mono=15, upper=veryuppercase)
                        drawshadow(starfont32, f"{padtext(wxdata['current']['conditions']['feelsLike'], 3)}°", 576+txoff, 347+ldl_y, 3, mono=19, upper=veryuppercase)

                    drawshadow(largefont32, f"{padtext(wxdata['current']['conditions']['temperature'], 3)}°", 170+txoff, 99+ldl_y, 3, ofw=1.125, mono=22.1, char_offsets={}, upper=veryuppercase)


                    mm = pg.transform.smoothscale_by(mainicon[m.floor(iconidx) % len(mainicon)][0], (1.2, 1))
                    ioff = (0, 0)
                    if icontable[wxdata['current']['info']['iconCode']] in icon_offset:
                        ioff = icon_offset[icontable[wxdata['current']['info']['iconCode']]]
                    win.blit(mm, (220-mm.width//2+ioff[0]+txoff, 215-mm.height//2+ioff[1]+ldl_y))
                    del mm

                    cctx = ccphrase
                    drawshadow(extendedfont, cctx, 168-18*(len(cctx)/2-2)+9+txoff, 139+ldl_y, 3, ofw=1.1, mono=18.9, char_offsets={":": 2, "i":2}, upper=veryuppercase)
                    if wxdata["current"]["conditions"]["windSpeed"] == 0:
                        drawshadow(extendedfont, f"Wind: Calm", 95+txoff, 303+ldl_y, 3, ofw=1.1, mono=18.9, char_offsets={":": 2, "i":2}, upper=veryuppercase)
                    else:
                        drawshadow(extendedfont, f"Wind: {padtext(wxdata['current']['conditions']['windCardinal'], 3)}  {padtext(wxdata['current']['conditions']['windSpeed'], 2)}", 95+txoff, 303+ldl_y, 3, ofw=1.1, mono=19, char_offsets={":": -3}, upper=veryuppercase)
                    if wxdata['current']['conditions']['windGusts'] is not None:
                        drawshadow(extendedfont, f"Gusts to", 95+txoff, 345+ldl_y, 3, ofw=1, mono=18.9, char_offsets={"u": 3, "s": 2}, upper=veryuppercase)
                        drawshadow(extendedfont, padtext(wxdata['current']['conditions']['windGusts'], 2), 272+txoff, 345+ldl_y, 3, ofw=1.1, mono=24, char_offsets={}, upper=veryuppercase)

        elif slide == "lo":
            drawshadow(startitlefont, "Latest Observations", 181+txoff//3, 39+ldl_y, 3, color=yeller, mono=15.5, ofw=1.07, bs=True, upper=veryuppercase)
            page = []
            for l in obsloc:
                if l[2] == None:
                    page.append(textmerge(l[1], "                  No Report"))
                else:
                    ol = textmerge(l[1], f"              {padtext(l[2]['current']['conditions']['temperature'], 3)} {shorten_phrase(l[2]['current']['info']['phraseShort'])}")
                    ws = l[2]['current']['conditions']['windSpeed']
                    if ws > 9:
                        ol = textmerge(ol, f"                            {windreduce(l[2]['current']['conditions']['windCardinal'])}")
                        page.append(textmerge(ol, f"                              {ws}"))
                    elif ws == 0:
                        page.append(textmerge(ol, f"                            Calm"))
                    else:
                        ol = textmerge(ol, f"                            {l[2]['current']['conditions']['windCardinal']}")
                        page.append(textmerge(ol, f"                               {ws}"))

            if veryuppercase:
                page = [p.upper() for p in page]
            drawpage2(page, f"               °{temp_symbol} WEATHER   WIND")
        elif slide == "oldro":
            drawshadow(startitlefont, your+"Latest Observations", 181, 39+ldl_y, 3, color=yeller, mono=15.5, ofw=1.07, bs=True, upper=veryuppercase)
            drawpage(["Cincinnati Apt 63 Cloudy    S 23",
                    "Birmingham     63 T'Storm     16",
                    "Mobile         74 Cloudy      24",
                    "Montgomery     67 Fair        10",
                    "New Orleans    75 Cloudy      13",
                    "Panama City    70 Fair        10",
                    "Pensacola Arpt 73 P Cloudy    23"],
                    f"                    WEATHER   °{temp_symbol}")
        elif slide == "lf":
            drawshadow(startitlefont, your+"Local Forecast", 181+txoff//3, 39+ldl_y, 3, color=yeller, mono=15.5, ofw=1.07, bs=True, upper=veryuppercase)

            alert36 = False
            allines = []

            alerts = []
            for alert in alertdata[1]:
                if alert[1] != "W":
                    alert36 = True
                    alerts.append(alert)

            finallines = []
            for alert in alerts:
                allines = [lin.strip().rstrip() for lin in wraptext(alert[0].upper(), 30)]
                for line in allines:
                    finallines.append(
                        textmerge("*"+30*" "+"*", m.ceil(16-len(line)/2)*" "+line)
                    )
                finallines.append("\n")

                break

            if wxdata:
                if not alert36:
                    fcsts = wxdata["extended"]["daypart"]
                    text = (fcsts[subpage]["name"][0].upper() + fcsts[subpage]["name"][1:].lower()) + "..." + fcsts[subpage]["narration"]
                    if veryuppercase:
                        text = text.upper()

                    drawpage(wraptext(text))
                else:
                    fcsts = wxdata["extended"]["daypart"]

                    textix = 0

                    texts = []

                    clear = False
                    squeeze = False

                    for textixx in range(4):
                        texts.append(wraptext((fcsts[textixx]["name"][0].upper() + fcsts[textixx]["name"][1:].lower()) + "..." + fcsts[textixx]["narration"]))
                        if veryuppercase:
                            texts[-1] = texts[-1].upper()
                    def build36(squ):
                        global textix, texts
                        all_lines = finallines.copy()
                        while True:
                            if len(all_lines) >= 21:
                                return all_lines, True
                            if len(all_lines) >= 14 and textix > 2:
                                return all_lines, True

                            if len(all_lines) % 7 == 0:
                                for line in texts[-1]:
                                    all_lines.append(line)
                                textix += 1

                            elif len(all_lines) + len(texts[textix]) <= 21:
                                for line in texts[textix]:
                                    all_lines.append(line)
                                textix += 1
                                if len(all_lines) % 7 != 0 and not squ:
                                    all_lines.append("\n")
                            elif len(all_lines) + 1 <= 21:
                                all_lines.append((fcsts[textix]["name"][0].upper() + fcsts[textix]["name"][1:].lower()) + "...")
                                return all_lines, False

                    all_lines, sq = build36(False)
                    if not sq:
                        textix = 0
                        a2, sq2 = build36(True)
                        if sq2:
                            all_lines = a2


                    drawpage(all_lines[(subpage*7):])
        elif slide == "lr":
            if radardata:
                win.blit(radardata[radaridx][0], (0, 0))
            if screenw > 768:
                win.blit(radarLeft, (0, 0))
                win.blit(radarRight, (screenw-radarRight.get_width(), 0))
            win.blit(radarHeader, (screenw//2 - radarHeader.get_width()//2, 0))
            win.blit(logorad, (screenw//2 - radarHeader.get_width()//2, 0))
        elif slide == "cr":
            if radardata:
                win.blit(radardata[0][0], (0, 0))
            if screenw > 768:
                win.blit(radarLeftC, (0, 0))
                win.blit(radarRightC, (screenw-radarRightC.get_width(), 0))
            win.blit(radarHeaderC, (screenw//2 - radarHeaderC.get_width()//2, 0))
            win.blit(logorad, (screenw//2 - radarHeaderC.get_width()//2, 0))
        elif slide == "al":
            def supper(text):
                if "uppercaseAMPM" in old:
                    return text.upper()
                return text
            drawshadow(startitlefont, "Almanac", 181+txoff//3, 39+ldl_y, 3, color=yeller, mono=18, ofw=1.07, bs=True, upper=veryuppercase)
            if aldata["sun"]:
                drawshadow(starfont32, "Sunrise:", 76+txoff, 114+ldl_y, 3, mono=gmono, char_offsets={})
                drawshadow(starfont32, " Sunset:", 76+txoff, 144+ldl_y, 3, mono=gmono, char_offsets={})

                d1 = dt.date.today().strftime("%A")
                drawshadow(starfont32, d1, 286+18*4.5-len(d1)*18/2+txoff, 85+ldl_y, 3, mono=gmono, char_offsets={}, color=yeller)
                d2 = ( dt.date.today()+dt.timedelta(days=1)).strftime("%A")
                drawshadow(starfont32, d2, 213+286+18*4.5-len(d2)*18/2+txoff, 85+ldl_y, 3, mono=gmono, char_offsets={}, color=yeller)

                sunrise1 = dt.datetime.fromtimestamp(aldata["sun"]["sunrise1"])
                sunset1 = dt.datetime.fromtimestamp(aldata["sun"]["sunset1"])
                sunrise2 = dt.datetime.fromtimestamp(aldata["sun"]["sunrise2"])
                sunset2 = dt.datetime.fromtimestamp(aldata["sun"]["sunset2"])

                drawshadow(starfont32, supper(splubby_the_return(sunrise1.strftime("%I:%M %p"))), 305+txoff, 114+ldl_y, 3, mono=gmono, char_offsets={})
                drawshadow(starfont32, supper(splubby_the_return(sunset1.strftime("%I:%M %p"))), 305+txoff, 144+ldl_y, 3, mono=gmono, char_offsets={})

                drawshadow(starfont32, supper(splubby_the_return(sunrise2.strftime("%I:%M %p"))), 518+txoff, 114+ldl_y, 3, mono=gmono, char_offsets={})
                drawshadow(starfont32, supper(splubby_the_return(sunset2.strftime("%I:%M %p"))), 518+txoff, 144+ldl_y, 3, mono=gmono, char_offsets={})
            if aldata["moon"]:
                drawshadow(starfont32, "Moon Data:", 76+txoff, 191+ldl_y, 3, mono=gmono, char_offsets={}, color=yeller)
                for i in range(4):
                    moondt = aldata["moon"][i]
                    mt = moondt[0]
                    xx = i*151
                    drawshadow(starfont32, mt, 112+18*1.5-len(mt)*9+xx+txoff, 224+ldl_y, 3, mono=gmono, char_offsets={})

                    dat = padtext(moondt[1], 6)
                    mn = pg.transform.smoothscale_by({"New": moon_new, "First": moon_fq, "Full": moon_full, "Last": moon_lq}[mt], (1.2, 1))

                    win.blit(mn, (80+xx+txoff, 265+ldl_y))
                    del mn

                    drawshadow(starfont32, dat, 76+xx+txoff, 354+ldl_y, 3, mono=gmono, char_offsets={})
        elif slide == "xf":
            drawshadow(startitlefont, efname, 180+txoff//3, 23+ldl_y, 3, mono=15, ofw=1.07, upper=veryuppercase)
            drawshadow(startitlefont, "Extended Forecast", 180+txoff//3, 49+ldl_y, 3, mono=15, ofw=1.07, upper=veryuppercase, color=yeller)
            def sane(text):
                text = text.replace("Thunderstorm", "T'Storm")
                if len(wraptext(text, 10)) > 2:
                    if "/" in text:
                        tl = list(text)
                        tl.insert(text.index("/")+1, " ")
                        text = "".join(tl)
                        return text
                for tx in text.split(" "):
                    if len(tx) > 10:
                        break
                else:
                    return text
                if "/" in text:
                    tl = list(text)
                    tl.insert(text.index("/")+1, " ")
                    text = "".join(tl)

                return text
            to = 13*widescreen
            yo = -round(ao*1.5)
            for i in range(3+widescreen):
                drawshadow(starfont32, "Lo", 118+i*230-18*2+to, 314+yo, 3, mono=gmono, color=(120, 120, 222))
                drawshadow(starfont32, "Hi", 118+i*230+18*3+to, 314+yo, 3, mono=gmono, color=yeller)
            if wxdata:
                for i in range(3+widescreen):
                    d = dt.date.today() + dt.timedelta(days=(i+2+subpage*3))
                    colow = {"color": yeller} if "whiteXF" not in old else {}
                    drawshadow(starfont32, d.strftime("%a").upper(), 118+i*230+to, 106+yo, 3, mono=gmono, **colow)
                    ix = i*2+4+subpage*6-(wxdata["extended"]["daypart"][0]["dayOrNight"] == "N")
                    fctx = sane(wxdata["extended"]["daypart"][ix]["phraseLong"])
                    fctx = wraptext(fctx, 10)
                    fctx = [f.strip().rstrip() for f in fctx]
                    for j, l in enumerate(fctx):
                        drawshadow(starfont32, l, 118+i*230+27-len(l)*9+to, 245+j*36+yo, 3, mono=gmono)
                    lo = str(wxdata["extended"]["daypart"][ix+1]["temperature"])
                    drawshadow(largefont32, lo, 114+i*230-18*2+24-len(lo)*12+to, 344+yo, 3, mono=25)

                    hi = str(wxdata["extended"]["daypart"][ix]["temperature"])
                    drawshadow(largefont32, hi, 114+i*230+18*3+24-len(hi)*12+to, 344+yo, 3, mono=25)
                    if xficons[i+subpage*3]:
                        xi = xficons[i+subpage*3][int(iconidx3%len(xficons[i+subpage*3]))][0]
                        xi = pg.transform.smoothscale_by(xi, (1.2, 1))
                        win.blit(xi, (120+i*230+27-xi.get_width()/2+to, 200-xi.get_height()/2+yo))
                        del xi
            else:
                drawshadow(starfont32, "Temporarily Unavailable", 177, 218, 3, mono=gmono)
        elif slide == "ol":
            drawshadow(startitlefont, "Outlook", 194+txoff//3, 39+ldl_y, 3, color=yeller, mono=16, ofw=1.07, bs=True, upper=veryuppercase)
            if clidata:
                drawpage([
                    "\n",
                    "        30 Day Outlook",
                    f"           {dt.date.today().strftime('%B').upper()}",
                    "",
                    f"Temperatures:  {['Normal', 'Above normal', 'Below normal'][clidata['temp_outlook']]}",
                    "",
                    f"Precipitation: {['Normal', 'Above normal', 'Below normal'][clidata['precip_outlook']]}"
                ], vshift=-20)
        elif slide == "sf":
            drawshadow(startitlefont, "School", 194+txoff//3, 25+ldl_y, 3, color=yeller, mono=18, ofw=1.07, bs=True, upper=veryuppercase)
            drawshadow(startitlefont, "Forecast", 194+txoff//3, 52+ldl_y, 3, color=yeller, mono=18, ofw=1.07, bs=True, upper=veryuppercase)

            if wxdata is None:
                drawshadow(starfont32, "       No Report Available", 80+txoff, 109+linespacing*2.5, 3, mono=gmono)
            else:
                fcsts = wxdata["hourly"]
                page = []
                times = []
                for fcst in fcsts:
                    dat = dt.datetime.fromtimestamp(fcst["valid"])
                    hour = dat.hour
                    if hour in [6, 7, 8, 13, 14, 15, 16]:
                        times.append((fcst, dat.strftime("%I:%M %p")[1:]))
                for time in times:
                    line = time[1]
                    line = textmerge(line, f"        {shorten_phrase(time[0]['phraseShort'])}")
                    line = textmerge(line, f"                  {round(time[0]['temperature'])}")
                    line = textmerge(line, f"                     {min(round(time[0]['rainChance']+time[0]['snowChance']+time[0]['sleetChance']+time[0]['freezingRainChance']), 100)}%")
                    precip_type = None
                    ch = [(time[0]['snowChance'], 'Snow'), (time[0]['sleetChance'], 'Sleet'), (time[0]['freezingRainChance'], 'FrzRn'), (time[0]['rainChance'], 'Rain')]
                    ch2 = sorted(ch, key=lambda x: x[0], reverse=True)
                    if ch2[0][0] == 0:
                        precip_type = ""
                    else:
                        precip_type = ch2[0][1]
                    line = textmerge(line, f"                          {precip_type}")

                    page.append(line)
                if veryuppercase:
                    page = [p.upper() for p in page]
                drawpage(page, f"        WEATHER   °{temp_symbol} PRECIP")
        elif slide == "df":
            drawshadow(startitlefont, "Daypart Forecast", 181+txoff//3, 39+ldl_y, 3, color=yeller, mono=15.5, ofw=1.07, bs=True, upper=veryuppercase)
            if not wxdata:
                drawshadow(starfont32, "       No Report Available", 80, 109+linespacing*2.5+ldl_y, 3, mono=gmono)
            else:
                for i  in range(4):
                    yoo = (ldl_y//4)
                    j = i+4+subpage*4
                    header = wxdata["extended"]["daypart"][j]["name"].upper()
                    header = textmerge(header, f"                {'HI' if wxdata['extended']['daypart'][j]['dayOrNight'] == 'D' else 'LO'}  WIND")
                    drawshadow(smallfont, header, 62+14+txoff, 84+ldl_y+(yoo+77)*i+9, 3, mono=gmono, upper=veryuppercase)
                    ps = wxdata["extended"]["daypart"][j]["phraseShort"]
                    pl = wxdata["extended"]["daypart"][j]["phraseLong"]
                    drawshadow(starfont32, ps if len(pl) > 14 else pl, 62+14+txoff, 96+14+ldl_y+(yoo+77)*i+9, 3, mono=gmono, upper=veryuppercase)
                    drawshadow(starfont32, padtext(wxdata["extended"]["daypart"][j]["temperature"], 3), 62+14+txoff+18*15, 96+14+ldl_y+(yoo+77)*i+9, 3, mono=gmono, upper=veryuppercase)
                    ws = wxdata["extended"]["daypart"][j]["windSpeed"]
                    wc = wxdata["extended"]["daypart"][j]["windCardinal"]
                    if ws > 9:
                        wt = textmerge(windreduce(wc), f"  {ws}")
                    elif ws == 0:
                        wt = "Calm"
                    else:
                        wt = textmerge(wc, f"   {ws}")
                    drawshadow(starfont32, wt, 62+14+txoff+18*20, 96+14+ldl_y+(yoo+77)*i+9, 3, mono=gmono, upper=veryuppercase)
                    drawreg(dficons[j-4], (640+txoff-15, 96+14+ldl_y+(yoo+77)*i+20), ix=(m.floor(iconidx3) % len(dficons[j-4])))
        elif slide == "intro":
            drawshadow(startitlefont, "Welcome!", 181+txoff//3, 39+ldl_y, 3, color=yeller, mono=15.5, ofw=1.07, bs=True, upper=veryuppercase)

            generaldrawidx += 3.5 / (framerate / 30)
            generaldrawidx = round(generaldrawidx*100)/100
            dr = generaldrawidx*1
            it = f"Hello,"
            if veryuppercase:
                it = it.upper()
            it += " "+locname+"!"
            tx, dr = drawing(it, dr, True)
            drawshadow(largefont32, tx, 98+txoff, 109+linespacing/2+ldl_y, 3, mono=20)

            for i, line in enumerate(wraptext(introtx, 30)):
                tx, dr = drawing(line, dr, True)
                drawshadow(starfont32, tx, 98+txoff, 109+linespacing*1.75+32*i+ldl_y, 3, mono=gmono, char_offsets={})
        elif slide == "ro":
            win.blit(regmapcut, (0, 0))
            drawshadow(startitlefont, "Regional", 194+txoff//3, 25+ldl_y, 3, color=yeller, mono=18, ofw=1.07, bs=True, upper=veryuppercase)
            drawshadow(startitlefont, "Observations", 194+txoff//3, 52+ldl_y, 3, color=yeller, mono=18, ofw=1.07, bs=True, upper=veryuppercase)

            def drawregloc(name, temp, idx, pos):
                if reglocs[idx][2]:
                    lat, long = reglocs[idx][2]["current"]["info"]["geocode"]
                    xx, yy = mapper((rmappoint1, rmappoint2), lat, long)
                    xx -= regmappos[0]-screenw//2
                    yy -= regmappos[1]-240
                else:
                    xx, yy = -300, -300
                xx += 8
                xx -= 60
                yy -= 18
                if reglocs[idx][3]:
                    drawreg(reglocs[idx][3], (xx+60, yy+18), (m.floor(iconidx3) % len(reglocs[idx][3])))
                drawshadow(starfont32, name, xx-round(len(name)*15/2)+34, yy-25, 3, mono=15)
                drawshadow(largefont32, str(temp), xx+25, yy, 3, mono=15, color=yeller, char_offsets=jroffsetstall, jr_override=jrfonttall, variable=jrwidthstall, leftalign=True)

            for i, lc in enumerate(reglocs):
                drawregloc(lc[1], "" if not lc[2] else lc[2]["current"]["conditions"]["temperature"], i, (150, 150))
        elif slide == "tcf":
            pre = 2
            post = 10
            roll = (48*seconds-slideinterval) - pre*seconds
            rt = (48-pre-post)
            roll = max(roll, 0)

            max_y = len(tcflocs) * 72 - 72 * 4
            yy = -min(max_y*roll/(rt*seconds), max_y)

            if "oldtcf" in old:
                for i in range(4):
                    win.blit(tcf_bg, (0, 91+(i-2)*tcf_bg.get_height()+18+yy%tcf_bg.get_height()))
            else:
                win.fill((0, 0, 64))

            stat = 0
            for i, name in enumerate(tcflocs):
                if (72*i+yy+ldl_y) <= -72:
                    continue

                if stat > 4:
                    continue

                stat += 1

                drawshadow(largefont32, name[1], 96, 72*i+120+yy+ldl_y, 3, color=yeller, mono=19, variable=jrwidthstravel, char_offsets=jroffsetstravel)
                if tcflocs[i][2]:
                    drawshadow(largefont32, padtext(str(tcflocs[i][2]["extended"]["daily"][1]["tempMin"]), 3), 540-21, 72*i+120+yy+ldl_y, 3, color=yeller, mono=21)
                    drawshadow(largefont32, padtext(str(tcflocs[i][2]["extended"]["daily"][1]["tempMax"]), 3), 613-21, 72*i+120+yy+ldl_y, 3, color=yeller, mono=21)
                if tcflocs[i][3]:
                    drawreg(tcflocs[i][3], (430, 72*i+120+yy+ldl_y+20), (m.floor(iconidx3) % len(tcflocs[i][3])))

            pg.draw.rect(win, outer_c, pg.Rect(0, 91+ldl_y, screenw, 20))
            drawshadow(smallfont, "LOW", 479+round((screenw-768)*2/3)+54, 75+ldl_y, 3, color=yeller, mono=gmono, char_offsets={})
            drawshadow(smallfont, "HIGH", 479+round((screenw-768)*2/3)+54+66, 75+ldl_y, 3, color=yeller, mono=gmono, char_offsets={})
        elif slide == "ti":
            lines = ["", "", "", "", "", "", ""]
            line = tidal[2]
            lines[0] = (m.floor(16-len(line)/2)*" "+line)
            if aldata["tidal"][0]:
                lines[1] = textmerge(textmerge("Lows:",
                                    " "*7+padtext(aldata["tidal"][0]["lows"][0][0], 11)),
                                    " "*21+padtext(aldata["tidal"][0]["lows"][1][0], 11))
                lines[2] = textmerge(textmerge("Highs:",
                                    " "*7+padtext(aldata["tidal"][0]["highs"][0][0], 11)),
                                    " "*21+padtext(aldata["tidal"][0]["highs"][1][0], 11))
            line = tidal[3]
            lines[3] = (m.floor(16-len(line)/2)*" "+line)
            if aldata["tidal"][1]:
                lines[4] = textmerge(textmerge("Lows:",
                                    " "*7+padtext(aldata["tidal"][1]["lows"][0][0], 11)),
                                    " "*21+padtext(aldata["tidal"][1]["lows"][1][0], 11))
                lines[5] = textmerge(textmerge("Highs:",
                                    " "*7+padtext(aldata["tidal"][1]["highs"][0][0], 11)),
                                    " "*21+padtext(aldata["tidal"][1]["highs"][1][0], 11))

            lines[6] = "   Sunrise         Set"
            if aldata["sun"]:
                s1 = dt.datetime.fromtimestamp(aldata["sun"]["sunrise1"])
                s2 = dt.datetime.fromtimestamp(aldata["sun"]["sunset1"])
                lines[6] = textmerge(textmerge("   Sunrise         Set", " "*11+splubby_the_return(s1.strftime("%I:%M%p").lower())), " "*23+splubby_the_return(s2.strftime("%I:%M%p").lower()))

            drawpage(lines)
        elif slide == "test":
            drawshadow(startitlefont, "Test Page", 181, 25+ldl_y, 3, color=yeller, mono=15.5, ofw=1.07, bs=True)
            drawshadow(startitlefont, "of Awesomeness", 181, 54+ldl_y, 3, color=yeller, mono=15.5, ofw=1.07, bs=True)
            drawshadow(starfont32, "       No Report Available", 80, 109+linespacing*2.5+ldl_y, 3, mono=gmono)

    nn = dt.datetime.now()
    al1 = False
    if not alerting:
        al1 = True

    alerting = False
    arank = 99999999
    for i, alert in enumerate(alertdata[1]):
        if alert[1] == "W":
            alerting = True
            alertactive = i+0
            arank = alert[2]
            break

    if alerting != switches[3]:
        switches[3] = alerting

    if al1 and alerting and not mute:
        beepch.play(beep)
    if alerting:
        crawling = True
    if ldlon and ldlmode:
        colorbug_started = False
    if slide not in ["cr", "lr"] and not ldlmode:
        draw_ldl(all_offset=ao, bh_offset=ao//2)
    ldl_y_off = -2
    if (ldlon and not serial) or not ldlmode or alerting:
        if serial:
            drawshadow(smallfont, "SN: 000000v1.0 SW:00000000 DQ:100", 78, 402.5-8, 3, mono=gmono, char_offsets={})
            drawshadow(smallfont, "RLYS:0110 BAUD:9600 SENSORS:N/A", 78, 402.5+24, 3, mono=gmono, char_offsets={})
        elif not crawling and not ((slide in ["lr", "cr"]) and not ldlmode):
            profiling_start()
            ldltext = ""
            ooo = True
            ldlextra = (4 if screenw > 768 else 0)
            ldlspace = ((ldlextra * 2) * " ") if ldlextra else ""
            if ldlidx == 0:
                if not veryuppercase:
                    ldltext = f"Conditions at {locname}"
                else:
                    ldltext = f"CONDITIONS AT {locname}"
            elif ldlidx == 1:
                if wxdata is not None:
                    ldltext = ccphrase
            elif ldlidx == 2:
                if wxdata is not None:
                    if wxdata["current"]["conditions"]["feelsLike"] == wxdata["current"]["conditions"]["temperature"]:
                        additional = ""
                    elif wxdata["current"]["conditions"]["feelsLike"] < wxdata["current"]["conditions"]["temperature"]:
                        additional = ldlspace + "               Wind Chill:"
                        additional += (padtext(wxdata["current"]["conditions"]["feelsLike"], 3) + f"°{temp_symbol}")
                    else:
                        additional = ldlspace + "               Heat Index:"
                        additional += (padtext(wxdata["current"]["conditions"]["feelsLike"], 3) + f"°{temp_symbol}")
                    ldltext = textmerge(f'Temp:{padtext(wxdata["current"]["conditions"]["temperature"], 3)}°{temp_symbol}',
                                        additional)
            elif ldlidx == 3:
                if wxdata is not None:
                    ldltext = textmerge(f'Humidity: {wxdata["current"]["conditions"]["humidity"]}%',
                                        f'{ldlspace}                 Dewpoint:{padtext(wxdata["current"]["conditions"]["dewPoint"], 3)}°{temp_symbol}')
            elif ldlidx == 4:
                if wxdata is not None:
                    bp = f'{wxdata["current"]["conditions"]["pressure"]:5.2f}'
                    ldltext = f'Barometric Pressure: {bp}'
                    pt = wxdata["current"]["conditions"]["pressureTendency"]
                    if pressuretrend == False:
                        ldltext += " in."
                    elif pt == 0:
                        ldltext += " S"
                    elif pt in [1, 3]:
                        ldltext += " R"
                    elif pt in [2, 4]:
                        ldltext += " F"
            elif ldlidx == 5:
                if wxdata is not None:
                    ldltext = textmerge(f'Wind: {padtext(wxdata["current"]["conditions"]["windCardinal"], 3)}',
                                        f'          {wxdata["current"]["conditions"]["windSpeed"]} {speed_unit}')
                    if wxdata["current"]["conditions"]["windSpeed"] == 0:
                        ldltext = "Wind: Calm"

                    if wxdata["current"]["conditions"]["windGusts"] is not None:
                        ldltext = textmerge(ldltext, f'{ldlspace}                  Gusts to  {wxdata["current"]["conditions"]["windGusts"]}')
            elif ldlidx == 6:
                if wxdata is not None:
                    ceil = f':{padtext(wxdata["current"]["conditions"]["cloudCeiling"], 5)}{short_dist}'
                    if wxdata["current"]["conditions"]["cloudCeiling"] is None:
                        if "ceiling_colon" in old:
                            ceil = ":Unlimited"
                        else:
                            ceil = " Unlimited"
                    ldltext = f'Visib:  {padtext(int(wxdata["current"]["conditions"]["visibility"]), 2)} {long_dist} {ldlspace}Ceiling' + ceil
            elif ldlidx == 7:
                if clidata is not None:
                    ldltext = f"{nn.strftime('%B')} Precipitation: {clidata['month_precip']}in"
            elif ldlidx == 8 and extraldltext:
                ldltext = extraldltext
            elif (ldlidx == 9 or (ldlidx == 8 and not extraldltext)):
                fc = (wxdata["extended"]["daypart"][0]["dayOrNight"] == "N")
                ooo = False
                xx = 72-ldlextra*18+txoff
                mm = pg.transform.smoothscale_by(ldllficon[m.floor(iconidx3) % len(ldllficon)][0], (1.2, 1))
                if fc == 0:
                    drawshadow(starfont32, "Today" , xx, 409, 3, mono=15, color=yeller)
                    drawshadow(starfont32, "'" , xx+72, 409, 3, mono=15, color=yeller)
                    drawshadow(starfont32, "s Forecast:" , xx+85, 409, 3, mono=15, color=yeller)
                    drawshadow(starfont32, "               High:" , xx+85+50+ldlextra*2*18, 409, 3, mono=18, color=yeller)
                    drawshadow(starfont32,f"                    {padtext(wxdata['extended']['daypart'][0]['temperature'], 3)}°{temp_symbol}" , xx+85+54+ldlextra*2*18, 409, 3, mono=18)
                    win.blit(mm, (xx+287-25, 418-15))
                elif fc == 1:
                    drawshadow(starfont32, "Tomorrow" , xx, 409, 3, mono=15, color=yeller)
                    drawshadow(starfont32, "'" , xx+72+50, 409, 3, mono=15, color=yeller)
                    drawshadow(starfont32, "s Forecast:" , xx+85+50, 409, 3, mono=15, color=yeller)
                    drawshadow(starfont32, "               High:" , xx+85+50+ldlextra*2*18, 409, 3, mono=18, color=yeller)
                    drawshadow(starfont32,f"                    {padtext(wxdata['extended']['daypart'][1]['temperature'], 3)}°{temp_symbol}" , xx+85+54+ldlextra*2*18, 409, 3, mono=18)
                    win.blit(mm, (xx+337-25, 418-15))
                del mm

            if ldldrawing:
                ldldrawidx += 3.5 / (framerate / 30)
                ldldrawidx = round(ldldrawidx*100)/100
                if veryuppercase and ldlidx != 0:
                    ldltext = ldltext.upper()
                ldltext = drawing(ldltext + " ", ldldrawidx)
            profiling_end("ops")
            if ui and ooo:
                drawshadow(starfont32, ldltext, 78+txoff-ldlextra*18, 403+ldl_y_off, 3, mono=gmono, char_offsets={})
            nextcrawlready = True

            ldlinterval -= delta*seconds
            if ldlinterval <= 0:
                ldlidx += 1
                ldlidx %= (8 + (ldlmode and bool(extraldltext)) + (ldllf and ldlmode))
                if ldlidx == 0 and not foreverldl:
                    ldlreps -= 1
                if ldlreps <= 0 and not foreverldl:
                    ldlon = False
                if ldlidx == 0 and not ldlmode and (len(crawls) > 0):
                    crawling = True
                    crawlscroll = 0
                ldlinterval = ldlintervaltime*1
                if (ldlidx == 9 or (ldlidx == 8 and not extraldltext)):
                    ldlinterval *= 3
                ldldrawidx = 0
        elif (not (slide in ["lr", "cr"])) or alerting:
            if alerting:
                crawl = alertdata[1][alertactive][3].upper()
            else:
                if len(crawls) > 0:
                    crawl = crawls[crawlactive]
                else:
                    crawl = 0
            nextcrawlready = False
            crawlscroll += 2*delta*seconds
            if alerting:
                pg.draw.rect(win, ((187, 17, 0) if (slide not in ["lr", "cr"] or ("warnpalbug" not in old)) else (128, 16, 0)) if True or "ADVISORY" not in crawl else (126, 31, 0), pg.Rect(0, 404, screenw, 76))
            jrf = jrfontnormal
            if (
                (
                    (slide in ["lr", "cr"]) or (colorbug_started and colorbug_nat and ldlmode)
                )
                and ("warnpalbug" in old)
                and alerting
                ):
                jrf = jrfontradaralert
            drawshadow(starfont32, crawl, round(screenw-crawlscroll), 403+ldl_y_off, 3, mono=gmono, char_offsets={}, jr_override=jrf)
            if not alerting:
                crawltime -= delta*seconds
            if crawlscroll >= (screenw+(len(crawl)+4)*(gmono if not jr else m.floor(gmono))):
                if alerting:
                    crawlscroll = 0
                    alertactive += 1
                    if not mute:
                        beepch.play(beep)
                else:
                    crawlscroll = 0
                    ldlidx = 0
                    ldldrawidx = 100
            if crawltime <= 0:
                crawltime = crawllen*seconds
                crawling = False
                nextcrawlready = True

    if slide not in ["cr", "lr"] and not ldlmode:
        draw_banner(all_offset=ao, bh_offset=ao//2)
        win.blit(logo, (txoff//3, ldl_y))

    if ldlmode:
        pass
    elif slide == "oldcc" or (slide == "cc" and textpos > 1):
        ln = f"Now at {locname}"
        if veryuppercase:
            ln = ln.upper()
        drawshadow(startitlefont, ln, 194+txoff//3, 30, 3, mono=18, ofw=1.07, upper=veryuppercase)
    elif slide == "cc":
        drawshadow(startitlefont, "Current", 194+txoff//3, 25+ldl_y, 3, color=yeller, mono=18, ofw=1.07, bs=True, upper=veryuppercase)
        drawshadow(startitlefont, "Conditions", 194+txoff//3, 52+ldl_y, 3, color=yeller, mono=18, ofw=1.07, bs=True, upper=veryuppercase)
    elif slide == "lo":
        drawshadow(startitlefont, "Latest Observations", 181+txoff//3, 39+ldl_y, 3, color=yeller, mono=15.5, ofw=1.07, bs=True, upper=veryuppercase)
    elif slide == "oldro":
        drawshadow(startitlefont, your+"Latest Observations", 181, 39+ldl_y, 3, color=yeller, mono=15.5, ofw=1.07, bs=True, upper=veryuppercase)
    elif slide == "lf":
        drawshadow(startitlefont, your+"Local Forecast", 181+txoff//3, 39+ldl_y, 3, color=yeller, mono=15.5, ofw=1.07, bs=True, upper=veryuppercase)
    elif slide == "al":
        drawshadow(startitlefont, "Almanac", 181+txoff//3, 39+ldl_y, 3, color=yeller, mono=18, ofw=1.07, bs=True, upper=veryuppercase)
    elif slide == "xf":
        if "oldtitles" in old:
            drawshadow(startitlefont, your+"Extended Forecast", 181+txoff//3, 39+ldl_y, 3, color=yeller, mono=15.5, ofw=1.07, bs=True, upper=veryuppercase)
        else:
            drawshadow(startitlefont, efname, 180+txoff//3, 23+ldl_y, 3, mono=15, ofw=1.07, upper=veryuppercase)
            drawshadow(startitlefont, "Extended Forecast", 180+txoff//3, 49+ldl_y, 3, mono=15, ofw=1.07, upper=veryuppercase, color=yeller)
    elif slide == "ol":
        drawshadow(startitlefont, "Outlook", 194+txoff//3, 39+ldl_y, 3, color=yeller, mono=16, ofw=1.07, bs=True, upper=veryuppercase)
    elif slide == "sf":
        drawshadow(startitlefont, "School", 194+txoff//3, 25+ldl_y, 3, color=yeller, mono=18, ofw=1.07, bs=True, upper=veryuppercase)
        drawshadow(startitlefont, "Forecast", 194+txoff//3, 52+ldl_y, 3, color=yeller, mono=18, ofw=1.07, bs=True, upper=veryuppercase)
    elif slide == "df":
        drawshadow(startitlefont, "Daypart Forecast", 181+txoff//3, 39+ldl_y, 3, color=yeller, mono=15.5, ofw=1.07, bs=True, upper=veryuppercase)
    elif slide == "intro":
        drawshadow(startitlefont, "Welcome!", 181+txoff//3, 39+ldl_y, 3, color=yeller, mono=15.5, ofw=1.07, bs=True, upper=veryuppercase)
    elif slide == "ro":
        drawshadow(startitlefont, "Regional", 194+txoff//3, 25+ldl_y, 3, color=yeller, mono=15.5, ofw=1.07, bs=True, upper=veryuppercase)
        drawshadow(startitlefont, "Observations", 194+txoff//3, 52+ldl_y, 3, color=yeller, mono=15.5, ofw=1.07, bs=True, upper=veryuppercase)
    elif slide == "tcf":
        drawshadow(startitlefont, "Travel Forecast", 181+txoff//3, 25+ldl_y, 3, color=yeller, mono=18, ofw=1.07, upper=veryuppercase)
        drawshadow(startitlefont, f"For {nn.strftime('%A')}", 181+txoff//3, 52+ldl_y, 3, color=yeller, mono=18, ofw=1.07, upper=veryuppercase)
    elif slide == "ti":
        drawshadow(startitlefont, "Tides", 181+txoff//3, 39+ldl_y, 3, color=yeller, mono=16, ofw=1.07, bs=True, upper=veryuppercase)
    elif slide == "test":
        drawshadow(startitlefont, "Test Page", 181, 25+ldl_y, 3, color=yeller, mono=15.5, ofw=1.07, bs=True)
        drawshadow(startitlefont, "of Awesomeness", 181, 54+ldl_y, 3, color=yeller, mono=15.5, ofw=1.07, bs=True)

    #timer
    time = " 7:09:14 AM"
    date = " THU MAY  6"

    time = splubby_the_return(nn.strftime("%I:%M:%S %p").upper())
    if len(time) < 11:
        time = " " + time

    day = splubby_the_return(nn.strftime("%d"))
    if len(day) < 2:
        day = " " + day
    date = nn.strftime(" %a %b ") + day


    if (type(lastlasttime) != int) and timedrawing:
        tcl = []
        for i, j in enumerate(time):
            if j == lastlasttime[i]:
                tcl.append(white)
            else:
                tcl.append((0, 0, 0))
    else:
        tcl = white

    if (ldlon and not serial) or not ldlmode:
        if not ui or ((slide in ["lr", "cr"]) and not ldlmode):
            pass
        elif ldlmode or textpos >= 2:
            txo = ((-6 if textpos <= 2 else ldl_y//2))
            drawshadow(smallfont, time.upper(), 465+round((screenw-768)*2/3), 375+txo, 3, mono=gmono, color=tcl, char_offsets={})
            drawshadow(smallfont, date.upper(), 60+round((screenw-768)/3), 375+txo, 3, mono=gmono, char_offsets={})
        elif slide == "oldcc" and not ldlmode and textpos < 2:
            pass
        elif textpos == 0:
            drawshadow(smallfont, time.upper(), 479+round((screenw-768)*2/3)-2, 35, 3, mono=gmono, color=tcl, char_offsets={})
            drawshadow(smallfont, date.upper(), 479+round((screenw-768)*2/3), 55, 3, mono=gmono, char_offsets={})
        elif textpos == 1:
            drawshadow(smallfont, time.upper(), 465+round((screenw-768)*2/3)-2, 28, 3, mono=gmono, color=tcl, char_offsets={})
            drawshadow(smallfont, date.upper(), 465+round((screenw-768)*2/3), 48, 3, mono=gmono, char_offsets={})

    if type(lasttime) != int:
        lastlasttime = lasttime + ""
    lasttime = time + ""

    clear_profile()

    transform = (1/(1.2 if compress else 1), 1)
    if (rwin.get_width()/rwin.get_height() > (rwidth/480)): #wider
        sl = rwin.get_height()/480
        transform = (sl/(1.2 if compress else 1), sl)
    elif (rwin.get_width()/rwin.get_height() < (rwidth/480)): #taller
        sl = rwin.get_width()/rwidth
        transform = (sl/(1.2 if compress else 1), sl)
    else:
        sl = rwin.get_height()/480
        transform = (sl/(1.2 if compress else 1), sl)

    if transform != (1, 1):
        if smoothscale:
            tr = pg.transform.smoothscale_by(win, transform)
        else:
            tr = pg.transform.scale_by(win, transform)
    else:
        tr = win

    rwin.fill((0, 0, 0))
    rwin.blit(tr, (rwin.get_width()/2-tr.get_width()/2, rwin.get_height()/2-tr.get_height()/2))
    del tr
    pg.display.flip()
    frame_idx_actual += 1
    p_counter += 1
    p_counter %= 512

pg.quit()
