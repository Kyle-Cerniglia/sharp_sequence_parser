# Parser for the sharpcap sequencer
# Designed for an ASI533MC Pro mounted to a C6 with a Hyperstar

import sys
import math
from enum import Enum
from enum import auto
import csv
from typing import Optional
from ssp_common import coords_direct, coords_catalog

class Telescope(Enum):
    C6_HYPER = 3
    
class Filters(Enum):
    UVIR = 1
    LENHANCE = 2
    LPRO = 3
    D1 = 4
    D2 = 5

class Presets(Enum):
    C6H_OSC = "C6H OSC"
    C6H_NB = "C6H NB"

# Exposure time
EXPOSURE_C6_HYPER = {
    Filters.UVIR: 15,
    Filters.LPRO: 30,
    Filters.LENHANCE: 120,
    Filters.D1: 240,
    Filters.D2: 240
}
EXPOSURE = {
    Telescope.C6_HYPER: EXPOSURE_C6_HYPER
}

# Platesolving exposure time
PLATE_EXPOSURE_C6_HYPER = {
    Filters.UVIR: 1,
    Filters.LPRO: 1,
    Filters.LENHANCE: 2,
    Filters.D1: 8,
    Filters.D2: 8
}
PLATE_EXPOSURE = {
    Telescope.C6_HYPER: PLATE_EXPOSURE_C6_HYPER
}

# Time divider for frame calculation
TIMEDIV_C6_HYPER = {
    Filters.UVIR: 18.62,
    Filters.LPRO: 35.08,
    Filters.LENHANCE: 133,
    Filters.D1: 247,
    Filters.D2: 247
}
TIMEDIV = {
    Telescope.C6_HYPER: TIMEDIV_C6_HYPER
}

# Frames per dither
DITHER_C6_HYPER = {
    Filters.UVIR: 24,
    Filters.LPRO: 12,
    Filters.LENHANCE: 8,
    Filters.D1: 3,
    Filters.D2: 3
}
DITHER = {
    Telescope.C6_HYPER: DITHER_C6_HYPER
}

ra_h = ""
ra_m = ""
ra_s = ""
dec_d = ""
dec_m = ""
dec_s = ""
catalog_search = ""
catalog_used = False

# Local function variables
outfile = None
temperature = None
filter_type = None
telescope_type = None
exposure_time = None
timediv = None
dither = None
plate_exposure_time = None

def init_session(
    out_file,
    temp=None,
    filter_val=None,
    telescope_val=None,
    exposure_val=None,
    timediv_val=None,
    dither_val=None,
    plate_exposure_val=None,
) -> None:
    """
    Replaces Session.__init__().
    Stores the session data in globals instead of self fields.
    """

    global outfile
    global temperature
    global filter_type
    global telescope_type
    global exposure_time
    global timediv
    global dither
    global plate_exposure_time

    outfile = out_file
    temperature = temp
    filter_type = filter_val
    telescope_type = telescope_val
    exposure_time = exposure_val
    timediv = timediv_val
    dither = dither_val
    plate_exposure_time = plate_exposure_val

def start_time() -> None:
    global outfile

    outfile.write("SEQUENCE\n")
    if input("Set a start time? (y/n)\n") == "y":
        hour = input("Enter hour start (24h)\n")
        minute = input("Enter minute start\n")
        if int(minute) < 10:
            minute = "0" + minute

        if int(hour) < 12:
            outfile.write(
                "    WAIT UNTIL LOCALTIME \"" + hour + ":" + minute + " AM\"\n"
            )
        else:
            hour = str(int(hour) - 12)
            outfile.write(
                "    WAIT UNTIL LOCALTIME \"" + hour + ":" + minute + " PM\"\n"
            )

def unpark() -> None:
    global outfile

    outfile.write("    DELAY 1\n")
    outfile.write("    MOUNT UNPARK\n")
    outfile.write("    MOUNT UNPARK\n")

def set_temp() -> None:
    global temperature

    temperature = input("Set cooler temp C (100 to disable)\n")

def set_telescope() -> None:
    global telescope_type

    telescope_type = Telescope(3)

def set_filter() -> None:
    global filter_type

    filter_in = input(
        "Select your filter::\n"
        "[1] = UV/IR\n"
        "[2] = L-Enhance\n"
        "[3] = L-Pro\n"
        "[4] = D1\n"
        "[5] = D2\n"
    )
    filter_type = Filters(int(filter_in))

def calc_capture_vals() -> None:
    global exposure_time
    global plate_exposure_time
    global timediv
    global dither

    exposure_time = EXPOSURE[telescope_type][filter_type]
    plate_exposure_time = PLATE_EXPOSURE[telescope_type][filter_type]
    timediv = TIMEDIV[telescope_type][filter_type]
    dither = DITHER[telescope_type][filter_type]

def preset() -> None:
    global outfile

    if filter_type in [Filters.UVIR, Filters.LENHANCE, Filters.LPRO]:
        preset_val = Presets.C6H_OSC
    else:
        preset_val = Presets.C6H_NB
    outfile.write(f"    LOAD PROFILE \"{preset_val.value}\"\n")

def create_target() -> None:
    global outfile

    # Setup
    outfile.write("    DELAY 1\n")
    outfile.write("    STILL MODE\n")

    # Configure image formatting
    outfile.write("    SET COLOUR SPACE TO RAW16\n")
    outfile.write("    SET OUTPUT FORMAT TO \"FITS files (*.fits)\"\n")
    preset()
    outfile.write("    MOUNT CONNECT\n")

    # Configure target
    if input("Lookup catalog target? (y/n)\n") == "y":
        ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used = coords_catalog()
    else:
        ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used = coords_direct()

    # Set target name
    if catalog_used:
        target_name = catalog_search
    else:
        target_name = input("Enter target name\n")

    if filter_type == Filters.UVIR:
        outfile.write("    TARGETNAME \"" + target_name + "_uvir\"\n")
    elif filter_type == Filters.LPRO:
        outfile.write("    TARGETNAME \"" + target_name + "_lpro\"\n")
    elif filter_type == Filters.LENHANCE:
        outfile.write("    TARGETNAME \"" + target_name + "_lenh\"\n")
    elif filter_type == Filters.D1:
        outfile.write("    TARGETNAME \"" + target_name + "_d1\"\n")
    elif filter_type == Filters.D2:
        outfile.write("    TARGETNAME \"" + target_name + "_d2\"\n")
    else:
        outfile.write("    TARGETNAME \"" + target_name + "\"\n")

    # Platesolve and correct position
    outfile.write(
        "    MOUNT GOTO \""
        + ra_h
        + " "
        + ra_m
        + " "
        + ra_s
        + ", "
        + dec_d
        + " "
        + dec_m
        + " "
        + dec_s
        + "\"\n"
    )

    outfile.write("    DELAY 10\n")
    outfile.write("    PRESERVE CAMERA SETTINGS\n")
    outfile.write("        SET EXPOSURE TO " + str(plate_exposure_time) + "\n")
    outfile.write("        SET GAIN TO 100\n")
    outfile.write("        MOUNT SOLVEANDSYNC\n")
    outfile.write("    END PRESERVE\n")
    outfile.write("    DELAY 10\n")

    # Set guiding
    outfile.write("    GUIDING CONNECT ABORT False\n")
    outfile.write("    GUIDING STOP\n")
    outfile.write("    DELAY 5\n")
    outfile.write("    GUIDING START\n")
    outfile.write("    DELAY 10\n")

    # Set cooler temperature
    if int(temperature) != 100:
        outfile.write("    COOL DOWN TO " + temperature + " RATE 8 TOLERANCE 1\n")

    # Set exposure
    outfile.write("    SET EXPOSURE TO " + str(exposure_time) + "\n")

    # Set frame capture
    outfile.write("    PRESERVE CAMERA SETTINGS\n")
    outfile.write("        FRAMETYPE Light\n")
    outfile.write("        GUIDING DITHER EVERY " + str(dither) + " FRAMES\n")
    frame_duration = input("Enter number of hours to capture data\n")
    frame_qty = (float(frame_duration) * 3600) / timediv
    frame_qty = math.floor(frame_qty)
    outfile.write("        CAPTURE " + str(frame_qty) + " FRAMES REQUIREGUIDING True\n")
    outfile.write("        GUIDING DITHER EVERY STOP\n")
    outfile.write("    END PRESERVE\n")
    outfile.write("    GUIDING STOP\n")
    outfile.write("    GUIDING DISCONNECT\n\n")

def shutdown() -> None:
    global outfile
    
    outfile.write("    MOUNT PARK\n")
    if int(temperature) != 100:
        outfile.write("    SET COOLER OFF\n")
    outfile.write("END SEQUENCE\n")
    outfile.close()

def main() -> None:
    if len(sys.argv) != 1:
        print('Formatting error!')
        print('Example: sharp_sequence_parser.py')
        quit()

    #Prompt for filename and create file
    filename = ""
    filename = input("Set filename\n")
    filename += ".scs"
    fileout = open(filename, "w+")

    init_session(fileout, 100, Filters.UVIR, Telescope.C6_HYPER, 0, 0, 0, 0)

    start_time()
    
    set_temp()
    
    set_telescope()
    
    set_filter()
    
    calc_capture_vals()
    
    unpark()

    create_target()

    #Insert additional targets
    while input("Enter additional target? (y/n)") == 'y':
        create_target()

    shutdown()

    print("Sequence file generated!\n")

if __name__ == "__main__":
    main()