# GoveePy
[![Documentation Status](https://readthedocs.org/projects/goveepy/badge/?version=latest)](https://goveepy.readthedocs.io/en/latest/?badge=latest)

GoveePy is a WIP Python wrapper for the Govee API.

## Table of Contents

- [GoveePy](#goveepy)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Usage](#usage)

## Installation

Installation is easy just do  
`pip install GoveePy`

## Usage

```python
from govee import Govee

g = Govee("API-KEY")
g.get_devices()

device = g.get_device_by_name("Living Room Light")
if device is None:
    exit()

device.turn_on()
device.set_brightness(100)
```

You can also use the Local API.   
Make sure you have enabled it for the light you want to use.

```python
from govee import GoveeLocal

g = GoveeLocal()
g.get_devices()
device = g.get_device_by_ip("192.169.0.143")

if device is None:
    exit()

device.turn_on()
device.set_brightness(100)

```


