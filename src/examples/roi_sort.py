#!/usr/bin/env python3
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
import sys
from argparse import ArgumentParser

def main(argv):

  parser = ArgumentParser(description='Runs an Ethoscope machinery on the given video file,' +
                                      ' which is meant to be a recording of single daphnia moving' +
                                      ' in a bunch of wells.' +
                                      ' The area of each well is determined by non-black regions' +
                                      ' in the supplied regions of interest (ROI) image file.' +
                                      ' Optionally an output video may be produced, documenting the ' +
                                      ' detection of animals.'
                         )
  parser.add_argument("-i", "--input-video", dest="inp_video_filename", required=True,
                      help="The video file to be processed.", metavar='<input video filename>')
  parser.add_argument("-o", "--output-db", dest="db_filename", required=True,
                      help="Create Sqlite DB file  for storing results.", metavar='<output DB filename>')
  parser.add_argument("-r", "--roi_image", dest="roi_filename", required=True,
                      help="Create Sqlite DB file DB_FILENAME for storing results.", metavar='<roi image>')
  parser.add_argument("-a", "--output-video", dest="outp_video_filename",
                      help="The annotated output video file.", metavar='<output video filename>')
  parser.add_argument("-b", "--single-roi-video", dest="single_roi_video_filename",
                      help="For debugging purpose a video file of a single roi may be produced.",
                      metavar='<single roi video filename>')

  args = parser.parse_args()

  # TODO: make this a command line option  
  dbg_single_roi_number = 47

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
  roi_builder = ImgMaskROIBuilder(args.roi_filename)

  logging.info("building rois")
  roi_builder.build(None)  # use image already loaded by ImgMaskROIBuilder instance
  rois = roi_builder.gridSort(50, 50)

  #for r in rois:
  #  print("Roi %d: value: %d, (%d,%d)" % (r.idx, r._value, r._rectangle[0], r._rectangle[1]))

  # We use a video input file as if it were a camera
  cam = MovieVirtualCamera(args.inp_video_filename)
  logging.info("Loading \"%s\"-encoded movie with %d FPS of duration %d s."
               % (cam.fourcc, cam.frames_per_sec, cam._total_n_frames/ cam.frames_per_sec))

  # we use a drawer to show inferred position for each animal, display frames and save them as a video
  do_draw_frames = False
  if args.outp_video_filename is not None:
    do_draw_frames = True
  drawer = DefaultDrawer(args.outp_video_filename, draw_frames = do_draw_frames,
                         framesWinSizeX = dbgImgWinSizeX, framesWinSizeY = dbgImgWinSizeY)

  # We build our monitor
  #monitor = Monitor(cam, AdaptiveBGModel, rois)
  if args.single_roi_video_filename is not None:
    monitor = Monitor(cam, AdaptiveBGModel, rois,
                      dbg_roi_value=dbg_single_roi_number,
                      dbg_roi_video_filename=args.single_roi_video_filename)
  else:
    monitor = Monitor(cam, AdaptiveBGModel, rois)

  # Now everything is ready, we run the monitor with a result writer and a drawer
  logging.info("run monitor with drawer")
  with SQLiteResultWriter(args.db_filename, rois) as rw:
       monitor.run(rw, drawer)


if __name__ == "__main__":
    main(sys.argv)

