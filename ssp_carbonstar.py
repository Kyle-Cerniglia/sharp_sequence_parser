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
catalog_search = ""
catalog_used = False

def coords_direct() -> None:
    global ra_h
    global ra_m
    global ra_s
    global dec_d
    global dec_m
    global dec_s
    
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
    
    catalog_search = input("Enter catalog name (Ex. m101):\n")
    
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

class Session:
    def __init__(
        self, outfile, temperature, filter_type, telescope_type, exposure_time, timediv, dither, plate_exposure_time
    ):
        self.outfile = outfile
        self.temperature = temperature
        self.filter_type = filter_type
        self.telescope_type = telescope_type
        self.exposure_time = exposure_time
        self.timediv = timediv
        self.dither = dither
        self.plate_exposure_time = plate_exposure_time
    
    def start_time(self) -> None:
        #Set start time
        self.outfile.write("SEQUENCE\n")
    
        if input("Set a start time? (y/n)\n") == 'y':
            hour = input("Enter hour start (24h)\n")
            minute = input("Enter minute start\n")
            if int(minute) < 10:
                minute = "0" + minute
            if int(hour) < 12:
                self.outfile.write("    WAIT UNTIL LOCALTIME \"" + hour + ":" + minute + " AM\"\n")
            else:
                hour = str(int(hour) - 12);
                self.outfile.write("    WAIT UNTIL LOCALTIME \"" + hour + ":" + minute + " PM\"\n")
                
    def unpark(self) -> None:
        self.outfile.write("    DELAY 1\n")
        self.outfile.write("    MOUNT UNPARK\n")
        self.outfile.write("    MOUNT UNPARK\n")
    
    def set_temp(self) -> None:
        #Set cooler temperature
        self.temperature = input("Set cooler temp C (100 to disable)\n")
        
    def set_telescope(self) -> None:
        self.telescope_type = Telescope(2)
        
    def set_filter(self) -> None:
        global rgb_flag
        filter_in = input("Select your filter:\n[1] = Luminance\n[2] = Red\n[3] = Green\n[4] = Blue\n[5] = SII\n[6] = Ha\n[7] = OIII\n[8] = None\n[9] = RGB\n")
        self.filter_type = Filters(int(filter_in))
        if self.filter_type in [Filters.RGB]:
            rgb_flag = True
        else:
            rgb_flag = False
    
    def calc_capture_vals(self) -> None:
        self.exposure_time = EXPOSURE[self.telescope_type][self.filter_type]
        self.plate_exposure_time = PLATE_EXPOSURE[self.telescope_type][self.filter_type]
        self.timediv = TIMEDIV[self.telescope_type][self.filter_type]
        self.dither = DITHER[self.telescope_type][self.filter_type]
        
    def preset(self) -> None:
        if self.filter_type in [Filters.LUMINANCE, Filters.RED, Filters.GREEN, Filters.BLUE]:
            preset_val = Presets.CARBON_LRGB
        else:
            preset_val = Presets.CARBON_NB
        self.outfile.write(f"    LOAD PROFILE {preset_val.value}\n")        

    def create_target(self) -> None:
        #Setup
        self.outfile.write("    DELAY 1\n")
        self.outfile.write("    STILL MODE\n")

        #Configure image formatting
        self.outfile.write("    SET COLOUR SPACE TO MONO16\n")
        self.outfile.write("    SET OUTPUT FORMAT TO \"FITS files (*.fits)\"\n")
        
        self.preset()
            
        self.outfile.write("    MOUNT CONNECT\n")

        #Configure target
        if input("Lookup catalog target? (y/n)\n") == 'y':
            coords_catalog()
        else:
            coords_direct()

        #Set target name
        if(catalog_used):
            target_name = catalog_search
        else:
            target_name = input("Enter target name\n")
        
        if self.filter_type in [Filters.LUMINANCE]:
            self.outfile.write("    TARGETNAME \"" + target_name + "_l\"\n")
        elif self.filter_type in [Filters.RED]:
            self.outfile.write("    TARGETNAME \"" + target_name + "_r\"\n")
        elif self.filter_type in [Filters.GREEN]:
            self.outfile.write("    TARGETNAME \"" + target_name + "_g\"\n")
        elif self.filter_type in [Filters.BLUE]:
            self.outfile.write("    TARGETNAME \"" + target_name + "_b\"\n")
        elif self.filter_type in [Filters.SII]:
            self.outfile.write("    TARGETNAME \"" + target_name + "_s\"\n")
        elif self.filter_type in [Filters.HA]:
            self.outfile.write("    TARGETNAME \"" + target_name + "_h\"\n")
        elif self.filter_type in [Filters.OIII]:
            self.outfile.write("    TARGETNAME \"" + target_name + "_o\"\n")
        else:
            self.outfile.write("    TARGETNAME \"" + target_name + "\"\n")
        
        
        #Slew and plate solve to a position 5 degrees off of target (Towards the equator) to get a rough platesolve
        dec_d_offset = int(dec_d)
        if(dec_d_offset > 0):
            dec_d_offset = dec_d_offset - 5
        else:
            dec_d_offset = dec_d_offset + 5
        self.outfile.write("    MOUNT GOTO \"" + ra_h + " " + ra_m + " " + ra_s + ", " + str(dec_d_offset) + " " + dec_m + " " + dec_s + "\"\n")
        self.outfile.write("    DELAY 10\n")
        self.outfile.write("    PRESERVE CAMERA SETTINGS\n")
        self.outfile.write("        SET EXPOSURE TO 2\n")
        self.outfile.write("        SET GAIN TO 100\n")
        self.outfile.write("        MOUNT SOLVEANDSYNC\n")
        self.outfile.write("    END PRESERVE\n")
        self.outfile.write("    DELAY 10\n")

        #Platesolve and correct position twice
        self.outfile.write("    WHEEL MOVE TO 1\n")
        self.outfile.write("    DELAY 10\n")
        self.outfile.write("    MOUNT GOTO \"" + ra_h + " " + ra_m + " " + ra_s + ", " + dec_d + " " + dec_m + " " + dec_s + "\"\n")
        self.outfile.write("    DELAY 10\n")
        self.outfile.write("    PRESERVE CAMERA SETTINGS\n")
        self.outfile.write("        SET EXPOSURE TO 2\n")
        self.outfile.write("        SET GAIN TO 100\n")
        self.outfile.write("        MOUNT SOLVEANDSYNC\n")
        self.outfile.write("    END PRESERVE\n")
        self.outfile.write("    DELAY 10\n")
        self.outfile.write("    MOUNT GOTO \"" + ra_h + " " + ra_m + " " + ra_s + ", " + dec_d + " " + dec_m + " " + dec_s + "\"\n")
        self.outfile.write("    DELAY 10\n")
        self.outfile.write("    PRESERVE CAMERA SETTINGS\n")
        self.outfile.write("        SET EXPOSURE TO 2\n")
        self.outfile.write("        SET GAIN TO 100\n")
        self.outfile.write("        MOUNT SOLVEANDSYNC\n")
        self.outfile.write("    END PRESERVE\n")
        self.outfile.write("    DELAY 10\n")
        self.outfile.write("    WHEEL MOVE TO " + str(self.filter_type.value) + "\n")
        self.outfile.write("    DELAY 10\n")

        #Set guiding
        self.outfile.write("    GUIDING CONNECT ABORT False\n")
        self.outfile.write("    GUIDING STOP\n")
        self.outfile.write("    DELAY 5\n")
        self.outfile.write("    GUIDING START\n")
        self.outfile.write("    DELAY 10\n")
        
        #Set cooler temperature
        if int(self.temperature) != 100:
            self.outfile.write("    COOL DOWN TO " + self.temperature + " RATE 25 TOLERANCE 1\n")
            
        #Set exposure
        self.outfile.write("    SET EXPOSURE TO " + str(self.exposure_time) + "\n")
        
        #Set frame capture
        self.outfile.write("    PRESERVE CAMERA SETTINGS\n")
        self.outfile.write("        FRAMETYPE Light\n")
        self.outfile.write("        GUIDING DITHER EVERY " + str(self.dither) + " FRAMES\n")
        frame_duration = input("Enter number of hours to capture data\n")
        frame_qty = (float(frame_duration) * 3600) / self.timediv
        frame_qty = math.floor(frame_qty)
            
        frame_qty_s = str(frame_qty)
        self.outfile.write("        CAPTURE " + frame_qty_s + " FRAMES REQUIREGUIDING True\n")
        self.outfile.write("        GUIDING DITHER EVERY STOP\n")
        self.outfile.write("    END PRESERVE\n")
        self.outfile.write("    GUIDING STOP\n")
        self.outfile.write("    GUIDING DISCONNECT\n\n")
    
    def create_rgb_target(self) -> None:
        #Setup
        self.outfile.write("    DELAY 1\n")
        self.outfile.write("    STILL MODE\n")

        #Configure image formatting
        self.outfile.write("    SET COLOUR SPACE TO MONO16\n")
        self.outfile.write("    SET OUTPUT FORMAT TO \"FITS files (*.fits)\"\n")
        
        self.preset()
            
        self.outfile.write("    MOUNT CONNECT\n")

        #Configure target
        if input("Lookup catalog target? (y/n)\n") == 'y':
            coords_catalog()
        else:
            coords_direct()
        
        # Image RED

        #Set target name
        if(catalog_used):
            target_name = catalog_search
        else:
            target_name = input("Enter RGB target name\n")
        
        self.outfile.write("    TARGETNAME \"" + target_name + "_r\"\n")
        
        #Slew and plate solve to a position 5 degrees off of target (Towards the equator) to get a rough platesolve
        dec_d_offset = int(dec_d)
        if(dec_d_offset > 0):
            dec_d_offset = dec_d_offset - 5
        else:
            dec_d_offset = dec_d_offset + 5
        self.outfile.write("    MOUNT GOTO \"" + ra_h + " " + ra_m + " " + ra_s + ", " + str(dec_d_offset) + " " + dec_m + " " + dec_s + "\"\n")
        self.outfile.write("    DELAY 10\n")
        self.outfile.write("    PRESERVE CAMERA SETTINGS\n")
        self.outfile.write("        SET EXPOSURE TO 2\n")
        self.outfile.write("        SET GAIN TO 100\n")
        self.outfile.write("        MOUNT SOLVEANDSYNC\n")
        self.outfile.write("    END PRESERVE\n")
        self.outfile.write("    DELAY 10\n")

        #Platesolve and correct position twice
        self.outfile.write("    WHEEL MOVE TO 1\n")
        self.outfile.write("    DELAY 10\n")
        self.outfile.write("    MOUNT GOTO \"" + ra_h + " " + ra_m + " " + ra_s + ", " + dec_d + " " + dec_m + " " + dec_s + "\"\n")
        self.outfile.write("    DELAY 10\n")
        self.outfile.write("    PRESERVE CAMERA SETTINGS\n")
        self.outfile.write("        SET EXPOSURE TO 2\n")
        self.outfile.write("        SET GAIN TO 100\n")
        self.outfile.write("        MOUNT SOLVEANDSYNC\n")
        self.outfile.write("    END PRESERVE\n")
        self.outfile.write("    DELAY 10\n")
        self.outfile.write("    MOUNT GOTO \"" + ra_h + " " + ra_m + " " + ra_s + ", " + dec_d + " " + dec_m + " " + dec_s + "\"\n")
        self.outfile.write("    DELAY 10\n")
        self.outfile.write("    PRESERVE CAMERA SETTINGS\n")
        self.outfile.write("        SET EXPOSURE TO 2\n")
        self.outfile.write("        SET GAIN TO 100\n")
        self.outfile.write("        MOUNT SOLVEANDSYNC\n")
        self.outfile.write("    END PRESERVE\n")
        self.outfile.write("    DELAY 10\n")
        self.outfile.write("    WHEEL MOVE TO " + str(Filters.RED.value) + "\n")
        self.outfile.write("    DELAY 10\n")

        #Set guiding
        self.outfile.write("    GUIDING CONNECT ABORT False\n")
        self.outfile.write("    GUIDING STOP\n")
        self.outfile.write("    DELAY 5\n")
        self.outfile.write("    GUIDING START\n")
        self.outfile.write("    DELAY 10\n")
        
        #Set cooler temperature
        if int(self.temperature) != 100:
            self.outfile.write("    COOL DOWN TO " + self.temperature + " RATE 25 TOLERANCE 1\n")
            
        #Set exposure
        self.outfile.write("    SET EXPOSURE TO " + str(self.exposure_time) + "\n")
        
        #Set frame capture
        self.outfile.write("    PRESERVE CAMERA SETTINGS\n")
        self.outfile.write("        FRAMETYPE Light\n")
        self.outfile.write("        GUIDING DITHER EVERY " + str(self.dither) + " FRAMES\n")
        frame_duration = input("Enter number of hours to capture data\n")
        frame_qty = (float(frame_duration) * 3600) / self.timediv
        frame_qty = frame_qty / 3
        frame_qty = math.floor(frame_qty)
            
        frame_qty_s = str(frame_qty)
        self.outfile.write("        CAPTURE " + frame_qty_s + " FRAMES REQUIREGUIDING True\n")
        self.outfile.write("        GUIDING DITHER EVERY STOP\n")
        self.outfile.write("    END PRESERVE\n")
        
        #Image GREEN
        self.outfile.write("    TARGETNAME \"" + target_name + "_g\"\n")
        self.outfile.write("    WHEEL MOVE TO " + str(Filters.GREEN.value) + "\n")
        self.outfile.write("    DELAY 10\n")
        self.outfile.write("    PRESERVE CAMERA SETTINGS\n")
        self.outfile.write("        FRAMETYPE Light\n")
        self.outfile.write("        GUIDING DITHER EVERY " + str(self.dither) + " FRAMES\n")
        self.outfile.write("        CAPTURE " + frame_qty_s + " FRAMES REQUIREGUIDING True\n")
        self.outfile.write("        GUIDING DITHER EVERY STOP\n")
        self.outfile.write("    END PRESERVE\n")
        
        #Image BLUE
        self.outfile.write("    TARGETNAME \"" + target_name + "_b\"\n")
        self.outfile.write("    WHEEL MOVE TO " + str(Filters.BLUE.value) + "\n")
        self.outfile.write("    DELAY 10\n")
        self.outfile.write("    PRESERVE CAMERA SETTINGS\n")
        self.outfile.write("        FRAMETYPE Light\n")
        self.outfile.write("        GUIDING DITHER EVERY " + str(self.dither) + " FRAMES\n")
        self.outfile.write("        CAPTURE " + frame_qty_s + " FRAMES REQUIREGUIDING True\n")
        self.outfile.write("        GUIDING DITHER EVERY STOP\n")
        self.outfile.write("    END PRESERVE\n")
        
        #Finish target
        self.outfile.write("    GUIDING STOP\n")
        self.outfile.write("    GUIDING DISCONNECT\n\n")
        
    def shutdown(self) -> None:
        #Final Shutdown
        self.outfile.write("    MOUNT PARK\n")
        if int(self.temperature) != 100:
            self.outfile.write("    SET COOLER OFF\n")
        self.outfile.write("    WHEEL MOVE TO 1\n")
        self.outfile.write("END SEQUENCE\n")
        self.outfile.close()

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

    session = Session(fileout, 100, Filters.LUMINANCE, Telescope.CARBON, 0, 0, 0, 0)

    session.start_time()
    
    session.set_temp()
    
    session.set_telescope()
    
    session.set_filter()
    
    session.calc_capture_vals()
    
    session.unpark()

    if (rgb_flag == True):
        session.create_rgb_target()
    else:
        session.create_target()

    #Insert additional targets
    while input("Enter additional target? (y/n)") == 'y':
        session.set_filter()
        session.calc_capture_vals()
        if (rgb_flag == True):
            session.create_rgb_target()
        else:
            session.create_target()

    session.shutdown()

    print("Sequence file generated!\n")

if __name__ == "__main__":
    main()