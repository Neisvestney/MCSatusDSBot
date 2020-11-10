import configparser
import os

c = configparser.ConfigParser()

c['SETTINGS'] = {"DISCORD_TOKEN": "<Token>"}
c['SERVERS'] = {}


def save():
    with open('settings.conf', 'w') as configfile:
        c.write(configfile)


if not os.path.exists('settings.conf'):
    save()
    print("Created config file. Edit it")
    exit()

c.read('settings.conf')
