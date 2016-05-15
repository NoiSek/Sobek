#! /usr/bin/env python3
from threading import Thread, Event
from models.Sobek import Sobek

#import curses
import queue
import time

def render_interface(events, terminate, window, app, init):
  log = []

  while not terminate.is_set():
    if init is not True:
      latest = events.get(block=True)
      log.append(latest)
      events.task_done()
    else:
      init = False

    log = log[-10:]

    window.clear()
    height, width = window.getmaxyx()
    window.addstr(0, 0, "Currently monitoring {} plants.".format(len(app.plants)))
    window.hline(1, 0, b"#", width - 1)
    window.addstr(2, 0, "Q - Exit, F - Force update")
    window.addstr(4, 0, "\n".join(log))

def take_input(events, terminate, window, app):
  while not terminate.is_set():
    try:
      action = window.getkey()

      if action.lower() == "q":
        events.put("{} - User exit.".format(time.strftime("%X")))
        terminate.set()

      elif action.lower() == "f":
        curses.flash()
        events.put("{} - Forced update.".format(time.strftime("%X")))
        app.force_update()

    except Exception:
      pass

def main(window):
  window.clear()
  window.nodelay(1)

  events = queue.Queue()
  terminate = Event()

  app = Sobek(events)
  app.init()
  
  interface = Thread(target=render_interface, args=(events, terminate, window, app, True))
  user_input = Thread(target=take_input, args=(events, terminate, window, app))

  interface.start()
  user_input.start()

  while not terminate.is_set():
    window.refresh()

  window.clear()
  window.refresh()

  interface.join()
  user_input.join()

if __name__ == "__main__":
  #curses.wrapper(main)
  #curses.clear()
  #curses.endwin()

  events = queue.Queue()
  terminate = Event()

  app = Sobek(events)
  app.init()

  while True:
    pass