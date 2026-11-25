#essai python tm1637

import tm1637
import time

tm = tm1637.TM1637("/dev/gpiochip0", clk=23, dio=24)
hours = 0
minutes = 0
colon = True
tm.brightness(2)
while True:
    tm.numbers(hours, minutes, colon)
    minutes += 1
    colon = not colon
    if minutes >= 60:
        hours+=1
        minutes = 0
    time.sleep(0.5)