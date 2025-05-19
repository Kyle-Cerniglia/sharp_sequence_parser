# Parser for the sharpcap sequencer

import sys
import math
from enum import Enum
from enum import auto

class Telescope(Enum):
    TOWA = 2
    
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
    TOWA = "MC8"

# Exposure time
EXPOSURE_TOWA = {
    Filters.LUMINANCE: 2,
    Filters.RED: 60,
    Filters.GREEN: 60,
    Filters.BLUE: 60,
    Filters.SII: 180,
    Filters.HA: 180,
    Filters.OIII: 180,
    Filters.NONE: 2
}
EXPOSURE = {
    Telescope.TOWA: EXPOSURE_TOWA
}

# Platesolving exposure time
PLATE_EXPOSURE_TOWA = {
    Filters.LUMINANCE: 2,
    Filters.RED: 2,
    Filters.GREEN: 2,
    Filters.BLUE: 2,
    Filters.SII: 2,
    Filters.HA: 2,
    Filters.OIII: 2,
    Filters.NONE: 2
}
PLATE_EXPOSURE = {
    Telescope.TOWA: PLATE_EXPOSURE_TOWA
}

# Time divider for frame calculation
TIMEDIV_TOWA = {
    Filters.LUMINANCE: 70.16,
    Filters.RED: 70.16,
    Filters.GREEN: 70.16,
    Filters.BLUE: 70.16,
    Filters.SII: 181.73,
    Filters.HA: 181.73,
    Filters.OIII: 181.73,
    Filters.NONE: 70.16
}
TIMEDIV = {
    Telescope.TOWA: TIMEDIV_TOWA
}

# Frames per dither
DITHER_TOWA = {
    Filters.LUMINANCE: 10,
    Filters.RED: 10,
    Filters.GREEN: 10,
    Filters.BLUE: 10,
    Filters.SII: 6,
    Filters.HA: 6,
    Filters.OIII: 6,
    Filters.NONE: 10
}
DITHER = {
    Telescope.TOWA: DITHER_TOWA
}

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
        filter_in = input("Select your filter::\n[1] = Luminance\n[2] = Red\n[3] = Green\n[4] = Blue\n[5] = SII\n[6] = Ha\n[7] = OIII\n[8] = None\n")
        self.filter_type = Filters(int(filter_in))
    
    def calc_capture_vals(self) -> None:
        self.exposure_time = EXPOSURE[self.telescope_type][self.filter_type]
        self.plate_exposure_time = PLATE_EXPOSURE[self.telescope_type][self.filter_type]
        self.timediv = TIMEDIV[self.telescope_type][self.filter_type]
        self.dither = DITHER[self.telescope_type][self.filter_type]
        
    def preset(self) -> None:
        preset_val = Presets.TOWA
        self.outfile.write(f"    LOAD PROFILE \"{preset_val.value}\"\n")

    def create_target(self) -> None:
        #Setup
        self.outfile.write("    DELAY 1\n")
        self.outfile.write("    STILL MODE\n")

        #Set cooler temperature
        if int(self.temperature) != 100:
            self.outfile.write("    COOL DOWN TO " + self.temperature + " RATE 8 TOLERANCE 1\n")

        #Configure image formatting
        self.outfile.write("    SET COLOUR SPACE TO RAW16\n")
        self.outfile.write("    SET OUTPUT FORMAT TO \"FITS files (*.fits)\"\n")
        
        self.preset()
            
        self.outfile.write("    MOUNT CONNECT\n")

        #Configure target
        ra_h = input("Enter J2000 coordinates (RA h)\n")
        ra_m = input("Enter J2000 coordinates (RA m)\n")
        ra_s = input("Enter J2000 coordinates (RA s)\n")
        dec_d = input("Enter J2000 coordinates (DEC d)\n")
        dec_m = input("Enter J2000 coordinates (DEC m)\n")
        dec_s = input("Enter J2000 coordinates (DEC s)\n")
        self.outfile.write("    MOUNT GOTO \"" + ra_h + " " + ra_m + " " + ra_s + ", " + dec_d + " " + dec_m + " " + dec_s + "\"\n")
        self.outfile.write("    DELAY 20\n")

        #Set target name
        target_name = input("Enter target name\n")
        self.outfile.write("    TARGETNAME \"" + target_name + "\"\n")
        self.outfile.write("    SET EXPOSURE TO " + str(self.exposure_time) + "\n")

        #Platesolve and correct position
        self.outfile.write("    WHEEL MOVE TO 1\n")
        self.outfile.write("    DELAY 10\n")
        self.outfile.write("    PRESERVE CAMERA SETTINGS\n")
        self.outfile.write("        SET EXPOSURE TO 2\n")
        self.outfile.write("        SET GAIN TO 100\n")
        self.outfile.write("        MOUNT SOLVEANDSYNC\n")
        self.outfile.write("    END PRESERVE\n")
        self.outfile.write("    DELAY 10\n")
        self.outfile.write("    WHEEL MOVE TO " + str(self.filter_type.value) + "\n")
        self.outfile.write("    DELAY 10\n")

        #Set guiding and frame quantity
        self.outfile.write("    GUIDING CONNECT ABORT False\n")
        self.outfile.write("    GUIDING START\n")
        self.outfile.write("    DELAY 20\n")
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
        print('Example: ssp_towa.py')
        quit()

    #Prompt for filename and create file
    filename = ""
    filename = input("Set filename\n")
    filename += ".scs"
    fileout = open(filename, "w+")

    session = Session(fileout, 100, Filters.LUMINANCE, Telescope.TOWA, 0, 0, 0, 0)

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