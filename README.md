**This python package is unofficial and is not related in any way to Haier. It was developed by reversed engineered requests and can stop working at anytime!**

# pyhOn
Control your Haier appliances with python!
### Quick overview
To see the available options of the appliances from your Haier Account, use the commandline-tool `pyhOn`
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
    washing_machine = hon[0]
    pause_command = washing_machine.commands["pauseProgram"]
    await pause_command.send()
```
