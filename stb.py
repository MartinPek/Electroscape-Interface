from random import random
import json

# TODO:
# Test of the clean exit

rpi_env = True

'''
    don't ask, everything on the frontend get smeared into strings
    bool_dict = {"true": True, "false": False}
    bool_convert = {"True": "false", "Talse": "true"}
'''
bool_dict = {"on": True, "off": False}


class Settings:
    def __init__(self, room_name, master_reset):
        self.room_name = room_name
        # we may need and individual reset pin for each brain at some point
        self.master_reset = master_reset
        self.is_rpi_env = True


class Relay:

    def get_frontend_mode(self):
        if self.mode:
            return "true"
        else:
            return "false"

    def __init__(self, name, active_high, mode, brain_association, intput_pin, output_pin, index):
        self.name = name
        self.active_high = active_high
        self.mode = mode
        self.brain_association = brain_association
        self.input = intput_pin
        self.output = output_pin
        self.status = 0
        self.index = index
        self.mode_frontend = self.get_frontend_mode()


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
        self.updates = []
        self.settings, self.relays, self.brains = self.__load_stb()
        self.GPIO = self.__gpio_init()
        self.update_stb()
        print("stb init done")

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
            relay_data = relay + pins_IO[i] + [i]
            relays[i] = Relay(*relay_data)

        for i, brain in enumerate(brains):
            brains[i] = Brain(brain, relays, i)

        settings = Settings(room_name, master_reset)
        return settings, relays, brains

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

        for relay in self.relays:
            if relay.active_high:
                pud = GPIO.PUD_DOWN
            else:
                pud = GPIO.PUD_UP
            GPIO.setup(relay.input, GPIO.IN, pull_up_down=pud)
            GPIO.setup(relay.output, GPIO.OUT, pull_up_down=pud)

        return GPIO

    def set_override(self, relay_index, value, test):
        # do yourself a favour and dont pass values into html merely JS,
        # converting bools into 3 different languages smeard into json is not fun
        print("testval: {}".format(test))
        relay = self.relays[int(relay_index)]
        '''
        try:
            value = not bool_dict[value]
            relay.mode = value
        except KeyError:
            print("KEYERROR!")
        '''
        relay.mode = not relay.mode
        relay.mode_frontend = relay.get_frontend_mode()

    # changes form the frontend applied to the GPIO pins
    def set_relay(self, relay, status):
        self.GPIO.output(relay.output, status)
        print("GPIO has been overriden, WIP automatic logdump needs to hook in here")

    # reads and updates the STB and sets/mirrors states
    def update_stb(self):
        print("update_stb")
        print("adding some random fake updates")
        for relay_no, relay in enumerate(self.relays):
            # auto = true, manual = false
            # new_status = self.GPIO.input(relay.input)
            new_status = round(random())
            if new_status != relay.status:
                relay.status = new_status
                self.updates.append([relay_no, relay.status])
            # this will mirror the GPIOs in Automatic mode

            if not relay.mode:
                print("mirroring")
                self.GPIO.output(relay.output, relay.status)
        print(self.updates)

    def cleanup(self):
        self.GPIO.cleanup()

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






