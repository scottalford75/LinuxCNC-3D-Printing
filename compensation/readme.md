## NAME 

compensation.py 

## SYNOPSIS 

**loadusr -Wn compensation** python compensation.py probe-results.txt *cubic*

## DEPENDENCIES 

The component has Python 2.7 or Python 3 dependencies of NumPy, SciPy and Enum34.

External Offsets are supported in LinuxCNC 2.8.0 and newer.

## DESCRIPTION 

### SUMMARY

**compensation.py** is a bed levelling / distortion correction user space compensation component for 3D Printing or engraving.

The component utilises the [external offsets](https://linuxcnc.org/docs/stable/html/motion/external-offsets.html) feature of LinuxCNC, which allows an axis to be offset by an external data source (in this case a Z compensation map). When enabled External Offsets (and hence Z compensation) is active during both world jogs and coordinated motion, offsetting the Z axis by the value of the map at that location.

The component uses the SciPy [griddata](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.griddata.html) function to interpolate between the probe data points at the specified resolution in X and Y.

Moves outside of the probe data region receive the compensation value at the edge of the compensation map so as not to have a jump / discontinuity, and hence the compensated value extends to the machine coordinate limits if the compensation map is non-zero at its edge.

![Compensation map](compensationMap.png)

### GENERATING AND LOADING A COMPENSATION MAP

To generate a Z compensation map, a probe data input file is specified in the *loadusr* string. An optional argument for the interpolation method can be either *nearest*, *linear* or *cubic*. If not specified the default method is cubic *(bicubic)* interpolation. Interpolation resolution and fade height are set according to HAL pins created by the component.

The probe data input file must have data on a regularly spaced grid. The file can be modified / updated at anytime while compensation is disabled (Don't probe whilst compensation is enabled). When compensation is next enabled, the compensation map will be recalculated.

A suitable probing program to create such a grid is [gridprobe.ngc](https://github.com/LinuxCNC/linuxcnc/blob/master/nc_files/gridprobe.ngc) (or [smartprobe.ngc](https://github.com/LinuxCNC/linuxcnc/blob/master/nc_files/smartprobe.ngc) if modified slightly to output data in the same format as *gridprobe.ngc*). A modified version, *smartprobe_compensation.ngc*, with these (and some further modifications) is in this repository.


### USAGE NOTES


It is recommended to familarise yourself with the [External Offsets Usage Notes](https://linuxcnc.org/docs/stable/html/motion/external-offsets.html#_usage). The most important points are summarised below:

<br/>

1. 
>The offsetting motion is not coordinated with teleop jogs nor with coordinated (G-code) motion.

This means that the ability of the machine to maintain the desired offset is dependent on multiple factors. If it is vital that the programmed path be followed to a defined tolerance, other tools that directly act on G-Code programs are likely more suitable.

The ability of the machine to maintain the compensated Z value or to conform to a probed surface depends on the proportion of the Z axis acceleration/velocity allocated to External Offsets vs. the acceleration/velocity of the other axes, the steepness of the surface gradient to follow, the probe grid resolution, interpolation resolution, and potentially the update rate of the component (which is every 0.05 seconds by default).

<br/>

2.
>External-offsets are intended for use with small offsets that are applied within the soft-limit bounds.

>When teleop jogging with external offsets enabled and non-zero values applied, encountering a soft limit will stop motion in the offending axis without a deacceleration interval. Similarly, during coordinated motion with external offsets enabled, reaching a soft limit will stop motion with no deacceleration phase. For this case, it does not matter if the offsets are zero.

>When motion is stopped with no deacceleration phase, system acceleration limits may be violated and lead to: 1) a following error (and/or a thump) for a servo motor system, 2) a loss of steps for a stepper motor system.

It is therefore not reccomended to approach the +Z and -Z soft limits with compensation enabled.

<br/>

3. 
When the component is enabled, it will cause a move in Z equal to the value of the map at that location. The opposite case applies when the component is disabled, causing a move in Z with an opposite sign but equal value to that of the map. The operator should therefore be mindful that enabling and disabling Z compensation does not cause a collision. This behaviour can be sidestepped by only enabling and disabling Z compensation at a position where the compensation value is 0.

<br/>

4. 
The authors of this software accept absolutely no liability for any harm or loss resulting from its use. It is EXTREMELY unwise to rely on software alone for safety.


## NAMING

The names for pins, parameters, and functions are prefixed as:  
**compensation**.name


## FUNCTIONS 

There are no discrete functions to call. Once loaded the component runs in user space in parallel with LinuxCNC.

## PINS 

| Pin | Type | Direction | Function|
| :--- | :--- | :---: | :--- |
| compensation.enable-in | bit | in | Enables Z compensation |
| compensation.enable-out | bit | out | Enables External Offset |
| compensation.eoffset | float | in | Value of External Offset |
| compensation.scale | float | out | Scale value for External Offset |
| compensation.count | s32 | out | Count value for External Offset |
| compensation.clear | bit | out | Clear External Offset |
| compensation.eoffset-limited | bit | in | External Offset is limited by soft limit |
| compensation.x-pos | float | in | X position command |
| compensation.y-pos | float | in | Y position command |
| compensation.z-pos | float | in | Z position command |
| compensation.fade-height  | float | in | Compensation will be faded out up to this value |
| compensation.resolution  | float | in | The resolution of the interpolation |

eoffset == scale * count

## INSTALLATION

For the component to function, External Offsets must be enabled for the Z axis and the component linked to the External Offsets pins:


### CONFIG MODIFICATIONS

Place the compensation.py in your configuration ini directory.


### INI FILE MODIFICATIONS

Add the following lines to enable [HALUI](https://linuxcnc.org/docs/stable/html/gui/halui.html) to make the relative xyz position HAL pins available:

	[HAL]  
	HALUI = halui

And add the following line to add an OFFSET_AV_RATIO parameter:

	[AXIS_Z]  
	OFFSET_AV_RATIO = 0.2

This may be a value between 0 (External Offsets disabled) and 0.9, where the value is the proportion of the axis max velocity and acceleration allocated to External Offsets. For more information, see the [documentation](https://linuxcnc.org/docs/stable/html/motion/external-offsets.html#_ini_file_settings).


### HAL FILE MODIFICATIONS

Add the following lines:

	loadusr -Wn compensation python compensation.py probe-results.txt cubic

	net eoffset-xpos 	<= halui.axis.x.pos-relative	=> compensation.x-pos
	net eoffset-ypos	<= halui.axis.y.pos-relative	=> compensation.y-pos
	net eoffset-zpos	<= halui.axis.z.pos-relative	=> compensation.z-pos
 	net eoffset-value 	<= axis.z.eoffset 		=> compensation.eoffset
  	net eoffset-limited 	<= motion.eoffset-limited 	=> compensation.eoffset-limited
	net eoffset-enable	<= compensation.enable-out	=> axis.z.eoffset-enable
	net eoffset-scale	<= compensation.scale		=> axis.z.eoffset-scale
	net eoffset-counts	<= compensation.counts 		=> axis.z.eoffset-counts
	net eoffset-clear	<= compensation.clear 		=> axis.z.eoffset-clear
	net compensation-on	<= compensation.enable-in

To enable/disable compensation by setting the signal directly: 

	sets compensation-on 1
 	sets compensation-on 0
 Or connect the signal to a hal pin associated with a suitable GUI button or M code so it can be easily toggled.
