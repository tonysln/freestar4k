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
    surfs = (pg.image.load(f"jrfonts/fill/{name}.png").convert_alpha(), pg.image.load(f"jrfonts/shadow/{name}.png").convert_alpha())
    widths = quickread(f"jrfonts/fill/{name}.widths.txt").split(",")
    offsets = quickread(f"jrfonts/fill/{name}.offsets.txt").split(",")
    off2 = {}
    for i, v in enumerate(offsets):
        off2[chars[i]] = -int(v)
    widths = [int(x) for x in widths]
    return surfs, widths, off2


def connsendall(conn, data):
    try:
        conn.sendall(data)
    except BrokenPipeError:
        pass


def sendtoall(data):
    for connection in connections:
        connsendall(connection, data)


# Module-level shared state - set by main.py before starting threads
loc = ""
metric = False
flavor = []
afos_climate = ""
tidal = ("", "", "", "")
radar_provider = "apollo"
screenw = 768
obsloc = []
reglocs = []
tcflocs = []
dficons = [[] for _ in range(12)]
leds = [False]*13
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
ldlfeedactive = False
smode = 0
sm2 = True
latestframe = None
capframes = []
ffps = 0
flock = th.Lock()

# Streaming state
outputs = None
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
    global leds, regmapcut, regmappos, xficons
    datagot = False

    while True:
        if datagot:
            ix += 1
            ix %= 60
        leds[6] = True
        sendtoall(f"led 6 1\n".encode())
        try:
            wxdata = r.get(f"https://wx.lewolfyt.cc/?loc={loc}"+("" if not metric else "&units=m")+"&extendeddays=10").json()

            if icontable[wxdata['current']['info']['iconCode']] is None:
                mainicon = [(pg.Surface((1, 1), pg.SRCALPHA), None)]
            else:
                micon = pg.image.load_animation(f"icons_cc/{icontable[wxdata['current']['info']['iconCode']]}.gif")
                nmicon = []
                for fr, ftime in micon:
                    nmicon.append((fr.convert_alpha(), ftime))
                mainicon = nmicon
            dn = (wxdata["extended"]["daypart"][0]["dayOrNight"] == "N")
            if regionalicontable[wxdata['extended']['daypart'][dn]['iconCode']] is None:
                mainicon = [(pg.Surface((1, 1), pg.SRCALPHA), None)]
            else:
                micon = pg.image.load_animation(f"icons_reg/{regionalicontable[wxdata['extended']['daypart'][dn]['iconCode']]}.gif")
                nricon = []
                for fr, ftime in micon:
                    nricon.append((fr.convert_alpha(), ftime))
                ldllficon = nricon

            if "df" in flavor:
                for i in range(12):
                    ic = regionalicontable[wxdata['extended']['daypart'][i+4]['iconCode']]
                    if ic:
                        dficons[i] = [(s.convert_alpha(), ft) for s, ft in pg.image.load_animation(f"icons_reg/{ic}.gif")]
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
                    xficon = pg.image.load_animation(f"icons_xf/{xficontable[wxdata['extended']['daypart'][ix]['iconCode']]}.gif")
                    ficon = []
                    for fr, ftime in xficon:
                        ficon.append((fr.convert_alpha(), ftime))
                xficons[i] = ficon
            leds[1] = True
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
                l[2] = r.get(f"https://wx.lewolfyt.cc/?loc={l[0]}&include=current"+("" if not metric else "&units=m")).json()
                leds[1] = True
            except:
                print(tb.format_exc())
        print("gre")
        def get_regloc(l):
            try:
                l[2] = r.get(f"https://wx.lewolfyt.cc/?loc={l[0]}&include=current"+("" if not metric else "&units=m")).json()
                l3 = pg.image.load_animation(f'icons_reg/{regionalicontable[l[2]["current"]["info"]["iconCode"]]}.gif')
                l[3] = [(l[0].convert_alpha(), l[1]) for l in l3]
                #print("got reg icon")
                leds[1] = True
            except:
                print(tb.format_exc())
        def get_tcfloc(l):
            try:
                l[2] = r.get(f"https://wx.lewolfyt.cc/?loc={l[0]}&include=extended"+("" if not metric else "&units=m")).json()
                l3 = pg.image.load_animation(f'icons_reg/{regionalicontable[l[2]["extended"]["daypart"][1+(l[2]["extended"]["daypart"][0]["dayOrNight"]=="D")]["iconCode"]]}.gif')
                l[3] = [(l[0].convert_alpha(), l[1]) for l in l3]
                #print("got reg icon")
                leds[1] = True
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
            leds[1] = True
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
                leds[1] = True
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
                leds[1] = True
            except:
                print(tb.format_exc())
        leds[6] = False
        sendtoall(f"led 6 0\n".encode())
        gc.collect()
        for i in range(300):
            tm.sleep(1)


def domusic():
    if mute:
        return
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


def omnomnomimeatingtheframes():
    global latestframe, capframes
    next_time = tm.perf_counter()
    while True:
        if ffps == 0:
            tm.sleep(0.01)
            next_time = tm.perf_counter()
            continue

        interval = 1.0 / float(ffps)
        next_time += interval
        if len(capframes) == 0:
            tm.sleep(0.01)
            next_time = tm.perf_counter()
            continue
        with flock:
            try:
                latestframe = capframes.pop(0)
            except:
                next_time = tm.perf_counter()
                continue
            if len(capframes) > 1200:
                capframes = capframes[600:]
                print("clipped capture frames! running slow?")

        #all programs need their sleep
        sleep_time = next_time - tm.perf_counter()
        if sleep_time > 0:
            tm.sleep(sleep_time)
        else:
            if -sleep_time > 1.0:
                next_time = tm.perf_counter()


def docapture():
    global latestframe, ffps
    import cv2
    if ldlfeedactive:
        vidcap = cv2.VideoCapture(ldlfeed)
        if not vidcap.isOpened():
            vidcap = None
            print("Video could not be opened!")
    else:
        vidcap = None
    print("Capture active!")
    #last = tm.time()

    ret_counter = 0
    reconnects = 0
    while True:
        if vidcap:
            ret, frame = vidcap.read()
            fps = vidcap.get(cv2.CAP_PROP_FPS)
            ffps = fps
            if not leds[0]:
                leds[0] = True
                sendtoall(f"led 0 1\n".encode())
        else:
            ret = False
            fps = 0
            if leds[0]:
                leds[0] = False
                sendtoall(f"led 0 0\n".encode())
        if fps == 0:
            tm.sleep(0.01)
            continue
        if not ret:
            if ret_counter <= 4:
                tm.sleep(2)
                ret_counter += 1
                print(f"no ret [{ret_counter}]")
            if ret_counter > 4:
                if ret_counter == 5:
                    print("too many losses! reconnecting...")
                vidcap.release()
                vidcap = cv2.VideoCapture(ldlfeed)
                reconnects += 1
                ss = "s" if reconnects > 1 else ""
                if not vidcap.isOpened():
                    vidcap = None
                    print(f"reconnect failed! [{reconnects} attempt{ss}]")
                else:
                    print(f"reconnect success! [after {reconnects} attempt{ss}]")
                    reconnects = 0
                    ret_counter = 0
            continue
        else:
            ret_counter = 0

        frame2 = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame2 = cv2.transpose(frame2)
        if smode == 0:
            scaled = cv2.resize(frame2, (480, screenw))
        fr_size = (vidcap.get(cv2.CAP_PROP_FRAME_WIDTH), vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if smode == 1:
            scaled = cv2.resize(frame2, (int(480 * fr_size[1] / fr_size[0] * (4/3 if sm2 else 1)), screenw))
        if smode == 2:
            scaled = cv2.resize(frame2, (480, int(fr_size[0]/fr_size[1]*(1.2 if sm2 else 1)*480)))
        latestframe = pg.surfarray.make_surface(scaled)

        with flock:
            capframes.append(latestframe)


def setupstream(url):
    import av
    s = av.open(url, mode="w", format="flv")
    st = s.add_stream(vencoder, rate=framerate)
    at = None
    if not mute:
        at = s.add_stream("aac", rate=audiorate)
        at.layout = "stereo"
    st.width = avscale[0]
    st.height = avscale[1]
    st.pix_fmt = "yuv420p"
    return (s, st, at, url)


# Streaming state managed by main
framelists = {}
audlists = {}
frame_start_evt = th.Event()
resetup = set()

def dowrite_th(strea : tuple, url):
    global resetup
    stream = tuple(strea)
    frame_start_evt.wait()
    while True:
        if stream in resetup:
            st = stream[3]
            try:
                stream[0].close()
            except:
                pass
            stream = setupstream(st)
            print(f"Reset stream {st[:20]}...")
            resetup.remove(stream)

        if len(framelists[url]) > 0:
            frame = framelists[url].pop(0)
        else:
            tm.sleep(0.01)
            continue

        if not mute:
            import av
            while len(audlists[url]) > 0:
                try:
                    af = audlists[url].pop(0)
                except:
                    break
                try:
                    for packet in stream[2].encode(af):
                        stream[0].mux(packet)
                except (av.BrokenPipeError, av.EOFError):
                    resetup.add(url)

        try:
            import av
            for packet in stream[1].encode(frame):
                stream[0].mux(packet)
        except (av.BrokenPipeError, av.EOFError):
            resetup.add(url)


def dowrite(outputs_list, avevent, avbuffer_ref, p_counter_ref, frame_idx_actual_ref, audio_ready_event):
    import av
    import fractions as frac

    streams2 = {}
    threads = []

    for out in outputs_list:
        stre = setupstream(out)
        streams2[out] = (stre, 0)
        framelists[out] = []
        audlists[out] = []
        h = th.Thread(target=dowrite_th, args=(stre, out))
        h.start()
        threads.append(h)

    frame_start_evt.set()
    audio_ready_event.set()
    last_p = 0
    while True:
        avevent.wait()
        avevent.clear()

        if last_p == p_counter_ref[0]:
            avevent.clear()
            continue
        sdata = pg.surfarray.array3d(avbuffer_ref[0]).transpose([1, 0, 2])
        frame = av.VideoFrame.from_ndarray(sdata, format="rgb24")
        frame = frame.reformat(format="yuv420p")
        frame.pts = frame_idx_actual_ref[0]
        frame.time_base = frac.Fraction(1, framerate)
        for out in outputs_list:
            framelists[out].append(frame)
        last_p = p_counter_ref[0] * 1


def dowriteaudio(outputs_list, audio_queue, audio_ready_event, frame_idx_actual_ref):
    import av
    import fractions as frac
    if mute:
        return
    audio_ready_event.wait()
    while True:
        try:
            buf = audio_queue.get_nowait()
        except:
            tm.sleep(0.01)
            continue

        n_int = len(buf) // 4
        af = av.AudioFrame(format="s16", layout="stereo", samples=n_int)
        af.sample_rate = audiorate
        af.planes[0].update(buf)
        af.time_base = frac.Fraction(1, 60)
        af.pts = frame_idx_actual_ref[0]
        for out in outputs_list:
            audlists[out].append(af)


def postmix(audio_queue):
    def _postmix(dev, mem):
        audio_queue.put_nowait(bytes(mem))
    return _postmix


def parse_ext_action(action, globals_dict):
    if action is None:
        return
    for act in action:
        if act[0] == "set_variable":
            varname = act[1]
            value = act[2]
            globals_dict[varname] = value
        elif act[0] == "call_function":
            funcname = act[1]
            args = act[2]
            func = globals_dict[funcname]
            func(*args)
        elif act[0] == "get_variable":
            varname = act[1]
            destvar = act[2]
            value = globals_dict[varname]
            globals_dict[destvar] = value
        elif act[0] == "execute_code":
            code = act[1]
            exec(code, globals_dict)
        elif act[0] == "quit":
            globals_dict["quit_requested"] = True
