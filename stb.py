import json
import asyncio

rpi_env = True

# TODO:
# considerations:
# - clean exit and restart of pins!
#     try:
#        print("some gpio loop")
#     finally:
#         GPIO.cleanup() #this ensures a clean exit


class Settings:
    def __init__(self, room_name, relays, brains, master_reset):
        self.room_name = room_name
        self.relays = relays
        self.brains = brains
        # we may need and individual reset pin for each brain at some point
        self.master_reset = master_reset
        self.is_rpi_env = True


class Relay:
    def __init__(self, args):
        name, active_high, mode, brain_association, intput_pin, output_pin = args
        self.name = name
        self.active_high = active_high
        self.mode = mode
        self.brain_association = brain_association
        self.input = intput_pin
        self.output = output_pin
        self.status = False


class Brain:
    def __init__(self, name, relays, brain_no):
        self.name = name
        associated_relays = []
        for relay in relays:
            if relay.brain_association == brain_no + 1:
                associated_relays.append(relay)
        self.associated_relays = associated_relays


class STB:
    def __init__(self):
        self.settings = self.__load_stb()
        self.__gpio_init()
        print("stb init done")
        self.update_stb()

    def __load_stb(self):
        try:
            with open('config.json') as json_file:
                cfg = json.loads(json_file.read())
                room_name = cfg["Room_name"]
                relays = cfg["Relays"]
                brains = cfg["Brains"]
                pins_IO = cfg["Pins_IO"]
                master_reset = cfg["Master_reset"]
        except ValueError as e:
            print('failure to read config.json')
            print(e)
            exit()

        for i, relay in enumerate(relays):
            relay_data = relay + pins_IO[i]
            relays[i] = Relay(relay_data)

        for i, brain in enumerate(brains):
            brains[i] = Brain(brain, relays, i)

        settings = Settings(room_name, relays, brains, master_reset)
        return settings

    def __gpio_init(self):
        try:
            import RPi.GPIO as GPIO
            print("Running on RPi")
            GPIO.setmode(GPIO.BCM)
        except (RuntimeError, ModuleNotFoundError):
            print("Running without GPIOs on non Pi ENV / non RPi.GPIO installed machine")
            self.settings.self.is_rpi_env = False
            from fakeRPiGPIO import GPIO
        except OSError as e:
            print(e)
            print("sth went terribly wrong with GPIO import")
            exit()

        for relay in self.settings.relays:
            if relay.active_high:
                pud = GPIO.PUD_DOWN
            else:
                pud = GPIO.PUD_UP
            GPIO.setup(relay.input, GPIO.IN, pull_up_down=pud)
            GPIO.setup(relay.output, GPIO.OUT, pull_up_down=pud)

    # reads and updates the STB and sets/mirrors states
    async def update_stb(self):
        for relay in self.settings.relays:
            print()

    def set_stb(self):
        print()

    def __manage_relays(self):
        for relay in self.settings.relays:
            # auto = true, manual = false
            relay.status = GPIO.input(relay.input)
            if not relay.mode:
                GPIO.output(relay.output, relay.status)

# flask + rabbitsmq or kafka?

# https://www.shanelynn.ie/asynchronous-updates-to-a-webpage-with-flask-and-socket-io/
# https://flask-socketio.readthedocs.io/en/latest/

# https://realpython.com/flask-by-example-implementing-a-redis-task-queue/

# https://docs.python.org/3/whatsnew/3.8.html#asyncio
# https://www.youtube.com/watch?v=LYTiaSXso_4
# start async first do async.run(fnc_name)
# run parallel?
# async.gather(fn1, fn2, fn3)


# just here fore testing when running stb.py, usually this is imported
if __name__ == "__main__":
    print("")






