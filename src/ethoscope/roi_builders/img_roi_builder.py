import cv2

try:
    CV_VERSION = int(cv2.__version__.split(".")[0])
except:
    CV_VERSION = 2

try:
    from cv2 import CV_LOAD_IMAGE_GRAYSCALE as IMG_READ_FLAG_GREY
    from cv import CV_RETR_EXTERNAL as RETR_EXTERNAL
    from cv import CV_CHAIN_APPROX_SIMPLE as CHAIN_APPROX_SIMPLE
except ImportError:
    from cv2 import IMREAD_GRAYSCALE as IMG_READ_FLAG_GREY
    from cv2 import RETR_EXTERNAL, CHAIN_APPROX_SIMPLE

import os
import logging
import numpy as np
from ethoscope.utils.debug import EthoscopeException
from ethoscope.roi_builders.roi_builders import BaseROIBuilder
from ethoscope.core.roi import ROI


class RoiWithGridBin():
  """
  Helper class to add a grid bin categories in two dimensions to rois
  """
  def __init__(self, roi):
    """
    Class representing a list of regions of interest(ROI) including their
    centers of gravity (center points):
    """
    self._roi = roi
    self._xCategory = 0
    self._yCategory = 0


class ImgMaskROIBuilder(BaseROIBuilder):

  def __init__(self, mask_path):
    """
    Class to build rois from greyscale image file.
    Each continuous region is used as a ROI.
    The greyscale value inside the ROI determines it's value.

    IMAGE HERE

    """

    if not os.path.exists(mask_path):
      raise EthoscopeException("'%s' does not exist. No such file" % mask_path)
    self._mask = cv2.imread(mask_path, IMG_READ_FLAG_GREY)
    self._rois = []
    self._rois_bounding_box = None

    super(ImgMaskROIBuilder,self).__init__()


  def _rois_from_img(self, img):
    # transform to gray scale image if not already
    if len(self._mask.shape) == 3:
      self._mask = cv2.cvtColor(self._mask, cv2.COLOR_BGR2GRAY)

    thresh_mask = self._mask.copy()
    #cv2.namedWindow("ROIMask Copy", cv2.WINDOW_NORMAL)
    #cv2.resizeWindow("ROIMask Copy", 800, 600)
    #cv2.imshow("ROIMask Copy", thresh_mask)
    #cv2.waitKey(0)

    # set threshold for findContours(): everthing not black (0) is over threshold
    ret, thresh_mask = cv2.threshold(thresh_mask, 5, 255, cv2.THRESH_BINARY)
    if CV_VERSION == 3:
      # OpenCV version 3 findContours() does not modify input image
      _, contours, _ = cv2.findContours(thresh_mask, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)
    else:
      contours, _ = cv2.findContours(thresh_mask, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)

    contour_cnt = len(contours)
    #logging.info("ImgMaskROIBuilder: found %s contours" % contour_cnt)
    tmp_mask = np.zeros_like(self._mask)
    for i, c in enumerate(contours):
      #logging.info("ROI Contour %s: %s", i, c);
      if len(c) >= 3:
        # skip contours with less than 3 elements
        cv2.drawContours(tmp_mask, [c], -1, 255)

        value = int(np.median(self._mask[tmp_mask > 0]))
        #print("ROI %s value: %s" % (i, value))
        #if (value == 255):
        #  value = None
        self._rois.append(ROI(c, i + 1, value))

    logging.info("ImgMaskROIBuilder: %s valid contours" % len(self._rois))
    if logging.getLogger().isEnabledFor(logging.DEBUG):
      cv2.namedWindow("ROIMask", cv2.WINDOW_NORMAL)
      cv2.resizeWindow("ROIMask", 800, 600)
      cv2.imshow("ROIMask", tmp_mask)
      cv2.waitKey(0)

    return self._rois

  def gridSort(self, xTolerance, yTolerance):
    """
    Tries to arrange the Rois into a rectangular grid and assign values to them
    to be able to sort them into the grid coordinates from left to right and top to down
    """
    self._xTolerance = xTolerance
    self._yTolerance = yTolerance
    binnedRois = []
    for r in self._rois:
      binnedRois.append(RoiWithGridBin(r))

    xSorted = sorted(binnedRois, key=lambda a: a._roi._rectangle[0])
    ySorted = sorted(binnedRois, key=lambda a: a._roi._rectangle[1])
    self._xCategoryCnt = 0
    self._yCategoryCnt = 0

    xCategory = -1
    prevX = 0
    for r in xSorted:
      xDistance = r._roi._rectangle[0] - prevX
      if (xDistance > xTolerance):
        xCategory += 1
      r._xCategory = xCategory
      prevX = r._roi._rectangle[0]
    self._xCategoryCnt = xCategory + 1

    yCategory = -1
    prevY = 0
    for r in ySorted:
      yDistance = r._roi._rectangle[1] - prevY
      if (yDistance > yTolerance):
        yCategory += 1
      r._yCategory = yCategory
      prevY = r._roi._rectangle[1]
    self._yCategoryCnt = yCategory + 1

    for rs in binnedRois:
      rs._roi._value = rs._yCategory * self._xCategoryCnt + rs._xCategory
#      print("Roi %d: (%d,%d), category: (%d,%d)" % (rs._roi.idx, rs._cX, rs._cY, rs._xCategory, rs._yCategory))

    sortedRois = sorted(binnedRois, key=lambda a: a._roi._value)
    self._rois = []
    for sr in sortedRois:
      self._rois.append(sr._roi)

    return self._rois


