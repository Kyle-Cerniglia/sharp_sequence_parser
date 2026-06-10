# Parser for the sharpcap sequencer
# Designed for a Minicam8M mounted to a Towa 339

import sys
import math
from enum import Enum
from enum import auto
import ssp_common

class Telescope(Enum):
    TOWA = 1
    
class Filters(Enum):
    LUMINANCE = 1
    RED = 2
    GREEN = 3
    BLUE = 4
    SII = 5
    HA = 6
    OIII = 7
    NONE = 8

class Presets(Enum):
    TOWA_RGB = "MC8_RGB"
    TOWA_NB = "MC8_NB"

class Exposure(Enum):
    LUMINANCE = 2
    RED = 60
    GREEN = 60
    BLUE = 60
    SII = 180
    HA = 180
    OIII = 180
    NONE = 2

class Plate(Enum):
    LUMINANCE = 2
    RED = 2
    GREEN = 2
    BLUE = 2
    SII = 2
    HA = 2
    OIII = 2
    NONE = 2

class Timediv(Enum):
    LUMINANCE = 70.16
    RED = 70.16
    GREEN = 70.16
    BLUE = 70.16
    SII = 190.82
    HA = 190.82
    OIII = 190.82
    NONE = 70.16

class Dither(Enum):
    LUMINANCE = 10
    RED = 10
    GREEN = 10
    BLUE = 10
    SII = 3
    HA = 3
    OIII = 3
    NONE = 10

# Local function variables
outfile = None
temperature = None
filter_type = None
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
        "Select your filter:\n"
        "[1] = Luminance\n"
        "[2] = Red\n"
        "[3] = Green\n"
        "[4] = Blue\n"
        "[5] = SII\n"
        "[6] = Ha\n"
        "[7] = OIII\n"
        "[8] = None\n"
    )
    filter_type = Filters(int(filter_in))

def calc_capture_vals() -> None:
    global exposure_time
    global plate_exposure_time
    global timediv
    global dither

    exposure_time = Exposure[filter_type.name].value
    plate_exposure_time = Plate[filter_type.name].value
    timediv = Timediv[filter_type.name].value
    dither = Dither[filter_type.name].value

def preset() -> None:
    global outfile

    if filter_type in [Filters.RED, Filters.GREEN, Filters.BLUE]:
        preset_val = Presets.TOWA_RGB
    else:
        preset_val = Presets.TOWA_NB
    outfile.write(f"    LOAD PROFILE {preset_val.value}\n")

def get_coordinates() -> tuple[str, str, str, str, str, str]:
    ra_h = input("Enter J2000 coordinates (RA h)\n")
    ra_m = input("Enter J2000 coordinates (RA m)\n")
    ra_s = input("Enter J2000 coordinates (RA s)\n")
    dec_d = input("Enter J2000 coordinates (DEC d)\n")
    dec_m = input("Enter J2000 coordinates (DEC m)\n")
    dec_s = input("Enter J2000 coordinates (DEC s)\n")
    return ra_h, ra_m, ra_s, dec_d, dec_m, dec_s

def write_mount_goto(
    ra_h: str,
    ra_m: str,
    ra_s: str,
    dec_d: str,
    dec_m: str,
    dec_s: str,
) -> None:
    global outfile

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

def plate_solve() -> None:
    global outfile

    outfile.write("    PRESERVE CAMERA SETTINGS\n")
    outfile.write("        SET EXPOSURE TO 2\n")
    outfile.write("        SET GAIN TO 100\n")
    outfile.write("        MOUNT SOLVEANDSYNC\n")
    outfile.write("    END PRESERVE\n")
    outfile.write("    DELAY 10\n")

def start_guiding() -> None:
    global outfile

    outfile.write("    GUIDING CONNECT ABORT False\n")
    outfile.write("    GUIDING STOP\n")
    outfile.write("    DELAY 5\n")
    outfile.write("    GUIDING START\n")
    outfile.write("    DELAY 20\n")

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

    # Configure target coordinates
    ra_h, ra_m, ra_s, dec_d, dec_m, dec_s = get_coordinates()

    write_mount_goto(ra_h, ra_m, ra_s, dec_d, dec_m, dec_s)
    outfile.write("    DELAY 20\n")

    # Set target name
    target_name = input("Enter target name\n")
    outfile.write("    TARGETNAME \"" + target_name + "\"\n")

    # Platesolve and correct position twice
    outfile.write("    WHEEL MOVE TO 1\n")
    outfile.write("    DELAY 20\n")
    plate_solve()
    write_mount_goto(ra_h, ra_m, ra_s, dec_d, dec_m, dec_s)
    outfile.write("    DELAY 20\n")
    plate_solve()

    # Set filter
    outfile.write("    WHEEL MOVE TO " + str(filter_type.value) + "\n")
    outfile.write("    DELAY 20\n")

    # Set guiding
    start_guiding()

    # Set cooler temperature
    cool_camera()

    # Set exposure
    outfile.write("    SET EXPOSURE TO " + str(exposure_time) + "\n")

    # Set frame capture
    frame_duration = input("Enter number of hours to capture data\n")
    frame_qty = (float(frame_duration) * 3600) / timediv
    frame_qty = math.floor(frame_qty)
    write_light_capture(frame_qty)
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
    global outfile
    global temperature
    
    if len(sys.argv) != 1:
        print('Formatting error!')
        print('Example: ssp_towa.py')
        quit()

    #Prompt for filename and create file
    filename = ""
    filename = input("Set filename\n")
    filename += ".scs"
    fileout = open(filename, "w+")

    init_session(fileout, 100, Filters.LUMINANCE, Telescope.TOWA, 0, 0, 0, 0)

    ssp_common.start_time(outfile)
    
    temperature = ssp_common.set_temp(temperature)
    
    set_filter()
    
    calc_capture_vals()
    
    ssp_common.unpark(outfile)

    create_target()

    #Insert additional targets
    while input("Enter additional target? (y/n)") == 'y':
        set_filter()
        calc_capture_vals()
        create_target()

    shutdown()

    print("Sequence file generated!\n")

if __name__ == "__main__":
    main()