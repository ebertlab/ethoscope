"""
  This is an example script making use of some of the features of the
  ethoscope framework.
  
  To run: change to the examples directory of the ethoscope source tree
  and issue the command line:

    python3 testplatte24.py

  Copyright (C) 2019, University of Basel, Switzerland, Lukas Zimmermann

  This script processes a video of four vials each with a daphnia.
  Four regions of interest are defined by a mask image.
  The daphnia get marked by a red ellipse and the position data is written
  to a SQLite database file.

"""
__author__ = 'lukas'

import sys, os
import logging

# change these variables according to how you name your input/output files
INPUT_DATA_DIR = "/home/lukas/tmp/AAA-Video/"
OUTPUT_DATA_DIR = "/home/lukas/tmp/ethoscope/"

#INPUT_VIDEO = INPUT_DATA_DIR + "Basler_acA5472-17um__23065142__20200108_113852055.mp4"
INPUT_VIDEO = INPUT_DATA_DIR + "Basler_acA5472-17um__23065142__20200109_152536071.mp4"
#INPUT_VIDEO = INPUT_DATA_DIR + "Basler_acA5472-17um__23065142__20200109_152536071_cropped.mp4"
#INPUT_VIDEO = INPUT_DATA_DIR + "Basler_acA5472-17um__23065142__20200110_122211091.mp4"

#ROI_IMAGE = INPUT_DATA_DIR + "irbacklit_20200108_1138_mask.jpg"
#ROI_IMAGE = INPUT_DATA_DIR + "irbacklit_20200108_1138_squaremask.jpg"
#ROI_IMAGE = INPUT_DATA_DIR + "irbacklit_20200108_1138_4x6_squaremask.png"
#ROI_IMAGE = INPUT_DATA_DIR + "irbacklit_20200108_1138_4x4x6_squaremask.png"
#ROI_IMAGE = INPUT_DATA_DIR + "irbacklit_20200109_1525_4x4x6_squaremask.png"
ROI_IMAGE = INPUT_DATA_DIR + "irbacklit_20200109_1525_4x4x6_squaremask_valued.png"
#ROI_IMAGE = INPUT_DATA_DIR + "irbacklit_20200109_1525_cropped.png"
#ROI_IMAGE = INPUT_DATA_DIR + "20200110.png"

OUTPUT_VIDEO = OUTPUT_DATA_DIR + "my_output.avi"
OUTPUT_DB = OUTPUT_DATA_DIR + "results.db"

logfile = OUTPUT_DATA_DIR + 'testplatte24.log'

# setup logging
logging.basicConfig(filename=logfile, level=logging.INFO)

# Make the ethoscope packages accessible
package_path = os.path.join(os.path.dirname(sys.path[0]), '')
logging.info("path of ethoscope package: %s" % package_path)
sys.path.insert(0, package_path)

import cv2

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

# We use a video input file as if it were a camera
cam = MovieVirtualCamera(INPUT_VIDEO)

# Generate ROIs from the mask image
logging.info("reading roi mask")
roi_builder = ImgMaskROIBuilder(ROI_IMAGE)

# here, we generate ROIs automatically from the targets in the images
#roi_builder = SleepMonitorWithTargetROIBuilder()

logging.info("building rois")
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
logging.info("run monitor with drawer")
with SQLiteResultWriter(OUTPUT_DB, rois) as rw:
     monitor.run(rw, drawer)

