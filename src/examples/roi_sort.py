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

ROI_IMAGE = INPUT_DATA_DIR + "irbacklit_20200109_1525_4x4x6_squaremask_valued.png"

logfile = OUTPUT_DATA_DIR + 'roi_sort.log'

# setup logging
logging.basicConfig(filename=logfile, level=logging.INFO)

# Make the ethoscope packages accessible
package_path = os.path.join(os.path.dirname(sys.path[0]), '')
logging.info("path of ethoscope package: %s" % package_path)
sys.path.insert(0, package_path)

import cv2

# import the bricks from ethoscope package
# Use a mask image to define rois. Mask image must have black background, every non-black
# region defines a roi.
from ethoscope.roi_builders.img_roi_builder import ImgMaskROIBuilder

# Generate ROIs from the mask image
logging.info("reading roi mask")
roi_builder = ImgMaskROIBuilder(ROI_IMAGE)

logging.info("building rois")
rois = roi_builder.build(None)  # use image already loaded by ImgMaskROIBuilder instance

image = np.zeros_like(roi_builder._mask);
#image = np.full_like(roi_builder._mask, 255);


#print("Rois: ");
for r in rois:
  # compute the center of the contour
  M = cv2.moments(r.polygon)
  cX = int(M["m10"] / M["m00"])
  cY = int(M["m01"] / M["m00"])

  # draw the contour and center of the shape on the image
  cv2.drawContours(image, [r.polygon], -1, (255, 255, 255), 2)
  cv2.circle(image, (cX, cY), 7, (255, 255, 255), -1)
  cv2.putText(image, "center", (cX - 20, cY - 20),
  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

  #print(r.polygon)

print("Found %d rois" % len(rois))
# show the image
cv2.namedWindow("ROIMask Centers", cv2.WINDOW_NORMAL)
cv2.resizeWindow("ROIMask Centers", 800, 600)
cv2.imshow("ROIMask Centers", image)
cv2.waitKey(0)

class RoiSpace():
  def __init__(self, roi):
    """
    Class representing a region of interest(ROI) augmented by it's
    center of gravity (center point):
    """
    self._roi = roi;
    # compute the center of the contour
    M = cv2.moments(roi.polygon)
    self._cX = int(M["m10"] / M["m00"])
    self._cY = int(M["m01"] / M["m00"])
    
    
class RoiCenters():

  def __init__(self, rois):
    """
    Class representing a list of regions of interest(ROI) including their
    centers of gravity (center points):
    """
    self._rois = rois
    self._roiSpaces = []
    self._localMaximaX = []
    for r in self._rois:
      self._roiSpaces.append(RoiSpace(r))
      

  def printRoiCenters(self):
    for r in self._roiSpaces:
      print("Roi %d: (%d,%d)" % (r._roi.idx, r._cX, r._cY))
  

roiCenters = RoiCenters(rois)
roiCenters.printRoiCenters()


