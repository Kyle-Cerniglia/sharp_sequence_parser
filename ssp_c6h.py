# Parser for the sharpcap sequencer
# Designed for an ASI533MC Pro mounted to a C6 with a Hyperstar

import sys
import math
from enum import Enum
from enum import auto
import csv
from pathlib import Path
from typing import Optional

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
    Filters.UVIR: 30,
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
    Filters.D1: 4,
    Filters.D2: 4
}
PLATE_EXPOSURE = {
    Telescope.C6_HYPER: PLATE_EXPOSURE_C6_HYPER
}

# Time divider for frame calculation
TIMEDIV_C6_HYPER = {
    Filters.UVIR: 35.08,
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
    Filters.UVIR: 12,
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
master_catalog = Path("catalogs") / "master.csv"
list_catalog = Path("catalogs") / "available_catalogs.txt"
catalog_search = ""
catalog_used = False

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
        self.telescope_type = Telescope(3)
        
    def set_filter(self) -> None:
        filter_in = input("Select your filter::\n[1] = UV/IR\n[2] = L-Enhance\n[3] = L-Pro\n[4] = D1\n[5] = D2\n")
        self.filter_type = Filters(int(filter_in))
    
    def calc_capture_vals(self) -> None:
        self.exposure_time = EXPOSURE[self.telescope_type][self.filter_type]
        self.plate_exposure_time = PLATE_EXPOSURE[self.telescope_type][self.filter_type]
        self.timediv = TIMEDIV[self.telescope_type][self.filter_type]
        self.dither = DITHER[self.telescope_type][self.filter_type]
        
    def preset(self) -> None:
        if self.filter_type in [Filters.UVIR, Filters.LENHANCE, Filters.LPRO]:
            preset_val = Presets.C6H_OSC
        else:
            preset_val = Presets.C6H_NB
        self.outfile.write(f"    LOAD PROFILE {preset_val.value}\n")

    def create_target(self) -> None:
        #Setup
        self.outfile.write("    DELAY 1\n")
        self.outfile.write("    STILL MODE\n")

        #Configure image formatting
        self.outfile.write("    SET COLOUR SPACE TO RAW16\n")
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
        
        if self.filter_type in [Filters.UVIR]:
            self.outfile.write("    TARGETNAME \"" + target_name + "_uvir\"\n")
        elif self.filter_type in [Filters.LPRO]:
            self.outfile.write("    TARGETNAME \"" + target_name + "_lpro\"\n")
        elif self.filter_type in [Filters.LENHANCE]:
            self.outfile.write("    TARGETNAME \"" + target_name + "_lenh\"\n")
        elif self.filter_type in [Filters.D1]:
            self.outfile.write("    TARGETNAME \"" + target_name + "_d1\"\n")
        elif self.filter_type in [Filters.D2]:
            self.outfile.write("    TARGETNAME \"" + target_name + "_d2\"\n")
        else:
            self.outfile.write("    TARGETNAME \"" + target_name + "\"\n")
            
        #Platesolve and correct position
        self.outfile.write("    MOUNT GOTO \"" + ra_h + " " + ra_m + " " + ra_s + ", " + dec_d + " " + dec_m + " " + dec_s + "\"\n")
        self.outfile.write("    DELAY 10\n")
        self.outfile.write("    PRESERVE CAMERA SETTINGS\n")
        self.outfile.write("        SET EXPOSURE TO " + str(self.plate_exposure_time) + "\n")
        self.outfile.write("        SET GAIN TO 100\n")
        self.outfile.write("        MOUNT SOLVEANDSYNC\n")
        self.outfile.write("    END PRESERVE\n")
        self.outfile.write("    DELAY 10\n")
        
        #Set guiding
        self.outfile.write("    GUIDING CONNECT ABORT False\n")
        self.outfile.write("    GUIDING STOP\n")
        self.outfile.write("    DELAY 5\n")
        self.outfile.write("    GUIDING START\n")
        self.outfile.write("    DELAY 10\n")
        
        #Set cooler temperature
        if int(self.temperature) != 100:
            self.outfile.write("    COOL DOWN TO " + self.temperature + " RATE 8 TOLERANCE 1\n")
        
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
        
    def shutdown(self) -> None:
        #Final Shutdown
        self.outfile.write("    MOUNT PARK\n")
        if int(self.temperature) != 100:
            self.outfile.write("    SET COOLER OFF\n")
        self.outfile.write("END SEQUENCE\n")
        self.outfile.close()

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

    session = Session(fileout, 100, Filters.UVIR, Telescope.C6_HYPER, 0, 0, 0, 0)

    session.start_time()
    
    session.set_temp()
    
    session.set_telescope()
    
    session.set_filter()
    
    session.calc_capture_vals()
    
    session.unpark()

    session.create_target()

    #Insert additional targets
    while input("Enter additional target? (y/n)") == 'y':
        session.create_target()

    session.shutdown()

    print("Sequence file generated!\n")

if __name__ == "__main__":
    main()