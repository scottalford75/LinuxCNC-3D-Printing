# CoreXY translation for TrivKins

When I developed the [Hypercube Evolution 3D printer] (https://www.thingiverse.com/thing:2254103) I chose the CoreXY motion system for its simplicity and low moving mas.

Originally the printer was controlled by a standard Marlin software that supports CoreXY and has no issues to Home this type of motion system.

Prior to LinuxCNC 2.8 homing in LinuxCNC was an *AXIS* based process. This also meant that when using CoreXY kinematics, homing also worked as expected. However, since homing has now moved to a *JOINT* based process, homing of a CoreXY system is not as easy to implement or reliable in my experience.

I can understand the move to *JOINT* based homing. Typically, most motion systems have MOTOR == JOINT with a homing switch / index directly related to the motor position.

However, CoreXY systems typically use homing / limit switches located on the Axes of the machine. This makes homing more difficult; we move one Joint (Motor) and get motion in both X and Y when we are trying to make a switch on X or Y.

## Solution

My solution is to treat the machine as a TrivKins kinematics machine but to wrap the kinematics motion component with a CoreXY translation for X and Y (Joint 0 and 1) to Motors 0 and 1. It works nicely and keeps the homing logic as we would normally expect.

```
addf corexy.pos-fb servo-thread
addf motion-command-handler servo-thread
addf motion-controller servo-thread
addf corexy.pos-cmd servo-thread
```

## Installtion

Like other HAL components it is simply installed using Halcompile and adding the compent to your HAL file and netting everying together. There is an example HAL file in the repo.

```
$ halcompile --install corexy.c
```

