# Parser for the sharpcap sequencer (Towa telescope)

import sys
import math

class Session:
    def __init__(
        self, outfile, temperature, filter_type
    ):
        self.outfile = outfile
        self.temperature = temperature
        self.filter_type = filter_type
    
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
        
    def set_filter(self) -> None:    
        self.filter_type = input("Is the filter (b)roadband (UV/IR Cut) or (n)arrowband (L-Pro)?\n")

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
        if self.filter_type == 'b':
            self.outfile.write("    LOAD PROFILE \"533 OSC\"\n")
        if self.filter_type == 'n':
            self.outfile.write("    LOAD PROFILE \"533 HO\"\n")
            
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
        if self.filter_type == 'b':
            self.outfile.write("    SET EXPOSURE TO 60\n")
        if self.filter_type == 'n':
            self.outfile.write("    SET EXPOSURE TO 180\n")

        #Platesolve and correct position
        self.outfile.write("    PRESERVE CAMERA SETTINGS\n")
        self.outfile.write("        SET EXPOSURE TO 12\n")
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
        if self.filter_type == 'b':
            self.outfile.write("        GUIDING DITHER EVERY 10 FRAMES\n")
        else:#Assuming narrowband
            self.outfile.write("        GUIDING DITHER EVERY 6 FRAMES\n")
        frame_duration = input("Enter number of hours to capture data\n")
        if self.filter_type == 'b':
            frame_qty = (float(frame_duration) * 3600) / 70.16
            frame_qty = math.floor(frame_qty)
        else:#Assuming narrowband
            frame_qty = (float(frame_duration) * 3600) / 181.73
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
    filename = "sequence.scs"
    filename = input("Set filename\n")
    fileout = open(filename, "w+")

    session = Session(fileout, 100, "b")

    session.start_time()
    
    session.set_temp()
    
    session.set_filter()
    
    session.unpark()

    session.create_target()

    #Insert additional targets
    while input("Enter additional target? (y/n)") == 'y':
        session.create_target()

    session.shutdown()

    print("Sequence file generated!\n")

if __name__ == "__main__":
    main()