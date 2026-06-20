from pathlib import Path
import csv

master_catalog = Path("catalogs") / "master.csv"
list_catalog = Path("catalogs") / "available_catalogs.txt"

def coords_direct():    
    ra_h = input("Enter J2000 coordinates (RA h)\n")
    ra_m = input("Enter J2000 coordinates (RA m)\n")
    ra_s = input("Enter J2000 coordinates (RA s)\n")
    dec_d = input("Enter J2000 coordinates (DEC d)\n")
    dec_m = input("Enter J2000 coordinates (DEC m)\n")
    dec_s = input("Enter J2000 coordinates (DEC s)\n")
    catalog_used = False
    return ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used
    
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
                    return ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used, catalog_search
            #If you got here, then the item wasn't found
            print("Catalog object not found, please enter in coordinates manually\n")
            ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used = coords_direct()
            return ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used, catalog_search

    except FileNotFoundError:
        print("Catalog file not found, please enter in coordinates manually\n")
        ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used = coords_direct()
        return ra_h, ra_m, ra_s, dec_d, dec_m, dec_s, catalog_used, catalog_search
        
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

def unpark(outfile) -> None:
    outfile.write("    DELAY 1\n")
    outfile.write("    MOUNT UNPARK\n")
    outfile.write("    MOUNT UNPARK\n")
    
def set_temp(temperature) -> None:
    temperature = input("Set cooler temp C (100 to disable)\n")
    return temperature
    
def calc_capture_vals(filter_type, exposure_c, plate_c, timediv_c, dither_c) -> None:
    exposure_time = exposure_c[filter_type.name].value
    plate_exposure_time = plate_c[filter_type.name].value
    timediv = timediv_c[filter_type.name].value
    dither = dither_c[filter_type.name].value
    
    return exposure_time, plate_exposure_time, timediv, dither
    
def start_guiding(outfile) -> None:
    outfile.write("    GUIDING CONNECT ABORT False\n")
    outfile.write("    GUIDING STOP\n")
    outfile.write("    DELAY 5\n")
    outfile.write("    GUIDING START\n")
    outfile.write("    DELAY 10\n")
    
def stop_guiding(outfile) -> None:
    outfile.write("    GUIDING STOP\n")
    outfile.write("    GUIDING DISCONNECT\n\n")
    
def write_light_capture(outfile, frame_qty: int, dither: int) -> None:
    outfile.write("    PRESERVE CAMERA SETTINGS\n")
    outfile.write("        FRAMETYPE Light\n")
    outfile.write("        GUIDING DITHER EVERY " + str(dither) + " FRAMES\n")
    outfile.write("        CAPTURE " + str(frame_qty) + " FRAMES REQUIREGUIDING True\n")
    outfile.write("        GUIDING DITHER EVERY STOP\n")
    outfile.write("    END PRESERVE\n")
    
def cool_camera(outfile, cool_c, temperature) -> None:
    if int(temperature) != 100:
        outfile.write("    COOL DOWN TO " + temperature + " RATE " + str(cool_c["RATE"].value) + " TOLERANCE " + str(cool_c["TOLERANCE"].value) + "\n")
        
def shutdown(outfile, wheel, temperature) -> None:
    outfile.write("    MOUNT PARK\n")
    if int(temperature) != 100:
        outfile.write("    SET COOLER OFF\n")
    if wheel == True:
        outfile.write("    WHEEL MOVE TO 1\n")
    outfile.write("END SEQUENCE\n")
    outfile.close()
    
def autofocus() -> None:
    rough_focus = int(input("Set autofocuser rough focal point (Set to -1 to disable):\n"))
    return rough_focus