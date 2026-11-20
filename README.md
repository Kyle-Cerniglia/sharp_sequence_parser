# sharp_sequence_parser

CHANGELOG

v1.0 (11/19/2026)

- INITIAL RELEASE


WHAT IS THIS TOOL?

Sharp Sequence Parser is a tool to generate sequencer files used by the SharpCap astrophotography software through a python CLI instead of using the clunky tool within SharpCap.

After installing Python 3.11.3 (Newer versions will >probably< work), you can either run the python files in the top level folder through the CLI, or just click on the batch files to automatically run.


WHAT ARE THESE FILES?

Each top level python file (Excluding ssp_common.py) is configured for a specific telescope setup:


ssp_c6h.py:

Scope: Celestron C6 with a Starizona Hyperstar v4 lens

Camera: ZWO ASI533MC Pro

Mount: Skywatcher EQ6-R

Filters: Optolong UV/IR, Optolong L-eNhance, Optolong L-Pro, Askar D1, Askar D2


ssp_carbonstar.py:

Scope: Carbonstar 150

Camera/Filter Wheel: QHY Minicam8MM

Focuser: Pegasus Astro 3

Mount: Skywatcher EQ6-R

Filters: Minicam mono filters (LRGBSHO)


ssp_towa.py:

Scope: Towa 339

Camera: QHY Minicam8MM

Mount: Skywatcher EQ6-R

Filters: Minicam mono filters (LRGBSHO)



While each telescope file is a collection of functions that execute to generate your sequence file, the ssp_common.py file contains functions that are common to all the main python files. Most functions should belong here, unless there is something unique to a particular telescope setup.


To assist in selecting targets to image, a folder of catalogs is included. In the subfolder all the individual catalogs are stored, however the data actually used by the software is the master.csv, which contains the data from all of the catalogs.

The available_catalogs.txt file is used by the software to display a list of catalogs that are present.


The Original Samples folder shows examples of the sequencer outputs.


HOW TO USE THE CLI TOOL

For this example, I will walk through the use of ssp_carbonstar.py as this is the most complicated telescope setup (Mount, camera, filter wheel, focuser).


1: Filename: Enter your desired filename (The .scs file extension is automatically appended).

2: Start Time: If you would like the sequence to run when you load it into SharpCap, press 'n'. If you want the sequence to hold until a specific time, then press 'y'. It will prompt you for the hour (24hr format), then the minute.

3: Cooler: Set your desired cooler temperature in degrees celcius. If you want the cooler disabled, set the temperature to 100.

4: Filter: Based on the list of filters within the python file, you can select which filter you want to use by entering the number indicated next to the filter name (This is the QHY monochrome filter wheel containing LRGBSHO and an 8th empty slot). In this example, there is an option for '9', which will split your imaging time equally across the RGB filters (Red block first, then the green block, then the blue block).

5: Autofocuser: If you do not need the system to autofocus, enter '-1'. If you would like the system to perform an autofocus, then enter the known approximate focus point in steps. The scope will scan -100 to +100 steps from the reference point split into 21 steps.

6: Catalog: If you wish to manually enter in the coordinates of a target, skip this request for a catalog lookup by pressing 'n'. If you would like to use a catalog, press 'y'. You will be given a list of loaded catalogs and how to format the designation (For example, if you want to select Messier 42, you would enter 'm42'. If you wanted Sharpless-2 220, you would enter 'sh2-220' as indicated). If the object is not present in the catalog, it will skip the catalog lookup.

7: Manual Coordinates: If the catalog function was not used (Or the desired object was not found in the catalog), you will be prompted to enter in the coordinates of the target manually. All coordinates are in J2000 format, and it will prompt you for each part of the coordinates individually (First RA Hours, then RA Minutes, etc).

8: Name: Enter in your desired target name for the output files. A suffix will be automatically appended to this name to indicate the filter used (Ex: m42_b is Messier 42 with the Blue filter).

9: Duration: Enter in the duration for the image capture in hours (WARNING: This software does not currently handle meridian flips automatically! If this is needed, manually enter in a second imaging session on the same target).

10: Next Target: If you are done entering in sequence data, press 'n'. If you need to enter another target that will image after the prior target, press 'y' and the software will repeat the prior prompts for the new target. When complete, your sequencer file will appear in the folder.


KNOWN BUGS

- Sometimes the sequence fails to unpark my mount when it starts, so I usually unpark it manually through EQMOD when loading the sequence.
