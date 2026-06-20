"""
FILE: ssp_common.py
DESCRIPTION: This file hosts common functions used by the main functions of the sharp sequence parser.
"""

from pathlib import Path
import csv
import math

# Catalog paths
master_catalog = Path("catalogs") / "master.csv"
list_catalog = Path("catalogs") / "available_catalogs.txt"

"""
FUNCTION: coords_direct
DESCRIPTION: Allows user to manually enter in target coordinates.
INPUTS: None
OUTPUTS:
ra_h: RA (Hours)
ra_m: RA (Minutes)
ra_s: RA (Seconds)
dec_d: DEC (Degrees)
dec_m: DEC (Minutes)
dec_s: DEC (Seconds)
catalog_used: False (Catalog not used)
"""
def coords_direct():    
    ra_h = input("Enter J2000 coordinates (RA h)\n")
    ra_m = input("Enter J2000 coordinates (RA m)\n")
    ra_s = input("Enter J2000 coordinates (RA s)\n")
    dec_d = input("Enter J2000 coordinates (DEC d)\n")
    dec_m = input("Enter J2000 coordinates (DEC m)\n")
    dec_s = input("Enter J2000 coordinates (DEC s)\n")
    catalog_used = False
    return ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used

"""
FUNCTION: coords_catalog
DESCRIPTION: Allows user to search for object coordinates in the csv catalogs.
INPUTS: None
OUTPUTS:
ra_h: RA (Hours)
ra_m: RA (Minutes)
ra_s: RA (Seconds)
dec_d: DEC (Degrees)
dec_m: DEC (Minutes)
dec_s: DEC (Seconds)
catalog_used: True/False (Catalog used/not used)
catalog_search: Target name used for catalog search
"""
def coords_catalog():    
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
                # Skip invalid catalog entry (Empty or too short)
                if len(row) < 7:
                    continue
                
                # Target found, return coordinate data
                if row[0] == catalog_search:
                    ra_h = row[1]
                    ra_m = row[2]
                    ra_s = row[3]
                    dec_d = row[4]
                    dec_m = row[5]
                    dec_s = row[6]
                    catalog_used = True
                    return ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used, catalog_search
                    
            # Target not found in catalog, enter target coordinates in manually
            print("Catalog object not found, please enter in coordinates manually\n")
            ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used = coords_direct()
            return ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used, catalog_search

    except FileNotFoundError:
        # Catalog file not found, enter target coordinates in manually
        print("Catalog file not found, please enter in coordinates manually\n")
        ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used = coords_direct()
        return ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used, catalog_search

"""
FUNCTION: start_time
DESCRIPTION: Sets the script start time (Local 24 hour time)
INPUTS:
outfile: Output file
OUTPUTS: None
"""
def start_time(outfile) -> None:
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

"""
FUNCTION: unpark
DESCRIPTION: Unparks the mount (Known to sometimes fail on an EQ6-R, recommend manually unparking telescope during setup!).
INPUTS:
outfile: Output file
OUTPUTS: None
"""
def unpark(outfile) -> None:
    outfile.write("    DELAY 1\n")
    outfile.write("    MOUNT UNPARK\n")
    outfile.write("    MOUNT UNPARK\n")

"""
FUNCTION: set_temp
DESCRIPTION: Sets the cooler temperature (Set to 100 to disable cooler).
INPUTS: None
OUTPUTS:
temperature: Temperature setpoint (C)
"""
def set_temp() -> None:
    temperature = input("Set cooler temp C (100 to disable)\n")
    return temperature

"""
FUNCTION: calc_capture_vals
DESCRIPTION: Copies a number of parameters for image capture from enums to variables.
INPUTS:
filter_type: Filter type (Enum)
exposure_c: Exposure time (Enum)
plate_c: Platesolving exposure time (Enum)
timediv_c: Time divider (Enum)
dither_c: Dither frequency (Enum)
OUTPUTS:
exposure_time: Exposure time (s)
plate_exposure_time: Platesolving exposure time (s)
timediv: Time divider
dither: Dither frequency (Frames per dither)
"""
def calc_capture_vals(filter_type, exposure_c, plate_c, timediv_c, dither_c) -> None:
    exposure_time = exposure_c[filter_type.name].value
    plate_exposure_time = plate_c[filter_type.name].value
    timediv = timediv_c[filter_type.name].value
    dither = dither_c[filter_type.name].value
    
    return exposure_time, plate_exposure_time, timediv, dither

"""
FUNCTION: start_guiding
DESCRIPTION: Starts autoguiding.
INPUTS:
outfile: Output file
OUTPUTS: None
"""
def start_guiding(outfile) -> None:
    outfile.write("    GUIDING CONNECT ABORT False\n")
    outfile.write("    GUIDING STOP\n")
    outfile.write("    DELAY 5\n")
    outfile.write("    GUIDING START\n")
    outfile.write("    DELAY 10\n")

"""
FUNCTION: stop_guiding
DESCRIPTION: Stops autoguiding.
INPUTS:
outfile: Output file
OUTPUTS: None
"""
def stop_guiding(outfile) -> None:
    outfile.write("    GUIDING STOP\n")
    outfile.write("    GUIDING DISCONNECT\n\n")

"""
FUNCTION: write_light_capture
DESCRIPTION: Starts image capture session.
INPUTS:
outfile: Output file
frame_qty: Frame quantity
dither: Dither frequency (Frames per dither)
OUTPUTS: None
"""
def write_light_capture(outfile, frame_qty: int, dither: int) -> None:
    outfile.write("    PRESERVE CAMERA SETTINGS\n")
    outfile.write("        FRAMETYPE Light\n")
    outfile.write("        GUIDING DITHER EVERY " + str(dither) + " FRAMES\n")
    outfile.write("        CAPTURE " + str(frame_qty) + " FRAMES REQUIREGUIDING True\n")
    outfile.write("        GUIDING DITHER EVERY STOP\n")
    outfile.write("    END PRESERVE\n")

"""
FUNCTION: cool_camera
DESCRIPTION: Apply temperature setpoint to cooler.
INPUTS:
outfile: Output file
cool_c: Cooler parameters (Enum)
temperature: Temperature (C)
OUTPUTS: None
"""
def cool_camera(outfile, cool_c, temperature) -> None:
    if int(temperature) != 100:
        outfile.write("    COOL DOWN TO " + temperature + " RATE " + str(cool_c["RATE"].value) + " TOLERANCE " + str(cool_c["TOLERANCE"].value) + "\n")

"""
FUNCTION: shutdown
DESCRIPTION: Park mount, turn off cooler, reposition filter wheel, and end the sequence.
INPUTS:
outfile: Output file
wheel: True = Filter wheel enabled
temperature: Temperature (C)
OUTPUTS: None
"""
def shutdown(outfile, wheel, temperature) -> None:
    outfile.write("    MOUNT PARK\n")
    if int(temperature) != 100:
        outfile.write("    SET COOLER OFF\n")
    if wheel == True:
        outfile.write("    WHEEL MOVE TO 1\n")
    outfile.write("END SEQUENCE\n")
    outfile.close()

"""
FUNCTION: set_autofocus
DESCRIPTION: Sets the autofocus start position
INPUTS: None
OUTPUTS:
rough_focus: Rough focus point
"""
def set_autofocus() -> None:
    rough_focus = int(input("Set autofocuser rough focal point (Set to -1 to disable):\n"))
    return rough_focus

"""
FUNCTION: run_autofocus
DESCRIPTION: Execute autofocus, centered at the rough_focus point +- 100 split over 21 steps
INPUTS:
outfile: Output file
rough_focus: Rough focus point
exposure_time: Capture exposure time for frame_subtraction calcs
OUTPUTS:
frame_subtraction: Number of frames to remove for autofocus time
"""
def run_autofocus(outfile, rough_focus, exposure_time) -> float:
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

"""
FUNCTION: goto_plate_solve
DESCRIPTION: Goto target and plate solve.
             Can add an offset to the DEC degrees (Some high FL scopes seem to have better pointing if they first slew to
             a point near the target before slewing to the final target. Offset will move away from the equator, unless your target is >85 degrees).
INPUTS:
outfile: Output file
offset: DEC degrees offset (Degrees)
exposure: Exposure duration (s)
wheel: True = Filter wheel enabled
ra_h: RA (Hours)
ra_m: RA (Minutes)
ra_s: RA (Seconds)
dec_d: DEC (Degrees)
dec_m: DEC (Minutes)
dec_s: DEC (Seconds)
OUTPUTS: None
"""
def goto_plate_solve(outfile, offset, exposure, wheel, ra_h, ra_m, ra_s, dec_d, dec_m, dec_s) -> None:
    dec_d_offset = int(dec_d)
    
    # Apply offset (If present)
    if dec_d_offset > 85:
        dec_d_offset = dec_d_offset - offset
    else:
        dec_d_offset = dec_d_offset + offset

    # Generate goto command
    if wheel == True:
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
    
    # Generate platesolve command
    outfile.write("    DELAY 10\n")
    outfile.write("    PRESERVE CAMERA SETTINGS\n")
    outfile.write("        SET EXPOSURE TO " + str(exposure) + "\n")
    outfile.write("        SET GAIN TO 100\n")
    outfile.write("        MOUNT SOLVEANDSYNC\n")
    outfile.write("    END PRESERVE\n")
    outfile.write("    DELAY 10\n")

"""
FUNCTION: set_format
DESCRIPTION: Sets the image format (Image mode, color space, and file format).
INPUTS:
outfile: Output file
mono: True = Mono (16-bit), False = Raw Color (16-bit)
OUTPUTS: None
"""
def set_format(outfile, mono) -> None:
    outfile.write("    DELAY 1\n")
    outfile.write("    STILL MODE\n")
    if mono == True:
        outfile.write("    SET COLOUR SPACE TO MONO16\n")
    else:
        outfile.write("    SET COLOUR SPACE TO RAW16\n")
    outfile.write("    SET OUTPUT FORMAT TO \"FITS files (*.fits)\"\n")

"""
FUNCTION: connect_mount
DESCRIPTION: Connects to the mount.
INPUTS:
outfile: Output file
OUTPUTS: None
"""
def connect_mount(outfile) -> None:
    outfile.write("    MOUNT CONNECT\n")

"""
FUNCTION: set_filter
DESCRIPTION: Sets the filter wheel position
INPUTS:
outfile: Output file
filter_number: Filter position
OUTPUTS: None
"""
def set_filter(outfile, filter_number) -> None:
    outfile.write("    WHEEL MOVE TO " + str(filter_number) + "\n")
    outfile.write("    DELAY 10\n")

"""
FUNCTION: set_exposure
DESCRIPTION: Sets the exposure duration.
INPUTS:
outfile: Output file
exposure: Exposure duration (s)
OUTPUTS: None
"""
def set_exposure(outfile, exposure) -> None:
    outfile.write("    SET EXPOSURE TO " + str(exposure) + "\n")

"""
FUNCTION: write_target_name
DESCRIPTION: Write the target name with the filter suffix.
INPUTS:
outfile: Output file
name: Target name
suffix: Filter suffix
OUTPUTS: None
"""
def write_target_name(outfile, name, suffix) -> None:
    outfile.write("    TARGETNAME \"" + name + "_" + suffix + "\"\n")

"""
FUNCTION: frame_calc
DESCRIPTION: Calculates the number of frames for an exposure.
             Has a divider in case you need to split the exposure times equally (RGB capture).
INPUTS:
outfile: Output file
timediv: Time divider
autofocus: Frames to remove for autofocus time
div: Frame divider
OUTPUTS:
frame_qty: Number of frames for exposure
"""
def frame_calc(outfile, timediv, autofocus, div):
    # Get session duration in hours
    frame_duration = input("Enter number of hours to capture data\n")
    # Convert hours into number of frames (Scaled by timediv to get the real ratio right, factoring in wasted time like cooldown and platesolving)
    frame_qty = (float(frame_duration) * 3600) / timediv
    # Remove frames lost during autofocus time
    frame_qty = frame_qty - autofocus
    # Divide frames if splitting between different filters (RGB mode)
    frame_qty = frame_qty / div
    # Round frames down to an even number
    frame_qty = math.floor(frame_qty)
    return frame_qty