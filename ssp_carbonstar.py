# Parser for the sharpcap sequencer
# Designed for a Minicam8M mounted to a Carbonstar 150

import sys
import math
from enum import Enum
from enum import auto
from typing import Optional
import ssp_common
    
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

class Presets(Enum):
    CARBON_LRGB = "MC8_LRGB"
    CARBON_NB = "MC8_NB"
    
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

def preset() -> None:
    global outfile

    if filter_type in [Filters.LUMINANCE, Filters.RED, Filters.GREEN, Filters.BLUE]:
        preset_val = Presets.CARBON_LRGB
    else:
        preset_val = Presets.CARBON_NB
    outfile.write(f"    LOAD PROFILE {preset_val.value}\n")

def autofocus() -> None:
    global rough_focus

    rough_focus = int(
        input("Set autofocuser rough focal point (Set to -1 to disable):\n")
    )

def write_target_name(target_name: str) -> None:
    global outfile

    if filter_type == Filters.LUMINANCE:
        outfile.write("    TARGETNAME \"" + target_name + "_l\"\n")
    elif filter_type == Filters.RED:
        outfile.write("    TARGETNAME \"" + target_name + "_r\"\n")
    elif filter_type == Filters.GREEN:
        outfile.write("    TARGETNAME \"" + target_name + "_g\"\n")
    elif filter_type == Filters.BLUE:
        outfile.write("    TARGETNAME \"" + target_name + "_b\"\n")
    elif filter_type == Filters.SII:
        outfile.write("    TARGETNAME \"" + target_name + "_s\"\n")
    elif filter_type == Filters.HA:
        outfile.write("    TARGETNAME \"" + target_name + "_h\"\n")
    elif filter_type == Filters.OIII:
        outfile.write("    TARGETNAME \"" + target_name + "_o\"\n")
    else:
        outfile.write("    TARGETNAME \"" + target_name + "\"\n")

def rough_plate_solve() -> None:
    global outfile

    dec_d_offset = int(dec_d)

    if dec_d_offset > 85:
        dec_d_offset = dec_d_offset - 3
    else:
        dec_d_offset = dec_d_offset + 3

    outfile.write("    WHEEL MOVE TO 1\n")
    outfile.write("    DELAY 10\n")
    outfile.write(
        "    MOUNT GOTO \""
        + ra_h
        + " "
        + ra_m
        + " "
        + ra_s
        + ", "
        + str(dec_d_offset)
        + " "
        + dec_m
        + " "
        + dec_s
        + "\"\n"
    )
    outfile.write("    DELAY 10\n")
    outfile.write("    PRESERVE CAMERA SETTINGS\n")
    outfile.write("        SET EXPOSURE TO 2\n")
    outfile.write("        SET GAIN TO 100\n")
    outfile.write("        MOUNT SOLVEANDSYNC\n")
    outfile.write("    END PRESERVE\n")
    outfile.write("    DELAY 10\n")

def centered_plate_solve() -> None:
    global outfile

    outfile.write("    WHEEL MOVE TO 1\n")
    outfile.write("    DELAY 10\n")
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
    outfile.write("        SET EXPOSURE TO 2\n")
    outfile.write("        SET GAIN TO 100\n")
    outfile.write("        MOUNT SOLVEANDSYNC\n")
    outfile.write("    END PRESERVE\n")
    outfile.write("    DELAY 10\n")

def run_autofocus_if_enabled() -> float:
    global outfile

    frame_subtraction = 0

    if rough_focus != -1:
        outfile.write("    SET EXPOSURE TO 4\n")
        outfile.write(
            "    AUTOFOCUS FROM "
            + str(rough_focus - 100)
            + " TO "
            + str(rough_focus + 100)
            + " STEP COUNT 21\n"
        )

        # Remove 12 minutes from frame time for autofocus
        frame_subtraction = 1440 / exposure_time

    return frame_subtraction

def stop_guiding() -> None:
    global outfile

    outfile.write("    GUIDING STOP\n")
    outfile.write("    GUIDING DISCONNECT\n\n")

def cool_camera() -> None:
    global outfile

    if int(temperature) != 100:
        outfile.write("    COOL DOWN TO " + temperature + " RATE 25 TOLERANCE 1\n")

def write_light_capture(frame_qty: int) -> None:
    global outfile

    outfile.write("    PRESERVE CAMERA SETTINGS\n")
    outfile.write("        FRAMETYPE Light\n")
    outfile.write("        GUIDING DITHER EVERY " + str(dither) + " FRAMES\n")
    outfile.write("        CAPTURE " + str(frame_qty) + " FRAMES REQUIREGUIDING True\n")
    outfile.write("        GUIDING DITHER EVERY STOP\n")
    outfile.write("    END PRESERVE\n")

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
    outfile.write("    SET COLOUR SPACE TO MONO16\n")
    outfile.write("    SET OUTPUT FORMAT TO \"FITS files (*.fits)\"\n")
    preset()
    outfile.write("    MOUNT CONNECT\n")

    # Configure autofocus
    autofocus()

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

    # Slew and plate solve to a position 3 degrees off target
    rough_plate_solve()

    # Platesolve and correct position twice
    centered_plate_solve()
    centered_plate_solve()

    # Autofocus
    frame_subtraction = run_autofocus_if_enabled()

    # Set filter
    outfile.write("    WHEEL MOVE TO " + str(filter_type.value) + "\n")
    outfile.write("    DELAY 10\n")

    # Set guiding
    ssp_common.start_guiding(outfile)

    # Set cooler temperature
    cool_camera()

    # Set exposure
    outfile.write("    SET EXPOSURE TO " + str(exposure_time) + "\n")

    # Set frame capture
    frame_duration = input("Enter number of hours to capture data\n")
    frame_qty = (float(frame_duration) * 3600) / timediv
    frame_qty = frame_qty - frame_subtraction
    frame_qty = math.floor(frame_qty)
    write_light_capture(frame_qty)
    stop_guiding()

def create_rgb_target() -> None:
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
    outfile.write("    SET COLOUR SPACE TO MONO16\n")
    outfile.write("    SET OUTPUT FORMAT TO \"FITS files (*.fits)\"\n")
    preset()
    outfile.write("    MOUNT CONNECT\n")

    # Configure autofocus
    autofocus()

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
    outfile.write("    TARGETNAME \"" + target_name + "_r\"\n")

    # Slew and plate solve to a position 3 degrees off target
    rough_plate_solve()

    # Platesolve and correct position twice
    centered_plate_solve()
    centered_plate_solve()

    # Autofocus
    frame_subtraction = run_autofocus_if_enabled()

    # Set RED filter
    outfile.write("    WHEEL MOVE TO " + str(Filters.RED.value) + "\n")
    outfile.write("    DELAY 10\n")

    # Set guiding
    ssp_common.start_guiding(outfile)

    # Set cooler temperature
    cool_camera()

    # Set exposure
    outfile.write("    SET EXPOSURE TO " + str(exposure_time) + "\n")

    frame_duration = input("Enter number of hours to capture data\n")
    frame_qty = (float(frame_duration) * 3600) / timediv
    frame_qty = frame_qty - frame_subtraction
    frame_qty = frame_qty / 3
    frame_qty = math.floor(frame_qty)

    # Capture RED
    write_light_capture(frame_qty)

    # Capture GREEN
    outfile.write("    TARGETNAME \"" + target_name + "_g\"\n")
    outfile.write("    WHEEL MOVE TO " + str(Filters.GREEN.value) + "\n")
    outfile.write("    DELAY 10\n")
    write_light_capture(frame_qty)

    # Capture BLUE
    outfile.write("    TARGETNAME \"" + target_name + "_b\"\n")
    outfile.write("    WHEEL MOVE TO " + str(Filters.BLUE.value) + "\n")
    outfile.write("    DELAY 10\n")
    write_light_capture(frame_qty)

    # Finish target
    stop_guiding()

def shutdown() -> None:
    global outfile

    outfile.write("    MOUNT PARK\n")
    if int(temperature) != 100:
        outfile.write("    SET COOLER OFF\n")
    outfile.write("    WHEEL MOVE TO 1\n")
    outfile.write("END SEQUENCE\n")
    outfile.close()

def main() -> None:
    global rgb_flag
    global outfile
    global temperature
    global exposure_time
    global plate_exposure_time
    global timediv
    global dither
    
    if len(sys.argv) != 1:
        print('Formatting error!')
        print('Example: ssp_towa.py')
        quit()

    #Prompt for filename and create file
    filename = ""
    filename = input("Set filename\n")
    filename += ".scs"
    fileout = open(filename, "w+")

    init_session(fileout, 100, Filters.LUMINANCE, 0, 0, 0, 0, -1)

    ssp_common.start_time(outfile)
    
    temperature = ssp_common.set_temp(temperature)
    
    set_filter()
    
    exposure_time, plate_exposure_time, timediv, dither = ssp_common.calc_capture_vals(filter_type, Exposure, Plate, Timediv, Dither)
    
    ssp_common.unpark(outfile)

    if (rgb_flag == True):
        create_rgb_target()
    else:
        create_target()

    #Insert additional targets
    while input("Enter additional target? (y/n)") == 'y':
        set_filter()
        calc_capture_vals()
        if (rgb_flag == True):
            create_rgb_target()
        else:
            create_target()

    shutdown()

    print("Sequence file generated!\n")

if __name__ == "__main__":
    main()