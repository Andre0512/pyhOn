**This python package is unofficial and is not related in any way to Haier. It was developed by reversed engineered requests and can stop working at anytime!**

# pyhOn
[![PyPI - Status](https://img.shields.io/pypi/status/pyhOn)](https://pypi.org/project/pyhOn)
[![PyPI](https://img.shields.io/pypi/v/pyhOn?color=blue)](https://pypi.org/project/pyhOn)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyhOn)](https://www.python.org/)
[![PyPI - License](https://img.shields.io/pypi/l/pyhOn)](https://github.com/Andre0512/pyhOn/blob/main/LICENSE)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/pyhOn)](https://pypistats.org/packages/pyhon)  
Control your Haier, Candy and Hoover appliances with python!
The idea behind this library is, to make the use of all available commands as simple as possible.

## Installation
```bash
pip install pyhOn
```

### Quick overview
To get an idea of what is possible, use the commandline-tool `pyhOn`. This command requests all available options of connected appliances from the hOn api of your Haier Account.
```commandline
$ pyhOn --user example@mail.com --password pass123
========== WM - Waschmaschine ==========
data:
  attributes:
    parameters:
      ...
      texture: 1
      totalElectricityUsed: 28.71
      totalWashCycle: 35
      totalWaterUsed: 2494
      transMode: 0
      ...
settings:
  startProgram:
    rinseIterations:
      max: 5
      min: 3
      step: 1
    spinSpeed:
      - 0
      - 400
      - 600
      - 800
      ...
```

## Python-API
### List devices
```python
import asyncio
from pyhon import Hon

async def devices_example():
    async with Hon(USER, PASSWORD) as hon:
        for appliance in hon.appliances:
            print(appliance.nick_name)

asyncio.run(devices_example())
```

### Execute a command
```python
async with Hon(USER, PASSWORD) as hon:
    washing_machine = hon.appliances[0]
    pause_command = washing_machine.commands["pauseProgram"]
    await pause_command.send()
```

### Set command parameter
```python
async with Hon(USER, PASSWORD) as hon:
    washing_machine = hon.appliances[0]
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

## Translation
To get the translation of some keys like programs, you can use the translation command to see all of hOn's available translations
```commandline
$ pyhOn translate es
AC:
  APPLIANCE_RENAME:
    CONTENT_CHOOSE_NAME: Antes de continuar, debes elegir un nombre...
    DEFAULT_NAME: Aire acondicionado
    TITLE_CHOOSE_NAME: ¡Elije un nombre para tu aire acondicionado!
    TITLE_SAVE_NAME: Para cambiar el nombre de tu aparato:
...
```
This generates a huge output. It is recommended to pipe this into a file
```commandline
$ pyhOn translate fr > hon_fr.yaml
$ pyhOn translate en --json > hon_en.json
```

## Usage example
This library is used for the custom [HomeAssistant Integration "Haier hOn"](https://github.com/Andre0512/hOn).

## Contribution
Any kind of contribution is welcome!

| Please add your appliances data to our [hon-test-data collection](https://github.com/Andre0512/hon-test-data). <br/>This helps us to develop new features and not to break compatibility in newer versions. |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

