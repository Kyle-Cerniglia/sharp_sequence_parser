# Parser for the sharpcap sequencer (Towa telescope)

import sys
import math

def extra_target():
    # Define globals
    global ra_h
    global ra_m
    global ra_s
    global dec_d
    global dec_m
    global dec_s
    global target_name
    
    #Setup
    fileout.write("    DELAY 1\n")
    fileout.write("    STILL MODE\n")

    #Set cooler temperature
    if int(cooler_temp) != 100:
        fileout.write("    COOL DOWN TO " + cooler_temp + " RATE 8 TOLERANCE 1\n")

    #Configure image formatting
    fileout.write("    SET COLOUR SPACE TO RAW16\n")
    fileout.write("    SET OUTPUT FORMAT TO \"FITS files (*.fits)\"\n")
    if band_type == 'b':
        fileout.write("    LOAD PROFILE \"533 OSC\"\n")
    if band_type == 'n':
        fileout.write("    LOAD PROFILE \"533 HO\"\n")
        
    fileout.write("    MOUNT CONNECT\n")

    #Configure target
    ra_h = input("Enter J2000 coordinates (RA h)\n")
    ra_m = input("Enter J2000 coordinates (RA m)\n")
    ra_s = input("Enter J2000 coordinates (RA s)\n")
    dec_d = input("Enter J2000 coordinates (DEC d)\n")
    dec_m = input("Enter J2000 coordinates (DEC m)\n")
    dec_s = input("Enter J2000 coordinates (DEC s)\n")
    fileout.write("    MOUNT GOTO \"" + ra_h + " " + ra_m + " " + ra_s + ", " + dec_d + " " + dec_m + " " + dec_s + "\"\n")
    fileout.write("    DELAY 20\n")

    #Set target name
    target_name = input("Enter target name\n")
    fileout.write("    TARGETNAME \"" + target_name + "\"\n")
    if band_type == 'b':
        fileout.write("    SET EXPOSURE TO 60\n")
    if band_type == 'n':
        fileout.write("    SET EXPOSURE TO 180\n")

    #Platesolve and correct position
    fileout.write("    PRESERVE CAMERA SETTINGS\n")
    fileout.write("        SET EXPOSURE TO 8\n")
    fileout.write("        SET GAIN TO 100\n")
    fileout.write("        MOUNT SOLVEANDSYNC\n")
    fileout.write("    END PRESERVE\n")
    fileout.write("    DELAY 10\n")

    #Set guiding and frame quantity
    fileout.write("    GUIDING CONNECT ABORT False\n")
    fileout.write("    GUIDING START\n")
    fileout.write("    DELAY 20\n")
    fileout.write("    PRESERVE CAMERA SETTINGS\n")
    fileout.write("        FRAMETYPE Light\n")
    if band_type == 'b':
        fileout.write("        GUIDING DITHER EVERY 10 FRAMES\n")
    else:#Assuming narrowband
        fileout.write("        GUIDING DITHER EVERY 6 FRAMES\n")
    frame_duration = input("Enter number of hours to capture data\n")
    if band_type == 'b':
        frame_qty = (float(frame_duration) * 3600) / 70.16
        frame_qty = math.floor(frame_qty)
    else:#Assuming narrowband
        frame_qty = (float(frame_duration) * 3600) / 181.73
        frame_qty = math.floor(frame_qty)
    # Handle the first 1-hour exposure
    if band_type == 'b':
        if (frame_qty > 120):
            frame_qty_s = str(120)
            fileout.write("        CAPTURE " + frame_qty_s + " FRAMES REQUIREGUIDING True\n")
            fileout.write("        GUIDING DITHER EVERY STOP\n")
            fileout.write("    END PRESERVE\n")
            fileout.write("    GUIDING STOP\n")
            fileout.write("    GUIDING DISCONNECT\n\n")
            frame_qty = frame_qty - 120
        else:
            frame_qty_s = str(frame_qty)
            fileout.write("        CAPTURE " + frame_qty_s + " FRAMES REQUIREGUIDING True\n")
            fileout.write("        GUIDING DITHER EVERY STOP\n")
            fileout.write("    END PRESERVE\n")
            fileout.write("    GUIDING STOP\n")
            fileout.write("    GUIDING DISCONNECT\n\n")
            frame_qty = 0
    else:#Assuming narrowband
        if (frame_qty > 40):
            frame_qty_s = str(40)
            fileout.write("        CAPTURE " + frame_qty_s + " FRAMES REQUIREGUIDING True\n")
            fileout.write("        GUIDING DITHER EVERY STOP\n")
            fileout.write("    END PRESERVE\n")
            fileout.write("    GUIDING STOP\n")
            fileout.write("    GUIDING DISCONNECT\n\n")
            frame_qty = frame_qty - 40
        else:
            frame_qty_s = str(frame_qty)
            fileout.write("        CAPTURE " + frame_qty_s + " FRAMES REQUIREGUIDING True\n")
            fileout.write("        GUIDING DITHER EVERY STOP\n")
            fileout.write("    END PRESERVE\n")
            fileout.write("    GUIDING STOP\n")
            fileout.write("    GUIDING DISCONNECT\n\n")
            frame_qty = 0

    # Split up additional frames into 1 hour chunks to counteract tube flexure
    while (frame_qty > 0):
        if band_type == 'b':
            if (frame_qty > 120):
                repeat_target(120)
                frame_qty = frame_qty - 120
            else:
                repeat_target(frame_qty)
                frame_qty = 0
        else:#Assuming narrowband
            if (frame_qty > 40):
                repeat_target(40)
                frame_qty = frame_qty - 40
            else:
                repeat_target(frame_qty)
                frame_qty = 0

def repeat_target(frames):
    # Define globals
    global frame_qty
    
    # Park to reset position as small corrections don't always work
    fileout.write("    MOUNT PARK\n")
    fileout.write("    DELAY 30\n")
    fileout.write("    MOUNT UNPARK\n")
    fileout.write("    MOUNT UNPARK\n")

    #Setup
    fileout.write("    DELAY 1\n")
    fileout.write("    STILL MODE\n")

    #Set cooler temperature
    if int(cooler_temp) != 100:
        fileout.write("    COOL DOWN TO " + cooler_temp + " RATE 8 TOLERANCE 1\n")

    #Configure image formatting
    fileout.write("    SET COLOUR SPACE TO RAW16\n")
    fileout.write("    SET OUTPUT FORMAT TO \"FITS files (*.fits)\"\n")
    if band_type == 'b':
        fileout.write("    LOAD PROFILE \"533 OSC\"\n")
    if band_type == 'n':
        fileout.write("    LOAD PROFILE \"533 HO\"\n")
        
    fileout.write("    MOUNT CONNECT\n")

    #Configure target
    fileout.write("    MOUNT GOTO \"" + ra_h + " " + ra_m + " " + ra_s + ", " + dec_d + " " + dec_m + " " + dec_s + "\"\n")
    fileout.write("    DELAY 20\n")

    #Set target name
    fileout.write("    TARGETNAME \"" + target_name + "\"\n")
    if band_type == 'b':
        fileout.write("    SET EXPOSURE TO 60\n")
    if band_type == 'n':
        fileout.write("    SET EXPOSURE TO 180\n")

    #Platesolve and correct position
    fileout.write("    PRESERVE CAMERA SETTINGS\n")
    fileout.write("        SET EXPOSURE TO 8\n")
    fileout.write("        SET GAIN TO 100\n")
    fileout.write("        MOUNT SOLVEANDSYNC\n")
    fileout.write("    END PRESERVE\n")
    fileout.write("    DELAY 10\n")

    #Set guiding and frame quantity
    fileout.write("    GUIDING CONNECT ABORT False\n")
    fileout.write("    GUIDING START\n")
    fileout.write("    DELAY 20\n")
    fileout.write("    PRESERVE CAMERA SETTINGS\n")
    fileout.write("        FRAMETYPE Light\n")
    if band_type == 'b':
        fileout.write("        GUIDING DITHER EVERY 10 FRAMES\n")
    else:#Assuming narrowband
        fileout.write("        GUIDING DITHER EVERY 6 FRAMES\n")
    frame_qty_s = str(frames)
    fileout.write("        CAPTURE " + frame_qty_s + " FRAMES REQUIREGUIDING True\n")
    fileout.write("        GUIDING DITHER EVERY STOP\n")
    fileout.write("    END PRESERVE\n")
    fileout.write("    GUIDING STOP\n")
    fileout.write("    GUIDING DISCONNECT\n\n")

if len(sys.argv) != 1:
    print('Formatting error!')
    print('Example: sharp_sequence_parser.py')
    quit()
    
filename = "sequence.scs"

#Prompt for filename and create file
filename = input("Set filename\n")
fileout = open(filename, "w+")

fileout.write("SEQUENCE\n")

#Set start time
if input("Set a start time? (y/n)\n") == 'y':
    hour = input("Enter hour start (24h)\n")
    minute = input("Enter minute start\n")
    if int(minute) < 10:
        minute = "0" + minute
    if int(hour) < 12:
        fileout.write("    WAIT UNTIL LOCALTIME \"" + hour + ":" + minute + " AM\"\n")
    else:
        hour = str(int(hour) - 12);
        fileout.write("    WAIT UNTIL LOCALTIME \"" + hour + ":" + minute + " PM\"\n")

#Setup
fileout.write("    DELAY 1\n")
fileout.write("    MOUNT UNPARK\n")
fileout.write("    MOUNT UNPARK\n")
fileout.write("    DELAY 1\n")
fileout.write("    STILL MODE\n")

#Set cooler temperature
cooler_temp = input("Set cooler temp C (100 to disable)\n")
if int(cooler_temp) != 100:
    fileout.write("    COOL DOWN TO " + cooler_temp + " RATE 8 TOLERANCE 1\n")

#Configure image formatting
fileout.write("    SET COLOUR SPACE TO RAW16\n")
fileout.write("    SET OUTPUT FORMAT TO \"FITS files (*.fits)\"\n")
band_type = input("Is the filter (b)roadband (UV/IR Cut) or (n)arrowband? (L-Pro)\n")
if band_type == 'b':
    fileout.write("    LOAD PROFILE \"533 OSC\"\n")
if band_type == 'n':
    fileout.write("    LOAD PROFILE \"533 HO\"\n")
    
fileout.write("    MOUNT CONNECT\n")

#Configure target
ra_h = input("Enter J2000 coordinates (RA h)\n")
ra_m = input("Enter J2000 coordinates (RA m)\n")
ra_s = input("Enter J2000 coordinates (RA s)\n")
dec_d = input("Enter J2000 coordinates (DEC d)\n")
dec_m = input("Enter J2000 coordinates (DEC m)\n")
dec_s = input("Enter J2000 coordinates (DEC s)\n")
fileout.write("    MOUNT GOTO \"" + ra_h + " " + ra_m + " " + ra_s + ", " + dec_d + " " + dec_m + " " + dec_s + "\"\n")
fileout.write("    DELAY 20\n")

#Set target name
target_name = input("Enter target name\n")
fileout.write("    TARGETNAME \"" + target_name + "\"\n")
if band_type == 'b':
    fileout.write("    SET EXPOSURE TO 60\n")
if band_type == 'n':
    fileout.write("    SET EXPOSURE TO 180\n")

#Platesolve and correct position
fileout.write("    PRESERVE CAMERA SETTINGS\n")
fileout.write("        SET EXPOSURE TO 8\n")
fileout.write("        SET GAIN TO 100\n")
fileout.write("        MOUNT SOLVEANDSYNC\n")
fileout.write("    END PRESERVE\n")
fileout.write("    DELAY 10\n")

#Set guiding and frame quantity
fileout.write("    GUIDING CONNECT ABORT False\n")
fileout.write("    GUIDING START\n")
fileout.write("    DELAY 20\n")
fileout.write("    PRESERVE CAMERA SETTINGS\n")
fileout.write("        FRAMETYPE Light\n")
if band_type == 'b':
    fileout.write("        GUIDING DITHER EVERY 10 FRAMES\n")
else:#Assuming narrowband
    fileout.write("        GUIDING DITHER EVERY 6 FRAMES\n")
frame_duration = input("Enter number of hours to capture data\n")
# Remove 11 minutes of setup time from the first target so that stop time is correct
frame_duration_f = float(frame_duration) - (11.0 / 60.0)
if band_type == 'b':
    frame_qty = (float(frame_duration_f) * 3600) / 70.16
    frame_qty = math.floor(frame_qty)
else:#Assuming narrowband
    frame_qty = (float(frame_duration_f) * 3600) / 181.73
    frame_qty = math.floor(frame_qty)

# Handle the first 1-hour exposure
if band_type == 'b':
    if (frame_qty > 120):
        frame_qty_s = str(120)
        fileout.write("        CAPTURE " + frame_qty_s + " FRAMES REQUIREGUIDING True\n")
        fileout.write("        GUIDING DITHER EVERY STOP\n")
        fileout.write("    END PRESERVE\n")
        fileout.write("    GUIDING STOP\n")
        fileout.write("    GUIDING DISCONNECT\n\n")
        frame_qty = frame_qty - 120
    else:
        frame_qty_s = str(frame_qty)
        fileout.write("        CAPTURE " + frame_qty_s + " FRAMES REQUIREGUIDING True\n")
        fileout.write("        GUIDING DITHER EVERY STOP\n")
        fileout.write("    END PRESERVE\n")
        fileout.write("    GUIDING STOP\n")
        fileout.write("    GUIDING DISCONNECT\n\n")
        frame_qty = 0
else:#Assuming narrowband
    if (frame_qty > 40):
        frame_qty_s = str(40)
        fileout.write("        CAPTURE " + frame_qty_s + " FRAMES REQUIREGUIDING True\n")
        fileout.write("        GUIDING DITHER EVERY STOP\n")
        fileout.write("    END PRESERVE\n")
        fileout.write("    GUIDING STOP\n")
        fileout.write("    GUIDING DISCONNECT\n\n")
        frame_qty = frame_qty - 40
    else:
        frame_qty_s = str(frame_qty)
        fileout.write("        CAPTURE " + frame_qty_s + " FRAMES REQUIREGUIDING True\n")
        fileout.write("        GUIDING DITHER EVERY STOP\n")
        fileout.write("    END PRESERVE\n")
        fileout.write("    GUIDING STOP\n")
        fileout.write("    GUIDING DISCONNECT\n\n")
        frame_qty = 0

# Split up additional frames into 1 hour chunks to counteract tube flexure
while (frame_qty > 0):
    if band_type == 'b':
        if (frame_qty > 120):
            repeat_target(120)
            frame_qty = frame_qty - 120
        else:
            repeat_target(frame_qty)
            frame_qty = 0
    else:#Assuming narrowband
        if (frame_qty > 40):
            repeat_target(40)
            frame_qty = frame_qty - 40
        else:
            repeat_target(frame_qty)
            frame_qty = 0

#Insert additional targets
while input("Enter additional target? (y/n)") == 'y':
    extra_target()

#Final Shutdown
fileout.write("    MOUNT PARK\n")
if int(cooler_temp) != 100:
    fileout.write("    SET COOLER OFF\n")
fileout.write("END SEQUENCE\n")

fileout.close()

print("Sequence file generated!\n")
