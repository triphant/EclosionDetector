# EclosionDetector.py
#
# This Fiji script detects eclosion events in an image stack and saves the
# frame numbers in a csv files. For further information see README.md
#
# Author: Tilman Triphan, tilman.triphan@uni-leipzig.de
# License: GNU General Public License v3.0
# Copyright (C) 2023  Tilman Triphan
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Tilman Triphan, 2023-04-18

import csv
import math
import os

from ij import IJ, ImagePlus, ImageStack, WindowManager
from ij.gui import NewImage,Roi
from ij.measure import ResultsTable
from ij.plugin.frame import RoiManager

# Change these values if necessary
# Where to save the results (change this or keep home directory)
savepath = IJ.getDirectory("home")
# Select a slice when all pupae have settled and are clearly visible
start_slice = 101
# Max grey value for inital pupae detection. Pupae should be darker than the background
threshold = 90

# Pupae are only recognized if their area is between 
# min_area_factor*average_pupae_area and max_area_factor*average_pupae_area
min_area_factor = 0.5
max_area_factor = 2.0
# You can also define min_area and max_area manually
# This is dependend on camera resolution and optics
min_area = 10
max_area = 350
# The minimum brightness change between a hatched and unhatched pupa
# Empty pupal cases should be brighter
diff_hatch = 10
# Detection method, you can use "Mean","Median","Mode","Min" and "Max"
diff_method = "Median"
# Starting frame for detection
idx_min = 101
# Last frame for detection
idx_max = 600

# Area of found objects
area = []
# List of eclosion events
eclosion = []

# Try to identify invalid eclosion events (e.g. flies walking over pupae)
check_error = True
# How many frames before and after to look for invalid eclosion events
timewindow_error = 3
# Minimum difference between the maximum and minimum grey value for error correction
error_min = -2

# How many frames before and after eclosion event should be included
timewindow_hatch = 5
# width of single mosaik tile
mosaic_size = 64
# font size used for labeling mosaik tiles
font_size = 10

# Get the active image. Any stack should work
image = IJ.getImage()
title = image.getTitle()
stack = image.getStack()
n_slices = stack.getSize()

# Set default measurements
IJ.run("Set Measurements...", "area mean modal min centroid median stack redirect=None decimal=3")

def median(array):
    x = sorted(array)
    if len(x) % 2:
        return x[int(math.floor(len(x)/2))]
    else:
        m = len(x)/2
        return round((x[m]+x[m+1])/2)

def find_objects():
    # Find all objects
    image.killRoi()
    image.setSlice(start_slice)
    IJ.setThreshold(0,threshold)
    IJ.run(image, "Analyze Particles...", "size="+str(min_area)+"-Infinity exclude clear add slice")
    rt = ResultsTable.getResultsTable()
    area = rt.getColumn(rt.getColumnIndex("Area"))
    IJ.run("Clear Results")
    return area

def autoset_size():
    # Try to set the minimum and maximum area for pupae. This is dependend on camera resolution and zoom.
    print("Trying to autodetect settings for pupal size...")
    min_area = math.ceil(median(area)*min_area_factor)
    max_area = math.ceil(median(area)*max_area_factor)
    print "Expected minimum pupa area:",min_area
    print "Expected maximum pupa area:",max_area
    return min_area, max_area

def find_valid(area):
    # return indices of objects that are within area parameters
    return [i for (a,i) in zip(area,range(1,len(area)+1)) if a >= min_area and a <= max_area]

def find_hatching(idx_valid,block_start,block_end,diff_hatch_th):
    rois = rm.getRoisAsArray()
    hatching = {}
    for i in range(0, len(idx_valid)):
        n = idx_valid[i]-1
        image.setRoi(rois[n])
        # Process all frames for currect object
        for j in range(block_start, block_end+1):
            image.setSlice(j)
            IJ.run(image, "Measure", "")
        rt = ResultsTable.getResultsTable()
        # Get the grey values for each pupa at every frame ("Mean","Median" or "Mode")
        compVals = rt.getColumn(rt.getColumnIndex(diff_method))
        # Calculate the difference
        delta = [j-i for i,j in zip(compVals, compVals[1:])]
        # Detect frames where there is a big difference in grey value
        idx_hatch = [m for (l,m) in zip(delta,range(1,len(delta)+1)) if l >= diff_hatch_th]
        h = set(idx_hatch)
        if (len(h) > 0):
            frame = h.pop()
            x = int(rt.getValue("X",frame))
            y = int(rt.getValue("Y",frame))
            frame_nr = frame + block_start
            if (check_error == True):
                # Make sure we don't go before first or behind last frame
                frameMin = min(frame-timewindow_error,1)
                frameMax = min(frame+timewindow_error,len(compVals)-1)
                # Check if the pupa gets darker after "eclosing", i.e. it was an invalid detection
                delta_error = compVals[frameMin]-compVals[frameMax]
            if (check_error == True) and (delta_error > error_min):
                print("{} Frame: {} X: {} Y: {} - invalid detection".format(n+1,frame_nr, x, y))
            else:
                hatching[n] = frame
                print("{} Frame: {} X: {} Y: {}".format(n+1,frame_nr, x, y))
                # Create snapshot of eclosing fly
                image.setRoi(Roi(x-(mosaic_size/2), y-(mosaic_size/2), mosaic_size, mosaic_size))
                IJ.run(image, "Duplicate...", "title=[Pupa "+str(n+1)+" "+str(frame_nr)+"] duplicate range="+str(frame_nr-timewindow_hatch)+"-"+str(frame_nr+timewindow_hatch)+" use")
                eclosion.append({"FrameID":image.getStack().getSliceLabel(frame_nr),"PupaID":n+1,"FrameNr":frame_nr,"X":x,"Y":y})
        IJ.run("Clear Results")

def create_mosaic(code=""):
    print("Creating mosaic")
    image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
    pupae = [t for t in image_titles if t.startswith("Pupa")]
    hatched = len(pupae)
    if hatched == 0:
        print("No snapshots found!")
        return
    # Calculate number of columns and rows needed
    cols = math.ceil(math.sqrt(hatched))
    rows = math.ceil(hatched/cols)
    x = cols*mosaic_size+(cols+1)*2
    y = rows*mosaic_size+(rows+1)*2
    # Create new image of required size
    imp = NewImage.createImage("Hatching", int(x), int(y), timewindow_hatch*2+1, 8, NewImage.FILL_BLACK)
    imp.show()
    # Insert snapshots of eclosing flies
    for i in range(0,hatched):
        r =  int(math.ceil((i+1) / rows / (cols / rows)))-1
        y = int(r*mosaic_size+(r+1)*2)
        c = ((int(i)) % int(cols))
        x = c*mosaic_size+(c+1)*2
        IJ.run("Insert...", "source=["+pupae[i]+"] destination=Hatching x="+str(x)+" y="+str(y))
        WindowManager.getImage(pupae[i]).close()
    # Add information
    stack = imp.getStack()
    for f in range(0,timewindow_hatch*2+1):
        proc = stack.getProcessor(f+1)
        proc.setFont(proc.getFont().deriveFont(font_size * 1.0))
        proc.setAntialiasedText(True)
        for i in range(0,hatched):
            r =  int(math.ceil((i+1) / rows / (cols / rows)))-1
            y = int(r*mosaic_size+(r+1)*2)
            c = ((int(i)) % int(cols))
            x = c*mosaic_size+(c+1)*2
            proc.drawString(str(eclosion[i]["PupaID"]), x+4, y+4+font_size)
        stack.setProcessor(proc, f+1)
    imp.setStack(stack)
    # Save image
    print("Saving mosaic...")
    filename = os.path.join(savepath,"Hatching_{}_{}".format(code,image.getTitle()))
    IJ.saveAs(imp, "Tiff", filename)
    imp.close()

def save_csv(code="eclosion"):
    if len(eclosion) == 0:
        print("No eclosion events found!")
        return
    print("Saving csv file...")
    csvfile = open(os.path.join(savepath, code+".csv"), 'wb')
    csvwriter = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    csvwriter.writerow(["FrameID","FrameNr","PupaID","X","Y"])
    for i in range(0,len(eclosion)):
        print ("ID: {} Frame: {} Pupa: {} X: {} Y: {}".format(eclosion[i]["FrameID"],eclosion[i]["FrameNr"],eclosion[i]["PupaID"],eclosion[i]["X"],eclosion[i]["Y"]))
        csvwriter.writerow([eclosion[i]["FrameID"],eclosion[i]["FrameNr"],eclosion[i]["PupaID"],eclosion[i]["X"],eclosion[i]["Y"]])
    csvfile.close()

# This is the entry point of the script
print("Start processing...")
area = find_objects()
(min_area,max_area) = autoset_size()
idx_valid = find_valid(area)
print len(idx_valid),"objects found."
rm = RoiManager.getInstance()
find_hatching(idx_valid,idx_min,idx_max,diff_hatch)
create_mosaic("new")
save_csv(title)

print("Processing complete.")
