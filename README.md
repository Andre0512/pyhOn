**This python package is unofficial and is not related in any way to Haier. It was developed by reversed engineered requests and can stop working at anytime!**

# pyhOn
[![PyPI - Status](https://img.shields.io/pypi/status/pyhOn)](https://pypi.org/project/pyhOn)
[![PyPI](https://img.shields.io/pypi/v/pyhOn?color=blue)](https://pypi.org/project/pyhOn)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyhOn)](https://www.python.org/)
[![PyPI - License](https://img.shields.io/pypi/l/pyhOn)](https://github.com/Andre0512/pyhOn/blob/main/LICENCE)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/pyhOn)](https://pypistats.org/packages/pyhOn)  
Control your Haier appliances with python!
The idea behind this library is, to make the use of all available commands as simple as possible.

## Installation
```bash
pip install pyhOn
```

### Quick overview
To get an idea of what is possible, use the commandline-tool `pyhOn`. This command requests all available options of connected appliances from the hOn api of your Haier Account.
```commandline
$ pyhOn --user example@mail.com --password pass123
========== Waschmaschine ==========
commands:
  pauseProgram: pauseProgram command
  resumeProgram: resumeProgram command
  startProgram: startProgram command
  stopProgram: stopProgram command
data:
  actualWeight: 0
  airWashTempLevel: 0
  airWashTime: 0
  antiAllergyStatus: 0
...
```
The claim is, to see everything what you can see in your hOn app and to execute everything you can execute there.

## Python-API
### List devices
```python
import asyncio
from pyhon import HonConnection

async def devices_example():
    async with HonConnection(USER, PASSWORD) as hon:
        for device in hon.devices:
            print(device.nick_name)

asyncio.run(devices_example())
```

### Execute a command
```python
async with HonConnection(USER, PASSWORD) as hon:
    washing_machine = hon.devices[0]
    pause_command = washing_machine.commands["pauseProgram"]
    await pause_command.send()
```

### Set command parameter
Use `device.settings` to get all variable parameters.  
Use `device.parmeters` to get also fixed parameters. 
```python
async with HonConnection(USER, PASSWORD) as hon:
    washing_machine = hon.devices[0]
    start_command = washing_machine.commands["startProgram"]
    for name, setting in start_command.settings:
        print("Setting", name)
        print("Current value", setting.value)
        if setting.typology == "enum":
            print("Available values", setting.values)
            setting.value = setting.values[0]
        elif setting.typology == "range":
            print("Min value", setting.min)
            print("Max value", setting.max)
            print("Step value", setting.step)
            setting.value = setting.min + setting.step
```

## Tested devices
- Haier Washing Machine HW90

_Unfortunately I don't have any more Haier appliances..._

## Usage example
This library is used for the custom [HomeAssistant Integration "Haier hOn"](https://github.com/Andre0512/hOn).
