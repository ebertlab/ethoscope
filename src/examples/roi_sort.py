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

dbgImgWinSizeX = 1600
dbgImgWinSizeY = 1200

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
#cv2.namedWindow("ROIMask Centers", cv2.WINDOW_NORMAL)
#cv2.resizeWindow("ROIMask Centers", dbgImgWinSizeX, dbgImgWinSizeY)
#cv2.imshow("ROIMask Centers", image)
#cv2.waitKey(0)

class RoiSpace():
  def __init__(self, roi):
    """
    Class representing a region of interest(ROI) augmented by it's
    center of gravity (center point) and a two dimensional category numbering.
    """
    self._roi = roi;
    # compute the center of the contour
    M = cv2.moments(roi.polygon)
    self._cX = int(M["m10"] / M["m00"])
    self._cY = int(M["m01"] / M["m00"])
    self._xCategory = 0
    self._yCategory = 0
    
    
class RoiCenters():

  def __init__(self, rois):
    """
    Class representing a list of regions of interest(ROI) including their
    centers of gravity (center points):
    """
    self._rois = rois
    self._roiSpaces = []
    for r in self._rois:
      self._roiSpaces.append(RoiSpace(r))
    self._xSorted = sorted(self._roiSpaces, key=lambda a: a._cX)
    self._ySorted = sorted(self._roiSpaces, key=lambda a: a._cY)
    self._xCategoryCnt = 0
    self._yCategoryCnt = 0
      

  def printRoiCenters(self):
    for r in self._roiSpaces:
      print("Roi %d: (%d,%d)" % (r._roi.idx, r._cX, r._cY))
  
  def gridSort(self, xTolerance, yTolerance):
    """
    Tries to arrange the Rois into a rectangular grid and assign values to them
    to be able to sort them into the grid coordinates from left to right and top to down
    """
    _xCategory = -1
    _prevX = 0
    for r in self._xSorted:
      _xDistance = r._cX - _prevX
      if (_xDistance > xTolerance):
        _xCategory += 1
      r._xCategory = _xCategory
      _prevX = r._cX
    self._xCategoryCnt = _xCategory + 1

    _yCategory = -1
    _prevY = 0
    for r in self._ySorted:
      _yDistance = r._cY - _prevY
      if (_yDistance > yTolerance):
        _yCategory += 1
      r._yCategory = _yCategory
      _prevY = r._cY
    self._yCategoryCnt = _yCategory + 1

    for rs in self._roiSpaces:
      rs._roi._value = rs._yCategory * self._xCategoryCnt + rs._xCategory
#      print("Roi %d: (%d,%d), category: (%d,%d)" % (rs._roi.idx, rs._cX, rs._cY, rs._xCategory, rs._yCategory))

    _valueSorted =  sorted(self._roiSpaces, key=lambda a: a._roi._value)

    for vs in _valueSorted:
      print("Roi %d: (%d,%d), value: %d, category: (%d,%d)" % 
            (vs._roi.idx, vs._cX, vs._cY, vs._roi._value + 1, vs._xCategory, vs._yCategory))

    print("Categories X: %d, Y: %d" % (self._xCategoryCnt, self._yCategoryCnt))



roiCenters = RoiCenters(rois)
#roiCenters.printRoiCenters()
roiCenters.gridSort(50, 50)


