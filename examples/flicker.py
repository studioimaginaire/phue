import random
from time import sleep
from phue import Bridge
b = Bridge()
b.connect()
lights = b.lights

def select_multiple_lights():
  '''
  Selects a random number of lights from the list of lights every time, resulting in a 'flickering' look.
  '''
  return random.choices(range(1,len(lights)+1),k=random.randint(1,len(lights)))

def multi_modal():
      '''
      Generates a random transition time between 0.2 and 0.7 seconds folowing a multi-modal distribution.
      This results in really fast transitions, but also slow transitions.
      '''
      return [2+int(random.betavariate(1,9)*5),2+int(random.betavariate(9,1)*5)][bool(random.getrandbits(1))]

def candle_flicker():
  '''
  Sends a command to change a certain number of lights a different color temperature every time. ct_inc was finicky, so I've used ct instead.
  All inputs use a beta distribution, as it looked more natural. A similar look can be achieved using a triangular distribution as well.
  '''
  b.set_light(select_multiple_lights(), {'transitiontime' : multi_modal(), 'on' : True, 'bri' : 1+int(random.betavariate(2,5)*253), 'ct' : 153+int(random.betavariate(9,4)*347)})
  
while True:
  candle_flicker()
  sleep(random.random())
