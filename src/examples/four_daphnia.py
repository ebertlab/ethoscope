"""
  This is an example script making use of some of the features of the
  ethoscope framework.
  
  To run: change to the examples directory of the ethoscope source tree
  and issue the command line:

    python3 four_daphnia.py

  Copyright (C) 2019, University of Basel, Switzerland, Lukas Zimmermann

  This script processes a video of four vials each with a daphnia.
  Four regions of interest are defined by a mask image.
  The daphnia get marked by a red ellipse and the position data is written
  to a SQLite database file.

"""
__author__ = 'lukas'

import sys
sys.path.insert(0, '../ethoscope')
import cv2

INPUT_DATA_DIR = "./test_data/"
OUTPUT_DATA_DIR = "/tmp/"

# We import all the bricks from ethoscope package
from ethoscope.core.monitor import Monitor
from ethoscope.trackers.adaptive_bg_tracker import AdaptiveBGModel
from ethoscope.utils.io import SQLiteResultWriter
from ethoscope.hardware.input.cameras import MovieVirtualCamera
from ethoscope.drawers.drawers import DefaultDrawer

# You can also load other types of ROI builder.
# This one is for 20 tubes (two columns of ten rows)
#from ethoscope.roi_builders.target_roi_builder import SleepMonitorWithTargetROIBuilder
#from ethoscope.roi_builders.roi_builders import DefaultROIBuilder

# Use a mask image to define rois. Mask image must have black background, every non-black
# region defines a roi.
from ethoscope.roi_builders.img_roi_builder import ImgMaskROIBuilder

# change these three variables according to how you name your input/output files
INPUT_VIDEO = INPUT_DATA_DIR + "img00004_1028x752.mov"
ROI_IMAGE = INPUT_DATA_DIR + "img00004_1028x752_4rectangles.jpg"
#ROI_IMAGE = INPUT_DATA_DIR + "img00004_1028x752_4circles.jpg"

OUTPUT_VIDEO = OUTPUT_DATA_DIR + "my_output.avi"
OUTPUT_DB = OUTPUT_DATA_DIR + "results.db"

# We use a video input file as if it were a camera
cam = MovieVirtualCamera(INPUT_VIDEO)

# Generate ROIs from the mask image
print("reading roi mask")
roi_builder = ImgMaskROIBuilder(ROI_IMAGE)

# here, we generate ROIs automatically from the targets in the images
#roi_builder = SleepMonitorWithTargetROIBuilder()

print("building rois")
rois = roi_builder.build(cam)
"""
print("Rois: ");
for r in rois:
  print(r.polygon)
"""

# Go back to the first frame of the video. Needed when generating rois automatically
# from input video only
#cam.restart()

# we use a drawer to show inferred position for each animal, display frames and save them as a video
drawer = DefaultDrawer(OUTPUT_VIDEO, draw_frames = True)
# We build our monitor
monitor = Monitor(cam, AdaptiveBGModel, rois)

# Now everything is ready, we run the monitor with a result writer and a drawer
with SQLiteResultWriter(OUTPUT_DB, rois) as rw:
     monitor.run(rw, drawer)

