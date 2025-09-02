# ESPHome components and example config for Respeaker XVF3800

## _ATTENTION! Early alpha, use on your own risk!_
## Testing appreciated.

## Known issues:
1. Mute statuses from software mute and hardware mute don't reflect eachother. So even if your mute LED is off, device still can be muted (but looks like not vice-versa).
2. There's no buttons, so no way to stop timer or response except saying "stop", and no way to start pipeline manually.
3. No volume controls besides the software one (similar to Respeaker Lite Voice Kit).
4. No exposed light (LED is controlled via I2C).
5. ...?
