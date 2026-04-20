import time as tm
import math as m

seconds = 60
minutes = 60*60
hours = 60*60*60

chars = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[°]^_'abcdefghijklmnopqrstuvwxyz{|}~ "
chars_symbol = " ↑↓"

# Profiling infrastructure
profile = False
profiling = {
    "text": 0,
    "ops": 0
}

def clear_profile():
    global profiling
    profiling = {
        "text": 0,
        "ops": 0
    }

pr_start = tm.perf_counter()
def profiling_start():
    global pr_start
    pr_start = tm.perf_counter()

def profiling_end(section):
    profiling[section] += (tm.perf_counter() - pr_start)

def profiling_sect(section):
    def profiling_wrap(func):
        def wrapper(*args, **kwargs):
            if profile:
                start = tm.perf_counter()
                val = func(*args, **kwargs)
                end = tm.perf_counter()
                diff = end - start
                profiling[section] += diff
                return val
            else:
                return func(*args, **kwargs)
        return wrapper
    return profiling_wrap

def sign(n):
    if n > 0:
        return 1
    if n < 0:
        return -1
    return 0

def splubby_the_return(tx):
    if tx[0] == "0":
        return tx[1:]
    else:
        return tx

def get_color_steps(c1, c2, steps):
    stepss = []
    #steps is the amount of steps generated
    for i in range(steps):
        stepss.append((
            c1[0] + (c2[0] - c1[0]) * (i / (steps-1)),
            c1[1] + (c2[1] - c1[1]) * (i / (steps-1)),
            c1[2] + (c2[2] - c1[2]) * (i / (steps-1))
        ))
    return stepss

def time_fmt(time):
    if time >= minutes:
        return str(int(time/minutes)) + " minutes " + str(int((time/seconds) % 60)) + " seconds"
    else:
        return str(int(time/seconds)) + " seconds"

def shorten_phrase(phrase : str):
    if len(phrase) < 9:
        return phrase
    replacelist = {"Ice Crystals": "Ice"}
    if phrase in replacelist:
        return replacelist[phrase]
    if "Shower" in phrase:
        t = phrase.replace("Shower", "Shwr")
        if len(t) < 9:
            return t
        t = phrase.replace("Showers", "Shwr")
        if len(t) < 9:
            return t
        t = phrase.replace("Shower", "Shw")
        if len(t) < 9:
            return t.replace("Snow Shw", "Hvy Snow").replace("Rain Shw", "Hvy Rain")
        t = phrase.replace("Showers", "Shw")
        if len(t) < 9:
            return t.replace("Snow Shw", "Hvy Snow").replace("Rain Shw", "Hvy Rain")
        return phrase.replace("Showers", "Shw")
    if "Light" in phrase:
        return phrase.replace("Light", "Lgt")
    if "Cldy" in phrase:
        if phrase[1] == " ":
            phrase = f'{phrase[0]} Cloudy'
        else:
            phrase = "Cloudy"
    if "Heavy" in phrase:
        return phrase.replace("Heavy", "Hvy")
    if phrase.endswith("/Wind"):
        return phrase.split("/")[0]
    if phrase.split(" ")[-1] == "Showers":
        return "Showers"
    return phrase

def mapper(ref_points, lat, lon):
    (lat1, lon1), (x1, y1) = ref_points[0]
    (lat2, lon2), (x2, y2) = ref_points[1]

    scale_lat = (y2 - y1) / (lat2 - lat1)
    scale_lon = (x2 - x1) / (lon2 - lon1)

    x_offset = x1 - lon1 * scale_lon
    y_offset = y1 - lat1 * scale_lat

    x = lon * scale_lon + x_offset
    y = lat * scale_lat + y_offset
    return (x, y)

def lerp(x, y, n):
    return x * n + y * (1-n)

def safedivide(x, y):
    if y == 0:
        return 0
    else:
        return x/y

@profiling_sect("ops")
def padtext(text, l):
    text = str(text)
    if len(text) >= l:
        return text
    final = " "*(l-len(text))
    final += text
    return final

@profiling_sect("ops")
def textmerge(t1, t2):
    final = ""
    for i in range(max(len(t1), len(t2))):
        if i >= len(t1):
            final += t2[i]
        elif i >= len(t2):
            final += t1[i]
        elif t1[i] == " ":
            final += t2[i]
        elif t2[i] == " ":
            final += t1[i]
        else:
            final += t1[i]
    return final

@profiling_sect("ops")
def drawingfilter(text, idx):
    finaltext = ""
    left = idx*1
    for char in text:
        if char == " ":
            finaltext += " "
            continue
        left -= 1
        if left == 0:
            break
        finaltext += char

def wraptext(text, ll=32):
    final = []
    paragraphs = text.split("\n")
    for pgh in paragraphs:
        if pgh == '':
            final.append('')
            continue
        words = pgh.split(" ")
        nl = ""
        for word in words:
            if (len(nl) + len(word)) > ll:
                final.append(nl + "")
                nl = ""
            nl += word
            nl += " "
        final.append(nl.strip())
    return final

def drawing(text, amount, ram=False):
    final = ""
    am = amount*1
    if am > len(text):
        am -= len(text)
        if ram:
            return text, am
        return text
    for char in text:
        if am <= 0:
            break
        if char == " ":
            final += char
            continue
        am -= 1
        final += char
    if (am % 1) != 0 and amount < len(text):
        txl = list(final)
        txl.insert(-1, "≠")
        final = "".join(txl)
    if ram:
        return final, am
    return final

def windreduce(text):
    rep = {"NNE": "NE", "ENE": "NE", "ESE": "SE", "SSE": "SE", "SSW": "SW", "WSW": "SW", "WNW": "NW", "NNW": "NW"}
    if text in rep: return rep[text]
    return text

class AccurateClock():
    def __init__(self):
        #next_frame holds the target time for the next frame (perf_counter)
        self.next_frame = tm.perf_counter()
        #amount of time in seconds to sleep before switching wait method
        self.spin_threshold = 0.002
    def tick(self, fps):
        now = tm.perf_counter()
        frame_duration = 1.0 / float(fps)

        if now - self.next_frame > 0.5:
            #reset timer
            self.next_frame = now + frame_duration

        #if we're behind, speed up a little
        if self.next_frame <= now:
            self.next_frame = now + frame_duration
            return 1000.0 / float(fps)

        #wait time
        wait = self.next_frame - now

        if wait > self.spin_threshold:
            tm.sleep(max(0.0, wait - self.spin_threshold))

        while tm.perf_counter() < self.next_frame:
            pass

        # schedule next frame
        self.next_frame += frame_duration

        return 1000.0 / float(fps)
