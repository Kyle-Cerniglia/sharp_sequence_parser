"""
FILE: ssp_carbonstar.py
DESCRIPTION: This file hosts the main function and unique functions for generating sequences for the Carbonstar.
             Designed for a Minicam8M mounted to a Carbonstar 150 with a Pegasus 3 autofocuser.
"""

import sys
import math
from enum import Enum
from enum import auto
from typing import Optional
import ssp_common

# Filters
class Filters(Enum):
    LUMINANCE = 1
    RED = 2
    GREEN = 3
    BLUE = 4
    SII = 5
    HA = 6
    OIII = 7
    NONE = 8
    RGB = 9

# Sharpcap preset names
class Presets(Enum):
    CARBON_LRGB = "MC8_LRGB"
    CARBON_NB = "MC8_NB"

# Exposure durations for each filter (s)
class Exposure(Enum):
    LUMINANCE = 30
    RED = 30
    GREEN = 30
    BLUE = 30
    SII = 180
    HA = 180
    OIII = 180
    NONE = 2
    RGB = 30

# Platesolving durations for each filter (s)
class Plate(Enum):
    LUMINANCE = 2
    RED = 2
    GREEN = 2
    BLUE = 2
    SII = 2
    HA = 2
    OIII = 2
    NONE = 2
    RGB = 2

# Time divider for each filter (Adust this value to get actual sequence duration to match the intended sequence duration)
class Timediv(Enum):
    LUMINANCE = 33.44
    RED = 33.44
    GREEN = 33.44
    BLUE = 33.44
    SII = 195.26
    HA = 195.26
    OIII = 195.26
    NONE = 33.44
    RGB = 33.44

# Dither frequency for each filter (Frames per dither event)
class Dither(Enum):
    LUMINANCE = 20
    RED = 20
    GREEN = 20
    BLUE = 20
    SII = 3
    HA = 3
    OIII = 3
    NONE = 20
    RGB = 20

# Cooler parameters
class Cool(Enum):
    RATE = 25
    TOLERANCE = 1

# Local function variables
outfile = None
temperature = None
filter_type = None
exposure_time = None
timediv = None
dither = None
plate_exposure_time = None
rough_focus = None
rgb_flag = False
catalog_search = ""
catalog_used = False

"""
FUNCTION: init_session
DESCRIPTION: Data initializer
INPUTS:
out_file: Output file
temp: Cooler temperature (C)
filter_val: Filter selection
exposure_val: Exposure duration (s)
timediv_val: Time divider
dither_val: Dither frequency (Frames per dither)
plate_exposure_time: Platesolving exposure duration (s)
rough_focus_val: Rough autofocus position
OUTPUTS: None
"""
def init_session(
    out_file,
    temp=None,
    filter_val=None,
    exposure_val=None,
    timediv_val=None,
    dither_val=None,
    plate_exposure_val=None,
    rough_focus_val=None,
) -> None:
    """
    Replaces Session.__init__().
    Stores the session data in globals instead of self fields.
    """

    global outfile
    global temperature
    global filter_type
    global exposure_time
    global timediv
    global dither
    global plate_exposure_time
    global rough_focus

    outfile = out_file
    temperature = temp
    filter_type = filter_val
    exposure_time = exposure_val
    timediv = timediv_val
    dither = dither_val
    plate_exposure_time = plate_exposure_val
    rough_focus = rough_focus_val

"""
FUNCTION: set_filter
DESCRIPTION: User selects the filter for the session.
INPUTS: None
OUTPUTS: None
"""
def set_filter() -> None:
    global filter_type
    global rgb_flag

    filter_in = input(
        "Select your filter:\n"
        "[1] = Luminance\n"
        "[2] = Red\n"
        "[3] = Green\n"
        "[4] = Blue\n"
        "[5] = SII\n"
        "[6] = Ha\n"
        "[7] = OIII\n"
        "[8] = None\n"
        "[9] = RGB\n"
    )

    filter_type = Filters(int(filter_in))

    if filter_type == Filters.RGB:
        rgb_flag = True
    else:
        rgb_flag = False

"""
FUNCTION: preset
DESCRIPTION: Selects the sharpcap preset depending on what kind of filter was selected (BB vs NB).
INPUTS: None
OUTPUTS: None
"""
def preset() -> None:
    global outfile
    global filter_type

    if filter_type in [Filters.LUMINANCE, Filters.RED, Filters.GREEN, Filters.BLUE]:
        preset_val = Presets.CARBON_LRGB
    else:
        preset_val = Presets.CARBON_NB
    outfile.write(f"    LOAD PROFILE {preset_val.value}\n")

"""
FUNCTION: identify_target_name
DESCRIPTION: Identifies the target name based on the target and the active filter.
INPUTS:
target_name: Target name
OUTPUTS: None
"""
def identify_target_name(target_name: str) -> None:
    global outfile
    global filter_type

    if filter_type == Filters.LUMINANCE:
        ssp_common.write_target_name(outfile, target_name, "l")
    elif filter_type == Filters.RED:
        ssp_common.write_target_name(outfile, target_name, "r")
    elif filter_type == Filters.GREEN:
        ssp_common.write_target_name(outfile, target_name, "g")
    elif filter_type == Filters.BLUE:
        ssp_common.write_target_name(outfile, target_name, "b")
    elif filter_type == Filters.SII:
        ssp_common.write_target_name(outfile, target_name, "s")
    elif filter_type == Filters.HA:
        ssp_common.write_target_name(outfile, target_name, "h")
    elif filter_type == Filters.OIII:
        ssp_common.write_target_name(outfile, target_name, "o")
    else:
        ssp_common.write_target_name(outfile, target_name, "")

"""
FUNCTION: create_target
DESCRIPTION: Create an imaging target sequence (Unique to this telescope setup, incorporating common and local functions).
INPUTS: None
OUTPUTS: None
"""
def create_target() -> None:
    global outfile
    global catalog_used
    global catalog_search
    global dither
    global temperature
    global rough_focus
    global exposure_time
    global timediv

    # Configure image formatting
    ssp_common.set_format(outfile, True)
    
    # Configure sharpcap preset
    preset()
    
    # Connect to mount
    ssp_common.connect_mount(outfile)

    # Configure autofocus
    rough_focus = ssp_common.set_autofocus()

    # Configure target
    if input("Lookup catalog target? (y/n)\n") == "y":
        ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used, catalog_search = ssp_common.coords_catalog()
    else:
        ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used = ssp_common.coords_direct()

    # Set target name
    if catalog_used:
        target_name = catalog_search
    else:
        target_name = input("Enter target name\n")
        
    identify_target_name(target_name)

    # Slew and plate solve to a position 3 degrees off target
    ssp_common.goto_plate_solve(outfile, 3, 2, True, ra_h, ra_m, ra_s, dec_d, dec_m, dec_s)

    # Platesolve and correct position twice
    ssp_common.goto_plate_solve(outfile, 0, 2, True, ra_h, ra_m, ra_s, dec_d, dec_m, dec_s)
    ssp_common.goto_plate_solve(outfile, 0, 2, True, ra_h, ra_m, ra_s, dec_d, dec_m, dec_s)

    # Autofocus
    frame_subtraction = 0
    if rough_focus != -1:
        frame_subtraction = ssp_common.run_autofocus(outfile, rough_focus, exposure_time)

    # Set filter
    ssp_common.set_filter(outfile, filter_type.value)

    # Set guiding
    ssp_common.start_guiding(outfile)

    # Set cooler temperature
    ssp_common.cool_camera(outfile, Cool, temperature)

    # Set exposure
    ssp_common.set_exposure(outfile, exposure_time)

    # Set frame capture
    frame_qty = ssp_common.frame_calc(outfile, timediv, frame_subtraction, 1)
    ssp_common.write_light_capture(outfile, frame_qty, dither)
    
    #Finish target
    ssp_common.stop_guiding(outfile)

"""
FUNCTION: create_rgb_target
DESCRIPTION: Create an imaging target sequence (Unique to this telescope setup, incorporating common and local functions).
             This function is selected if the user selects the 'RGB' filter option. It will split the imaging time equally
             between the Red, Green, and Blue filter in a single imaging session.
INPUTS: None
OUTPUTS: None
"""
def create_rgb_target() -> None:
    global outfile
    global catalog_used
    global catalog_search
    global dither
    global temperature
    global rough_focus
    global exposure_time
    global timediv

    # Setup
    outfile.write("    DELAY 1\n")
    outfile.write("    STILL MODE\n")

    # Configure image formatting
    ssp_common.set_format(outfile, True)
    
    # Connect to mount
    preset()
    
    # Connect to mount
    ssp_common.connect_mount(outfile)

    # Configure autofocus
    rough_focus = ssp_common.set_autofocus()

    # Configure target
    if input("Lookup catalog target? (y/n)\n") == "y":
        ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used, catalog_search = ssp_common.coords_catalog()
    else:
        ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used = ssp_common.coords_direct()

    # Set target name
    if catalog_used:
        target_name = catalog_search
    else:
        target_name = input("Enter RGB target name\n")

    # Image RED
    ssp_common.write_target_name(outfile, target_name, "r")

    # Slew and plate solve to a position 3 degrees off target
    ssp_common.goto_plate_solve(outfile, 3, 2, True, ra_h, ra_m, ra_s, dec_d, dec_m, dec_s)

    # Platesolve and correct position twice
    ssp_common.goto_plate_solve(outfile, 0, 2, True, ra_h, ra_m, ra_s, dec_d, dec_m, dec_s)
    ssp_common.goto_plate_solve(outfile, 0, 2, True, ra_h, ra_m, ra_s, dec_d, dec_m, dec_s)

    # Autofocus
    frame_subtraction = 0
    if rough_focus != -1:
        frame_subtraction = ssp_common.run_autofocus(outfile, rough_focus, exposure_time)

    # Set RED filter
    ssp_common.set_filter(outfile, Filters.RED.value)

    # Set guiding
    ssp_common.start_guiding(outfile)

    # Set cooler temperature
    ssp_common.cool_camera(outfile, Cool, temperature)

    # Set exposure
    ssp_common.set_exposure(outfile, exposure_time)

    # Calculate frames
    frame_qty = ssp_common.frame_calc(outfile, timediv, frame_subtraction, 3)

    # Capture RED
    ssp_common.write_light_capture(outfile, frame_qty, dither)

    # Capture GREEN
    ssp_common.write_target_name(outfile, target_name, "g")
    ssp_common.set_filter(outfile, Filters.GREEN.value)
    ssp_common.write_light_capture(outfile, frame_qty, dither)

    # Capture BLUE
    ssp_common.write_target_name(outfile, target_name, "b")
    ssp_common.set_filter(outfile, Filters.BLUE.value)
    ssp_common.write_light_capture(outfile, frame_qty, dither)

    # Finish target
    ssp_common.stop_guiding(outfile)

"""
FUNCTION: main
DESCRIPTION: Main function that contols the sequence generation and logical flow.
INPUTS: None
OUTPUTS: None
"""
def main() -> None:
    global rgb_flag
    global outfile
    global temperature
    global exposure_time
    global plate_exposure_time
    global timediv
    global dither
    
    # CMD line arguments
    if len(sys.argv) != 1:
        print('Formatting error!')
        print('Example: ssp_towa.py')
        quit()

    #Prompt for filename and create file
    filename = ""
    filename = input("Set filename\n")
    filename += ".scs"
    fileout = open(filename, "w+")

    # Initialize session data
    init_session(fileout, 100, Filters.LUMINANCE, 0, 0, 0, 0, -1)

    # Set sequence start time
    ssp_common.start_time(outfile)
    
    # Set cooler temperature
    temperature = ssp_common.set_temp()
    
    # Set filter type
    set_filter()
    
    # Fetch capture parameters
    exposure_time, plate_exposure_time, timediv, dither = ssp_common.calc_capture_vals(filter_type, Exposure, Plate, Timediv, Dither)
    
    # Unpark mount
    ssp_common.unpark(outfile)

    # Create normal target or RGB target
    if (rgb_flag == True):
        create_rgb_target()
    else:
        create_target()

    #Insert additional targets or RGB targets
    while input("Enter additional target? (y/n)") == 'y':
        set_filter()
        exposure_time, plate_exposure_time, timediv, dither = ssp_common.calc_capture_vals(filter_type, Exposure, Plate, Timediv, Dither)
        if (rgb_flag == True):
            create_rgb_target()
        else:
            create_target()

    # Park mount and end sequence
    ssp_common.shutdown(outfile, True, temperature)

    print("Sequence file generated!\n")

if __name__ == "__main__":
    main()