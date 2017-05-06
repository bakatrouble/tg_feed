from time import sleep

import yaml
import tg_feed

config = yaml.load(open('config.yaml'))
tg_feed.init(config)

while True:
    tg_feed.do_work()
    sleep(60 * 5)
