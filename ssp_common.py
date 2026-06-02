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