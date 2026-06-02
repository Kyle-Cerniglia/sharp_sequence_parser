# Parser for the sharpcap sequencer
# Designed for an Minicam8M mounted to a Carbonstar 150

import sys
import math
from enum import Enum
from enum import auto
import csv
from pathlib import Path
from typing import Optional

class Telescope(Enum):
    CARBON = 2
    
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

# Exposure time
EXPOSURE_CARBON = {
    Filters.LUMINANCE: 30,
    Filters.RED: 30,
    Filters.GREEN: 30,
    Filters.BLUE: 30,
    Filters.SII: 180,
    Filters.HA: 180,
    Filters.OIII: 180,
    Filters.NONE: 2,
    Filters.RGB: 30
}
EXPOSURE = {
    Telescope.CARBON: EXPOSURE_CARBON
}

# Platesolving exposure time
PLATE_EXPOSURE_CARBON = {
    Filters.LUMINANCE: 2,
    Filters.RED: 2,
    Filters.GREEN: 2,
    Filters.BLUE: 2,
    Filters.SII: 2,
    Filters.HA: 2,
    Filters.OIII: 2,
    Filters.NONE: 2,
    Filters.RGB: 2
}
PLATE_EXPOSURE = {
    Telescope.CARBON: PLATE_EXPOSURE_CARBON
}

# Time divider for frame calculation
TIMEDIV_CARBON = {
    Filters.LUMINANCE: 33.44,
    Filters.RED: 33.44,
    Filters.GREEN: 33.44,
    Filters.BLUE: 33.44,
    Filters.SII: 195.26,
    Filters.HA: 195.26,
    Filters.OIII: 195.26,
    Filters.NONE: 33.44,
    Filters.RGB: 33.44
}
TIMEDIV = {
    Telescope.CARBON: TIMEDIV_CARBON
}

# Frames per dither
DITHER_CARBON = {
    Filters.LUMINANCE: 20,
    Filters.RED: 20,
    Filters.GREEN: 20,
    Filters.BLUE: 20,
    Filters.SII: 3,
    Filters.HA: 3,
    Filters.OIII: 3,
    Filters.NONE: 20,
    Filters.RGB: 20
}
DITHER = {
    Telescope.CARBON: DITHER_CARBON
}

rgb_flag = False
ra_h = ""
ra_m = ""
ra_s = ""
dec_d = ""
dec_m = ""
dec_s = ""
master_catalog = Path("catalogs") / "master.csv"
list_catalog = Path("catalogs") / "available_catalogs.txt"
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
rough_focus = None
rgb_flag = False

def coords_direct() -> None:
    global ra_h
    global ra_m
    global ra_s
    global dec_d
    global dec_m
    global dec_s
    global catalog_used
    
    ra_h = input("Enter J2000 coordinates (RA h)\n")
    ra_m = input("Enter J2000 coordinates (RA m)\n")
    ra_s = input("Enter J2000 coordinates (RA s)\n")
    dec_d = input("Enter J2000 coordinates (DEC d)\n")
    dec_m = input("Enter J2000 coordinates (DEC m)\n")
    dec_s = input("Enter J2000 coordinates (DEC s)\n")
    catalog_used = False
    
def coords_catalog() -> None:
    global ra_h
    global ra_m
    global ra_s
    global dec_d
    global dec_m
    global dec_s
    global catalog_search
    global catalog_used
    
    #Show users the available catalogs
    print("Available catalogs:\n")
    with list_catalog.open("r", encoding="utf-8") as f:
        contents = f.read()
    print(contents)
    catalog_search = input("\nEnter catalog name (Ex. m101):\n")
    
    try:
        with master_catalog.open(mode="r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)

            for row in reader:
                # Skip empty or short rows
                if len(row) < 7:
                    continue

                if row[0] == catalog_search:
                    ra_h = row[1]
                    ra_m = row[2]
                    ra_s = row[3]
                    dec_d = row[4]
                    dec_m = row[5]
                    dec_s = row[6]
                    catalog_used = True
                    return
            #If you got here, then the item wasn't found
            print("Catalog object not found, please enter in coordinates manually\n")
            coords_direct()

    except FileNotFoundError:
        print("Catalog file not found, please enter in coordinates manually\n")
        coords_direct()

def init_session(
    out_file,
    temp=None,
    filter_val=None,
    telescope_val=None,
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
    global telescope_type
    global exposure_time
    global timediv
    global dither
    global plate_exposure_time
    global rough_focus

    outfile = out_file
    temperature = temp
    filter_type = filter_val
    telescope_type = telescope_val
    exposure_time = exposure_val
    timediv = timediv_val
    dither = dither_val
    plate_exposure_time = plate_exposure_val
    rough_focus = rough_focus_val

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

    telescope_type = Telescope(2)

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

def start_guiding() -> None:
    global outfile

    outfile.write("    GUIDING CONNECT ABORT False\n")
    outfile.write("    GUIDING STOP\n")
    outfile.write("    DELAY 5\n")
    outfile.write("    GUIDING START\n")
    outfile.write("    DELAY 10\n")

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
        coords_catalog()
    else:
        coords_direct()

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
    start_guiding()

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
        coords_catalog()
    else:
        coords_direct()

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
    start_guiding()

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
    if len(sys.argv) != 1:
        print('Formatting error!')
        print('Example: ssp_towa.py')
        quit()

    #Prompt for filename and create file
    filename = ""
    filename = input("Set filename\n")
    filename += ".scs"
    fileout = open(filename, "w+")

    init_session(fileout, 100, Filters.LUMINANCE, Telescope.CARBON, 0, 0, 0, 0, -1)

    start_time()
    
    set_temp()
    
    set_telescope()
    
    set_filter()
    
    calc_capture_vals()
    
    unpark()

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