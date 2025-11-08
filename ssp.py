# Parser for the sharpcap sequencer

import sys
import math
from enum import Enum
from enum import auto

class Telescope(Enum):
    ORION = 1
    TOWA = 2
    C6_HYPER = 3
    
class Filters(Enum):
    UVIR = 1
    LENHANCE = 2
    LPRO = 3
    D1 = 4
    D2 = 5

class Presets(Enum):
    ORION_OSC = "533 OSC"
    ORION_NB = "533 HO"
    C6H_OSC = "C6H OSC"
    C6H_NB = "C6H NB"

# Exposure time
EXPOSURE_ORION = {
    Filters.UVIR: 30,
    Filters.LPRO: 30,
    Filters.LENHANCE: 180
}
EXPOSURE_TOWA = {
    Filters.UVIR: 60,
    Filters.LPRO: 180
}
EXPOSURE_C6_HYPER = {
    Filters.UVIR: 30,
    Filters.LPRO: 30,
    Filters.LENHANCE: 120,
    Filters.D1: 240,
    Filters.D2: 240
}
EXPOSURE = {
    Telescope.ORION: EXPOSURE_ORION,
    Telescope.TOWA: EXPOSURE_TOWA,
    Telescope.C6_HYPER: EXPOSURE_C6_HYPER
}

# Platesolving exposure time
PLATE_EXPOSURE_ORION = {
    Filters.UVIR: 4,
    Filters.LPRO: 4,
    Filters.LENHANCE: 4
}
PLATE_EXPOSURE_TOWA = {
    Filters.UVIR: 12,
    Filters.LPRO: 12
}
PLATE_EXPOSURE_C6_HYPER = {
    Filters.UVIR: 1,
    Filters.LPRO: 1,
    Filters.LENHANCE: 2,
    Filters.D1: 4,
    Filters.D2: 4
}
PLATE_EXPOSURE = {
    Telescope.ORION: PLATE_EXPOSURE_ORION,
    Telescope.TOWA: PLATE_EXPOSURE_TOWA,
    Telescope.C6_HYPER: PLATE_EXPOSURE_C6_HYPER
}

# Time divider for frame calculation
TIMEDIV_ORION = {
    Filters.UVIR: 35.08,
    Filters.LPRO: 35.08,
    Filters.LENHANCE: 188
}
TIMEDIV_TOWA = {
    Filters.UVIR: 70.16,
    Filters.LPRO: 181.73
}
TIMEDIV_C6_HYPER = {
    Filters.UVIR: 35.08,
    Filters.LPRO: 35.08,
    Filters.LENHANCE: 133,
    Filters.D1: 247,
    Filters.D2: 247
}
TIMEDIV = {
    Telescope.ORION: TIMEDIV_ORION,
    Telescope.TOWA: TIMEDIV_TOWA,
    Telescope.C6_HYPER: TIMEDIV_C6_HYPER
}

# Frames per dither
DITHER_ORION = {
    Filters.UVIR: 12,
    Filters.LPRO: 12,
    Filters.LENHANCE: 6
}
DITHER_TOWA = {
    Filters.UVIR: 10,
    Filters.LPRO: 6
}
DITHER_C6_HYPER = {
    Filters.UVIR: 12,
    Filters.LPRO: 12,
    Filters.LENHANCE: 8,
    Filters.D1: 3,
    Filters.D2: 3
}
DITHER = {
    Telescope.ORION: DITHER_ORION,
    Telescope.TOWA: DITHER_TOWA,
    Telescope.C6_HYPER: DITHER_C6_HYPER
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
        scope_in = input("Select your telescope:\n[1] = Orion 130ST\n[2] = Towa 339\n[3] = C6 (Hyperstar)\n")
        self.telescope_type = Telescope(int(scope_in))
        
    def set_filter(self) -> None:
        filter_in = input("Select your filter::\n[1] = UV/IR\n[2] = L-Enhance\n[3] = L-Pro\n[4] = D1\n[5] = D2\n")
        self.filter_type = Filters(int(filter_in))
    
    def calc_capture_vals(self) -> None:
        self.exposure_time = EXPOSURE[self.telescope_type][self.filter_type]
        self.plate_exposure_time = PLATE_EXPOSURE[self.telescope_type][self.filter_type]
        self.timediv = TIMEDIV[self.telescope_type][self.filter_type]
        self.dither = DITHER[self.telescope_type][self.filter_type]
        
    def preset(self) -> None:
        preset_in = int(input("Select your preset:\n[1] = Orion OSC\n[2] = Orion NB\n[3] = C6 (Hyperstar) OSC\n[4] = C6 (Hyperstar) NB\n"))
        if preset_in == 1:
            preset_val = Presets.ORION_OSC
        elif preset_in == 2:
            preset_val = Presets.ORION_NB
        elif preset_in == 3:
            preset_val = Presets.C6H_OSC
        elif preset_in == 4:
            preset_val = Presets.C6H_NB
        else:
            raise ValueError("Invalid selection.")
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
        self.outfile.write("    PRESERVE CAMERA SETTINGS\n")
        self.outfile.write("        SET EXPOSURE TO " + str(self.plate_exposure_time) + "\n")
        self.outfile.write("        SET GAIN TO 100\n")
        self.outfile.write("        MOUNT SOLVEANDSYNC\n")
        self.outfile.write("    END PRESERVE\n")
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
        print('Example: sharp_sequence_parser.py')
        quit()

    #Prompt for filename and create file
    filename = ""
    filename = input("Set filename\n")
    filename += ".scs"
    fileout = open(filename, "w+")

    session = Session(fileout, 100, Filters.UVIR, Telescope.ORION, 0, 0, 0, 0)

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