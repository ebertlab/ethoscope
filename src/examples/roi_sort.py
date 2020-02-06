"""
  This script loads an image defining rois and tries to sort them into
  rows and columns
  
  To run: change to the examples directory of the ethoscope source tree
  and issue the command line:

    python3 roi_sort.py

  Copyright (C) 2019, University of Basel, Switzerland, Lukas Zimmermann

"""
__author__ = 'lukas'

import sys, os
import logging
import numpy as np


# change these variables according to how you name your input/output files
INPUT_DATA_DIR = "/home/lukas/tmp/AAA-Video/"
OUTPUT_DATA_DIR = "/home/lukas/tmp/ethoscope/"

#ROI_IMAGE = INPUT_DATA_DIR + "irbacklit_20200109_1525_4x4x6_squaremask_valued.png"
ROI_IMAGE = INPUT_DATA_DIR + "4xWellplates4x6_registred_squaremask_tight.png"
#INPUT_VIDEO = INPUT_DATA_DIR + "Basler_acA5472-17um__23065142__20200109_152536071.mp4"
INPUT_VIDEO = INPUT_DATA_DIR + "Basler_acA5472-17um__23065142__20200205_172106124.mp4"

logfile = OUTPUT_DATA_DIR + '20200205.log'
OUTPUT_VIDEO = OUTPUT_DATA_DIR + "20200205.avi"
OUTPUT_DB = OUTPUT_DATA_DIR + "results20200205.db"
#logfile = OUTPUT_DATA_DIR + 'results.log'
#OUTPUT_VIDEO = OUTPUT_DATA_DIR + "output.avi"
#OUTPUT_DB = OUTPUT_DATA_DIR + "output.db"

dbgImgWinSizeX = 2200
dbgImgWinSizeY = 1500

# setup logging
logging.basicConfig(filename=logfile, level=logging.INFO)
#logging.basicConfig(filename=logfile, level=logging.DEBUG)
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# add the handler to the root logger
logging.getLogger('').addHandler(console)

# Make the ethoscope packages accessible
package_path = os.path.join(os.path.dirname(sys.path[0]), '')
logging.info("path of ethoscope package: %s" % package_path)
sys.path.insert(0, package_path)

import cv2

# import the bricks from ethoscope package
# Use a mask image to define rois. Mask image must have black background, every non-black
# region defines a roi.
from ethoscope.roi_builders.img_roi_builder import ImgMaskROIBuilder
from ethoscope.core.monitor import Monitor
from ethoscope.trackers.adaptive_bg_tracker import AdaptiveBGModel
from ethoscope.utils.io import SQLiteResultWriter
from ethoscope.hardware.input.cameras import MovieVirtualCamera
from ethoscope.drawers.drawers import DefaultDrawer

# Generate ROIs from the mask image
logging.info("reading roi mask")
roi_builder = ImgMaskROIBuilder(ROI_IMAGE)

logging.info("building rois")
roi_builder.build(None)  # use image already loaded by ImgMaskROIBuilder instance
rois = roi_builder.gridSort(50, 50)

#for r in rois:
#  print("Roi %d: value: %d, (%d,%d)" % (r.idx, r._value, r._rectangle[0], r._rectangle[1]))

# We use a video input file as if it were a camera
cam = MovieVirtualCamera(INPUT_VIDEO)
logging.info("Loading \"%s\"-encoded movie with %d FPS of duration %d s."
             % (cam.fourcc, cam.frames_per_sec, cam._total_n_frames/ cam.frames_per_sec))

# we use a drawer to show inferred position for each animal, display frames and save them as a video
drawer = DefaultDrawer(OUTPUT_VIDEO, draw_frames = True,
                       framesWinSizeX = dbgImgWinSizeX, framesWinSizeY = dbgImgWinSizeY)

# We build our monitor
monitor = Monitor(cam, AdaptiveBGModel, rois)
#monitor = Monitor(cam, AdaptiveBGModel, rois,
#                  dbg_roi_value=14,
#                  dbg_roi_video_filename=("%s/roi_14_dbg.avi" % OUTPUT_DATA_DIR))

# Now everything is ready, we run the monitor with a result writer and a drawer
logging.info("run monitor with drawer")
with SQLiteResultWriter(OUTPUT_DB, rois) as rw:
     monitor.run(rw, drawer)


