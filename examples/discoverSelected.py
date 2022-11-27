from phue import Bridge
# How to:
# 1. Set newDevice to True
# 2. Set bridge ip
# 3. Turn those lamps on, you wish to control
# 4. Press bind button of the bridge
# 5. Run programm

newDevice = False
ip = '192.168.0.100'

b = Bridge(ip)
if newDevice:
    b.connect()
discovered = []
try:
    for i in range(1,100):
        if b.get_light(i, 'on'):
            discovered.append(i)
except TypeError:
    print()
print(discovered)
