import datetime as dt
import threading as th
import time as tm
import math as m
import random as rd
import pygame as pg
import requests as r
from io import BytesIO
import traceback as tb
import gc

from calculations import splubby_the_return, sign, mapper, chars

icontable = [
    None,
    None,
    None,
    "Thunderstorm",
    "Thunderstorm",
    "Rain-Snow",
    "Rain-Sleet",
    "Wintry-Mix",
    "Shower",
    "Shower",
    "Freezing-Rain",
    "Shower",
    "Rain",
    "Light-Snow",
    "Heavy-Snow",
    "Blowing-Snow",
    "Heavy-Snow",
    "Sleet",
    "Sleet",
    "Fog",
    "Fog",
    "Fog",
    "Fog",
    "Windy",
    "Windy",
    "Blowing-Snow",
    "Cloudy",
    "Partly-Clear",
    "Mostly-Cloudy",
    "Mostly-Clear",
    "Partly-Cloudy",
    "Clear",
    "Sunny",
    "Mostly-Clear",
    "Partly-Cloudy",
    "Rain-Sleet",
    "Sunny",
    "Thunderstorm",
    "Thunderstorm",
    "Shower",
    "Shower",
    "Heavy-Snow",
    "Heavy-Snow",
    "Heavy-Snow",
    "Partly-Cloudy", #N/A is partly cloudy by default
    "Shower",
    "Heavy-Snow",
    "Thunderstorm"
]

regionalicontable = [
    None,
    None,
    None,
    "Thunderstorm",
    "Thunderstorm",
    "Rain-Snow-1992",
    "Rain-Sleet",
    "Wintry-Mix-1992",
    "Freezing-Rain-1992",
    "Rain-1992",
    "Freezing-Rain-1992",
    "Shower",
    "Rain-1992",
    "Light-Snow",
    "Heavy-Snow-1994",
    "Blowing Snow",
    "Light-Snow",
    "Sleet",
    "Sleet",
    "Smoke",
    "Fog",
    "Haze",
    "Smoke",
    "Wind",
    "Wind",
    "Cold",
    "Cloudy",
    "Mostly-Cloudy-Night-1994",
    "Mostly-Cloudy-1994",
    "Partly-Cloudy-Night",
    "Partly-Cloudy",
    "Clear-1992",
    "Sunny",
    "Partly-Cloudy-Night",
    "Partly-Cloudy",
    "Rain-Sleet",
    "Hot",
    "Scattered-Tstorms-1994",
    "Scattered-Tstorms-1994",
    "Scattered-Showers-1994",
    "Shower",
    "Scattered-Snow-Showers-1994",
    "Heavy-Snow-1994",
    "Heavy-Snow-1994",
    "Partly-Cloudy", #na
    "Shower",
    "Heavy-Snow-1994",
    "Thunderstorm"
]

xficontable = [
    None,
    None,
    None,
    "Thunderstorms",
    "Thunderstorms",
    "Rain-Snow",
    "Rain-Sleet",
    "Wintry-Mix",
    "Freezing-Rain-Sleet",
    "Rain",
    "Freezing-Rain",
    "Showers",
    "Rain",
    "Light-Snow",
    "Heavy-Snow",
    "Blowing-Snow",
    "Heavy-Snow",
    "Sleet",
    "Sleet",
    "Fog",
    "Fog",
    "Fog",
    "Fog",
    "Windy",
    "Windy",
    "Blowing-Snow",
    "Cloudy",
    "Mostly-Cloudy",
    "Mostly-Cloudy",
    "Partly-Cloudy",
    "Partly-Cloudy",
    "Sunny",
    "Sunny",
    "Partly-Cloudy",
    "Partly-Cloudy",
    "Rain-Sleet",
    "Sunny",
    "Isolated-Tstorms",
    "Scattered-Tstorms",
    "Scattered-Showers",
    "Showers",
    "Scattered-Snow-Showers",
    "Heavy-Snow",
    "Heavy-Snow",
    "Partly-Cloudy",
    "Scattered-Showers",
    "Scattered-Snow-Showers",
    "Scattered-Tstorms"
]

icon_offset = {"Rain": (10, 10), "Sunny": (0, 10), "Fog": (0, 15)}


def quickread(file):
    with open(file, "r") as f:
        return f.read().strip().rstrip()

def loadjrfont(name):
    surfs = (pg.image.load(f"fonts/jrfonts/fill/{name}.png").convert_alpha(), pg.image.load(f"fonts/jrfonts/shadow/{name}.png").convert_alpha())
    widths = quickread(f"fonts/jrfonts/fill/{name}.widths.txt").split(",")
    offsets = quickread(f"fonts/jrfonts/fill/{name}.offsets.txt").split(",")
    off2 = {}
    for i, v in enumerate(offsets):
        off2[chars[i]] = -int(v)
    widths = [int(x) for x in widths]
    return surfs, widths, off2

# Module-level shared state - set by main.py before starting threads
loc = ""
flavor = []
afos_climate = ""
tidal = ("", "", "", "")
radar_provider = "apollo"
screenw = 768
obsloc = []
reglocs = []
tcflocs = []
dficons = [[] for _ in range(12)]
connections = []
wxdata = None
clidata = None
alertdata = [None, []]
mainicon = None
ldllficon = None
radardata = None
aldata = {"sun": {}, "moon": [], "tidal": [None, None]}
regmap = None
regmapcut = None
regmappos = ()
mappoint1 = None
mappoint2 = None
rmappoint1 = None
rmappoint2 = None
xficons = [None]*6

# Media state
musicfiles = []
musicch = None
ldlmode = False
lfmusic = False
mute = False
ldlfeed = None
smode = 0
sm2 = True
latestframe = None
capframes = []
ffps = 0
flock = th.Lock()

# Streaming state
audiorate = 44100
framerate = 60
vencoder = "libx264"
avscale = (640, 480)


def init(**kwargs):
    g = globals()
    for k, v in kwargs.items():
        g[k] = v


def getdata():
    ix = 0
    global wxdata, clidata, alertdata, mainicon, ldllficon, radardata, aldata
    global regmapcut, regmappos, xficons
    datagot = False

    while True:
        if datagot:
            ix += 1
            ix %= 60
        try:
            wxdata = r.get(f"https://wx.lewolfyt.cc/?loc={loc}"+"&extendeddays=10").json()

            if icontable[wxdata['current']['info']['iconCode']] is None:
                mainicon = [(pg.Surface((1, 1), pg.SRCALPHA), None)]
            else:
                micon = pg.image.load_animation(f"icons/icons_cc/{icontable[wxdata['current']['info']['iconCode']]}.gif")
                nmicon = []
                for fr, ftime in micon:
                    nmicon.append((fr.convert_alpha(), ftime))
                mainicon = nmicon
            dn = (wxdata["extended"]["daypart"][0]["dayOrNight"] == "N")
            if regionalicontable[wxdata['extended']['daypart'][dn]['iconCode']] is None:
                mainicon = [(pg.Surface((1, 1), pg.SRCALPHA), None)]
            else:
                micon = pg.image.load_animation(f"icons/icons_reg/{regionalicontable[wxdata['extended']['daypart'][dn]['iconCode']]}.gif")
                nricon = []
                for fr, ftime in micon:
                    nricon.append((fr.convert_alpha(), ftime))
                ldllficon = nricon

            if "df" in flavor:
                for i in range(12):
                    ic = regionalicontable[wxdata['extended']['daypart'][i+4]['iconCode']]
                    if ic:
                        dficons[i] = [(s.convert_alpha(), ft) for s, ft in pg.image.load_animation(f"icons/icons_reg/{ic}.gif")]
                    else:
                        dficons[i] = []

            az = [None, []]
            if wxdata["current"]["alerts"]:
                a_preprocess = {}
                for alert in wxdata["current"]["alerts"]:
                    a_preprocess[alert["alertid"]] = alert
                aas = list(a_preprocess.values())

                getdetaillist = [x for x in aas if x["significance"] == "W"]
                keylist = ",".join([x["alertkey"] for x in getdetaillist])

                almap = {}
                if keylist:
                    ll = "https://wx.lewolfyt.cc/alerts?alertkey="+keylist
                    print(ll)
                    details = r.get(ll).json()["alerts"]
                    for alert in details:
                        almap[alert["alertid"]] = alert["description"].replace("&&", "").replace("\n", " ").strip().rstrip()

                for alert in aas:
                    az[1].append((alert["headline"], alert["significance"], alert["rank"],
                                  None if alert["alertid"] not in almap else almap[alert["alertid"]]))
            az[1] = sorted(az[1], key=lambda e : e[2])
            alertdata = az

            lat, long = wxdata["current"]["info"]["geocode"]
            x, y = mapper((rmappoint1, rmappoint2), lat, long)
            regmappos = (x, y)
            x = max(x, 0)
            y = max(y, 0)
            x = min(x, regmap.get_width()-screenw)
            y = min(y, regmap.get_height()-480)
            regmapcut.blit(regmap, (0, 0), pg.Rect(x, y, screenw, 480))

            for i in range(6):
                ix = i*2+4-(wxdata["extended"]["daypart"][0]["dayOrNight"] == "N")
                if xficontable[wxdata['extended']['daypart'][ix]['iconCode']] is None:
                    ficon = [(pg.Surface((1, 1), pg.SRCALPHA), None)]
                else:
                    xficon = pg.image.load_animation(f"icons/icons_xf/{xficontable[wxdata['extended']['daypart'][ix]['iconCode']]}.gif")
                    ficon = []
                    for fr, ftime in xficon:
                        ficon.append((fr.convert_alpha(), ftime))
                xficons[i] = ficon
        except:
            print(tb.format_exc())

        if "ti" in flavor:
            if not "al" in flavor:
                print("tidaling")
                if wxdata:
                    lat, long = wxdata["current"]["info"]["geocode"]
                    sr1 = r.get(f"https://api.sunrisesunset.io/json?lat={lat}&lng={long}&time_format=unix").json()["results"]
                    sr2 = r.get(f"https://api.sunrisesunset.io/json?lat={lat}&lng={long}&time_format=unix&date=tomorrow").json()["results"]
                    aldata["sun"] = {
                        "sunrise1": int(sr1["sunrise"]),
                        "sunset1": int(sr1["sunset"]),
                        "sunrise2": int(sr2["sunrise"]),
                        "sunset2": int(sr2["sunset"])
                    }

            t1 = aldata["tidal"][0]
            print(f"https://wx.lewolfyt.cc/?id={tidal[0]}")
            t1data = r.get(f"https://wx.lewolfyt.cc/tides?id={tidal[0]}").json()["tides"]
            t1list = {"lows": [], "highs": []}
            for i in range(4):
                fts = dt.datetime.fromtimestamp(t1data[i]["valid"])
                t1list[["lows", "highs"][t1data[i]["type"] == "H"]].append((splubby_the_return(fts.strftime("%I:%M%p").lower()+" "+fts.strftime("%a")), t1data[i]["valid"]))
            aldata["tidal"][0] = t1list

            t2 = aldata["tidal"][1]
            t2data = r.get(f"https://wx.lewolfyt.cc/tides?id={tidal[1]}").json()["tides"]
            t2list = {"lows": [], "highs": []}
            for i in range(4):
                fts = dt.datetime.fromtimestamp(t2data[i]["valid"])
                t2list[["lows", "highs"][t1data[i]["type"] == "H"]].append((splubby_the_return(fts.strftime("%I:%M%p").lower()+" "+fts.strftime("%a")), t1data[i]["valid"]))
            aldata["tidal"][1] = t2list

        if "al" in flavor:
            import moon_calc
            startdt = dt.date.today()
            moons = sorted([
                ("new", moon_calc.localtime(moon_calc.next_new_moon(startdt))),
                ("lq",  moon_calc.localtime(moon_calc.next_last_quarter_moon(startdt))),
                ("fq",  moon_calc.localtime(moon_calc.next_first_quarter_moon(startdt))),
                ("full",  moon_calc.localtime(moon_calc.next_full_moon(startdt)))
            ], key=(lambda p : p[1]))
            mooninfo = [(
                {"new": "New", "fq": "First", "lq": "Last", "full": "Full"}[p[0]],
                p[1].strftime("%h ")+splubby_the_return(p[1].strftime("%d"))
            ) for p in moons]
            aldata["moon"] = mooninfo
            if wxdata:
                lat, long = wxdata["current"]["info"]["geocode"]
                sr1 = r.get(f"https://api.sunrisesunset.io/json?lat={lat}&lng={long}&time_format=unix").json()["results"]
                sr2 = r.get(f"https://api.sunrisesunset.io/json?lat={lat}&lng={long}&time_format=unix&date=tomorrow").json()["results"]
                aldata["sun"] = {
                    "sunrise1": int(sr1["sunrise"]),
                    "sunset1": int(sr1["sunset"]),
                    "sunrise2": int(sr2["sunrise"]),
                    "sunset2": int(sr2["sunset"])
                }

        def get_obsloc(l):
            try:
                l[2] = r.get(f"https://wx.lewolfyt.cc/?loc={l[0]}&include=current").json()
            except:
                print(tb.format_exc())
        print("gre")
        def get_regloc(l):
            try:
                l[2] = r.get(f"https://wx.lewolfyt.cc/?loc={l[0]}&include=current").json()
                l3 = pg.image.load_animation(f'icons/icons_reg/{regionalicontable[l[2]["current"]["info"]["iconCode"]]}.gif')
                l[3] = [(l[0].convert_alpha(), l[1]) for l in l3]
                #print("got reg icon")
            except:
                print(tb.format_exc())
        def get_tcfloc(l):
            try:
                l[2] = r.get(f"https://wx.lewolfyt.cc/?loc={l[0]}&include=extended").json()
                l3 = pg.image.load_animation(f'icons/icons_reg/{regionalicontable[l[2]["extended"]["daypart"][1+(l[2]["extended"]["daypart"][0]["dayOrNight"]=="D")]["iconCode"]]}.gif')
                l[3] = [(l[0].convert_alpha(), l[1]) for l in l3]
                #print("got reg icon")
            except:
                print(tb.format_exc())
        if "lo" in flavor:
            for l in obsloc:
                th.Thread(target=get_obsloc, args=(l,)).start()
        if "ro" in flavor:
            for rg in reglocs:
                th.Thread(target=get_regloc, args=(rg,)).start()
        if "tcf" in flavor:
            for tc in tcflocs:
                th.Thread(target=get_tcfloc, args=(tc,)).start()

        try:
            report = r.get(f"https://mesonet.agron.iastate.edu/cgi-bin/afos/retrieve.py?&pil={afos_climate}&center=&limit=1&sdate=&edate=&ttaaii=&order=desc").text

            rline = report[report.index("MONTH TO DATE"):].split("\n")[0]

            #get outlook data
            templine = report[report.index("DEGREE DAYS"):]
            templine = templine[templine.index("MONTH TO DATE"):].split("\n")[0]

            for section in rline.split(" "):
                if section.strip() == "":
                    continue
                try:
                    float(section)
                except:
                    pass
                else:
                    break

            ix = 0
            for ts in templine.split(" "):
                if ts.strip() == "":
                    continue
                try:
                    float(ts)
                except:
                    pass
                else:
                    ix += 1
                    if ix == 2:
                        normt = float(ts)
                    if ix == 3:
                        break
            ts = float(ts)
            ix = 0
            for rs in rline.split(" "):
                if rs.strip() == "":
                    continue
                try:
                    float(rs)
                except:
                    pass
                else:
                    ix += 1
                    if ix == 2:
                        normp = float(rs)
                    if ix == 3:
                        break
            rs = float(rs)
            dev1 = (abs(ts/normt) > 0.15)
            dev2 = (abs(rs/normp) > 0.15)

            clidata = {"month_precip": section, "temp_outlook": dev1*sign(ts), "precip_outlook": dev2*sign(rs)}
            datagot = True
        except:
            print(tb.format_exc())

        if "lr" in flavor:
            try:
                if radar_provider == "apollo":
                    radardt = pg.image.load_animation(BytesIO(r.get(f"http://apollo.us.com:8008/radar_composite_animate.gif").content))
                    radardata2 = []
                    lat, long = wxdata["current"]["info"]["geocode"]
                    x, y = mapper((mappoint1, mappoint2), lat, long)
                    x = max(x, 0)
                    y = max(y, 0)
                    x = min(x, radardt[0][0].get_width()-screenw//2)
                    y = min(y, radardt[0][0].get_height()-240)
                    for rad, t in radardt:
                        r2 = pg.Surface((screenw//2, 240))
                        r2.blit(rad, (0, 0), pg.Rect(x, y, screenw//2, 240))
                        radardata2.append((pg.transform.scale_by(r2, (2, 2)), t))
                    radardata = radardata2
            except:
                print(tb.format_exc())
        elif "cr" in flavor:
            try:
                if radar_provider == "apollo":
                    radardt = pg.image.load(BytesIO(r.get(f"http://apollo.us.com:8008/radar_composite.png").content))
                    radardata2 = []
                    lat, long = wxdata["current"]["info"]["geocode"]
                    x, y = mapper((mappoint1, mappoint2), lat, long)
                    x = max(x, 0)
                    y = max(y, 0)
                    x = min(x, radardt.get_width()-screenw//2)
                    y = min(y, radardt.get_height()-240)
                    r2 = pg.Surface((screenw//2, 240))
                    r2.blit(radardt, (0, 0), pg.Rect(x, y, screenw//2, 240))
                    radardata2.append((pg.transform.scale_by(r2, (2, 2)), 0))
                    radardata = radardata2
            except:
                print(tb.format_exc())
        gc.collect()
        for i in range(300):
            tm.sleep(1)
