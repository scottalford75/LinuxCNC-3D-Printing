/********************************************************************
* Description:  corexy.c
*
*               This file, 'corexy.c', is a HAL component that
*               provides a corexy modification for a trivial kinematics
*				implementation.
*
*				A corexy machine does not follow the LinuxCNC joint
*				model where a joint represents a single degree of
*				freedom for the mechanism. Standard homing then
*				becomes possible.
*
*				Inverse Kinematics:
*
*				motor0 = x + y
*				motor1 = x - y
*
*				Forward Kinematics
*
*				x = (motor0 + motor1)/2
*				y = (motor0 - motor1)/2
*
*
* Author: Scott Alford
* License: GPL Version 2
*
*		Credit to GP Orcullo and PICnc V2 which originally inspired this
*		and portions of this code is based on stepgen.c by John Kasunich
*		and hm2_rpspi.c by Matsche
*
* Copyright (c) 2019	All rights reserved.
*
* Last change:
********************************************************************/


#include "rtapi.h"			/* RTAPI realtime OS API */
#include "rtapi_app.h"		/* RTAPI realtime module decls */
#include "hal.h"			/* HAL public API decls */

#include <math.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>


#define MODNAME "corexy"
#define PREFIX "corexy"

MODULE_AUTHOR("Scott Alford");
MODULE_DESCRIPTION("CoreXY translation for Trivkins");
MODULE_LICENSE("GPL v2");

/***********************************************************************
*                STRUCTURES AND GLOBAL VARIABLES                       *
************************************************************************/

typedef struct {
	hal_float_t 	*xpos_cmd;			// pin: X position command (position units)
	hal_float_t 	*ypos_cmd;			// pin: Y position command (position units)
	hal_float_t 	*xpos_fb;			// pin: X position feedback (position units)
	hal_float_t 	*ypos_fb;			// pin: Y position feedback (position units)
	hal_float_t 	*m0pos_cmd;		// pin: Motor 0 position command (position units)
	hal_float_t 	*m1pos_cmd;		// pin: Motor 1 position command (position units)
	hal_float_t 	*m0pos_fb;			// pin: X position feedback (position units)
	hal_float_t 	*m1pos_fb;			// pin: Y position feedback (position units)
} data_t;

static data_t *data;

/* other globals */
static int 			comp_id;			/* component ID */
static const char 	*modname = MODNAME;
static const char 	*prefix = PREFIX;


/***********************************************************************
*                  LOCAL FUNCTION DECLARATIONS                         *
************************************************************************/

static void pos_cmd();
static void pos_fb();


/***********************************************************************
*                       INIT AND EXIT CODE                             *
************************************************************************/

int rtapi_app_main(void)
{
    char name[HAL_NAME_LEN + 1];
	int n, retval;


    // connect to the HAL, initialise the component
    comp_id = hal_init(modname);
    if (comp_id < 0)
	{
		rtapi_print_msg(RTAPI_MSG_ERR, "%s ERROR: hal_init() failed \n", modname);
		return -1;
    }

	// allocate shared memory
	data = hal_malloc(sizeof(data_t));
	if (data == 0) {
		rtapi_print_msg(RTAPI_MSG_ERR,
			"%s: ERROR: hal_malloc() failed\n", modname);
		hal_exit(comp_id);
		return -1;
	}


    // export pins
	retval = hal_pin_float_newf(HAL_IN, &(data->xpos_cmd),
			comp_id, "%s.xpos-cmd", prefix);
	if (retval != 0) { return retval; }

	retval = hal_pin_float_newf(HAL_IN, &(data->ypos_cmd),
			comp_id, "%s.ypos-cmd", prefix);
	if (retval != 0) { return retval; }
		
	retval = hal_pin_float_newf(HAL_OUT, &(data->xpos_fb),
			comp_id, "%s.xpos-fb", prefix);
	if (retval != 0) { return retval; }

	retval = hal_pin_float_newf(HAL_OUT, &(data->ypos_fb),
			comp_id, "%s.ypos-fb", prefix);
	if (retval != 0) { return retval; }
	
	retval = hal_pin_float_newf(HAL_OUT, &(data->m0pos_cmd),
			comp_id, "%s.m0pos-cmd", prefix);
	if (retval != 0) { return retval; }

	retval = hal_pin_float_newf(HAL_OUT, &(data->m1pos_cmd),
			comp_id, "%s.m1pos-cmd", prefix);
	if (retval != 0) { return retval; }
		
	retval = hal_pin_float_newf(HAL_IN, &(data->m0pos_fb),
			comp_id, "%s.m0pos-fb", prefix);
	if (retval != 0) { return retval; }

	retval = hal_pin_float_newf(HAL_IN, &(data->m1pos_fb),
			comp_id, "%s.m1pos-fb", prefix);
	if (retval != 0) { return retval; }

	error:
	if (retval < 0) {
		rtapi_print_msg(RTAPI_MSG_ERR,
		        "%s: ERROR: pin export failed with err=%i\n",
		        modname, retval);
		hal_exit(comp_id);
		return -1;
	}



	// Export functions
	rtapi_snprintf(name, sizeof(name), "%s.pos-cmd", prefix);
	retval = hal_export_funct(name, pos_cmd, data, 1, 0, comp_id);
	if (retval < 0) {
		rtapi_print_msg(RTAPI_MSG_ERR,
		        "%s: ERROR: pos_cmd function export failed\n", modname);
		hal_exit(comp_id);
		return -1;
	}

	rtapi_snprintf(name, sizeof(name), "%s.pos-fb", prefix);
	retval = hal_export_funct(name, pos_fb, data, 1, 0, comp_id);
	if (retval < 0) {
		rtapi_print_msg(RTAPI_MSG_ERR,
		        "%s: ERROR: pos_cmd function export failed\n", modname);
		hal_exit(comp_id);
		return -1;
	}


	rtapi_print_msg(RTAPI_MSG_INFO, "%s: installed driver\n", modname);
	hal_ready(comp_id);
    return 0;
}

void rtapi_app_exit(void)
{
    hal_exit(comp_id);
}


/***********************************************************************
*                   LOCAL FUNCTION DEFINITIONS                         *
************************************************************************/

void pos_cmd()
{
	*data->m0pos_cmd = *data->xpos_cmd + *data->ypos_cmd;
	*data->m1pos_cmd = *data->xpos_cmd - *data->ypos_cmd;
}


void pos_fb()
{
	*data->xpos_fb = (*data->m0pos_fb + *data->m1pos_fb)/2;
	*data->ypos_fb = (*data->m0pos_fb - *data->m1pos_fb)/2;
}


