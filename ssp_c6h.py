# Parser for the sharpcap sequencer
# Designed for an ASI533MC Pro mounted to a C6 with a Hyperstar

import sys
import math
from enum import Enum
from enum import auto
from typing import Optional
import ssp_common
    
class Filters(Enum):
    UVIR = 1
    LENHANCE = 2
    LPRO = 3
    D1 = 4
    D2 = 5

class Presets(Enum):
    C6H_OSC = "C6H OSC"
    C6H_NB = "C6H NB"

class Exposure(Enum):
    UVIR = 15
    LPRO = 30
    LENHANCE = 120
    D1 = 240
    D2 = 240

class Plate(Enum):
    UVIR = 1
    LPRO = 1
    LENHANCE = 2
    D1 = 8
    D2 = 8

class Timediv(Enum):
    UVIR = 18.62
    LPRO = 35.08
    LENHANCE = 133
    D1 = 247
    D2 = 247

class Dither(Enum):
    UVIR = 24
    LPRO = 12
    LENHANCE = 8
    D1 = 3
    D2 = 3

# Local function variables
outfile = None
temperature = None
filter_type = None
exposure_time = None
timediv = None
dither = None
plate_exposure_time = None
ra_h = ""
ra_m = ""
ra_s = ""
dec_d = ""
dec_m = ""
dec_s = ""
catalog_search = ""
catalog_used = False

def init_session(
    out_file,
    temp=None,
    filter_val=None,
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
    global exposure_time
    global timediv
    global dither
    global plate_exposure_time

    outfile = out_file
    temperature = temp
    filter_type = filter_val
    exposure_time = exposure_val
    timediv = timediv_val
    dither = dither_val
    plate_exposure_time = plate_exposure_val

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

def preset() -> None:
    global outfile

    if filter_type in [Filters.UVIR, Filters.LENHANCE, Filters.LPRO]:
        preset_val = Presets.C6H_OSC
    else:
        preset_val = Presets.C6H_NB
    outfile.write(f"    LOAD PROFILE \"{preset_val.value}\"\n")

def write_target_name(target_name: str) -> None:
    global outfile

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

def create_target() -> None:
    global outfile
    global ra_h
    global ra_m
    global ra_s
    global dec_d
    global dec_m
    global dec_s
    global catalog_used
    global catalog_search

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
        ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used, catalog_search = ssp_common.coords_catalog()
    else:
        ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used = ssp_common.coords_direct()

    # Set target name
    if catalog_used:
        target_name = catalog_search
    else:
        target_name = input("Enter target name\n")

    write_target_name(target_name)

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
    global outfile
    global temperature
    global exposure_time
    global plate_exposure_time
    global timediv
    global dither
    
    if len(sys.argv) != 1:
        print('Formatting error!')
        print('Example: sharp_sequence_parser.py')
        quit()

    #Prompt for filename and create file
    filename = ""
    filename = input("Set filename\n")
    filename += ".scs"
    fileout = open(filename, "w+")

    init_session(fileout, 100, Filters.UVIR, 0, 0, 0, 0)

    ssp_common.start_time(outfile)
    
    temperature = ssp_common.set_temp(temperature)
    
    set_filter()
    
    exposure_time, plate_exposure_time, timediv, dither = ssp_common.calc_capture_vals(filter_type, Exposure, Plate, Timediv, Dither)
    
    ssp_common.unpark(outfile)

    create_target()

    #Insert additional targets
    while input("Enter additional target? (y/n)") == 'y':
        create_target()

    shutdown()

    print("Sequence file generated!\n")

if __name__ == "__main__":
    main()