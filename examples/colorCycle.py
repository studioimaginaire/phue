from phue import Bridge
# How to:
# 1. Run discoverSelected.py
# 2. Set hueLamps to the output of discoverSelected
# 3. Set bridge ip
# 4. Run programm

ip = '192.168.X.XXX'

br = Bridge(ip)
hueLamps = []

speed = 400
s = 254
b = 100

br.set_light(hueLamps, 'on', True)
br.set_light(hueLamps, 'hue', int(0)) # 0 bis 65535
br.set_light(hueLamps, 'sat', int(s)) # 0 bis 254
br.set_light(hueLamps, 'bri', int(b)) # 0 bis 254

while True:
    for x in range(0, 65535, speed):
        br.set_light(hueLamps, 'hue', int(x))
