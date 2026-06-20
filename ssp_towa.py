# Parser for the sharpcap sequencer
# Designed for a Minicam8M mounted to a Towa 339

import sys
import math
from enum import Enum
from enum import auto
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

def preset() -> None:
    global outfile

    if filter_type in [Filters.RED, Filters.GREEN, Filters.BLUE]:
        preset_val = Presets.TOWA_RGB
    else:
        preset_val = Presets.TOWA_NB
    outfile.write(f"    LOAD PROFILE {preset_val.value}\n")

def identify_target_name(target_name: str) -> None:
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

def create_target() -> None:
    global outfile
    global dither
    global temperature

    # Configure image formatting
    ssp_common.set_format(outfile, True)
    
    # Configure sharpcap preset
    preset()
    
    # Connect to mount
    ssp_common.connect_mount(outfile)

    # Configure target coordinates
    ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used = ssp_common.coords_direct()

    # Set target name
    target_name = input("Enter target name\n")
    
    identify_target_name(target_name)

    # Slew and plate solve to a position 3 degrees off target
    ssp_common.goto_plate_solve(outfile, 3, 2, True, ra_h, ra_m, ra_s, dec_d, dec_m, dec_s)

    # Platesolve and correct position twice
    ssp_common.goto_plate_solve(outfile, 0, 2, True, ra_h, ra_m, ra_s, dec_d, dec_m, dec_s)
    ssp_common.goto_plate_solve(outfile, 0, 2, True, ra_h, ra_m, ra_s, dec_d, dec_m, dec_s)

    # Set filter
    ssp_common.set_filter(outfile, filter_type.value)

    # Set guiding
    ssp_common.start_guiding(outfile)

    # Set cooler temperature
    ssp_common.cool_camera(outfile, Cool, temperature)

    # Set exposure
    ssp_common.set_exposure(outfile, exposure_time)

    # Set frame capture
    frame_duration = input("Enter number of hours to capture data\n")
    frame_qty = (float(frame_duration) * 3600) / timediv
    frame_qty = math.floor(frame_qty)
    ssp_common.write_light_capture(outfile, frame_qty, dither)
    
    # Finish target
    ssp_common.stop_guiding(outfile)

def main() -> None:
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

    init_session(fileout, 100, Filters.LUMINANCE, 0, 0, 0, 0)

    ssp_common.start_time(outfile)
    
    temperature = ssp_common.set_temp(temperature)
    
    set_filter()
    
    exposure_time, plate_exposure_time, timediv, dither = ssp_common.calc_capture_vals(filter_type, Exposure, Plate, Timediv, Dither)
    
    ssp_common.unpark(outfile)

    create_target()

    #Insert additional targets
    while input("Enter additional target? (y/n)") == 'y':
        set_filter()
        exposure_time, plate_exposure_time, timediv, dither = ssp_common.calc_capture_vals(filter_type, Exposure, Plate, Timediv, Dither)
        create_target()

    ssp_common.shutdown(outfile, True, temperature)

    print("Sequence file generated!\n")

if __name__ == "__main__":
    main()