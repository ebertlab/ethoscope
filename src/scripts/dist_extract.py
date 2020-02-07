#!/usr/bin/env python3
"""
 This script extracts a table of the moved distance values of all ROIs for every sample times
 (movie frame times) out of the sqlite result database produced by ethoscope.
 The columns are sorted by the ROI value field, which is set in my version of ethoscope
 img_roi_builder.py to representing a left to right, top to down ordering of ROIs.
"""

__author__ = 'lukas'
import logging
import sqlite3
import sys
from argparse import ArgumentParser

def main(argv):

  parser = ArgumentParser(description='Extract a table of the moved distance values of all ROIs ' +
                                      'for every sample times (movie frame times) out of ' +
                                      'the sqlite result database produced by ethoscope.')
  parser.add_argument("-i", "--input-db", dest="db_filename",
                      help="Connect to Sqlite DB file DB_FILENAME.")

  args = parser.parse_args()

  #OUTPUT_DATA_DIR = "/home/lukas/tmp/ethoscope/"
  #OUTPUT_DB = OUTPUT_DATA_DIR + "results.db"
  #OUTPUT_DB = OUTPUT_DATA_DIR + "results20200205.db"

  conn = sqlite3.connect(args.db_filename)
  c = conn.cursor()

  # create a list of all rois sorted by their value field
  rois = []
  sql_rois = 'SELECT roi_idx,roi_value FROM ROI_MAP'
  c.execute(sql_rois)
  for row in c:
    rois.append((row))

  # sort by the roi_value field
  sorted(rois, key=lambda a: a[1])

  # query from ROI_1 a list of all sample times.
  sql = "SELECT GROUP_CONCAT(ROI_1.t) FROM ROI_1"
  c.execute(sql)
  sample_times = map(int, c.fetchone()[0].split(','))

  caption_str = 'time [ms]'
  for roi in rois:
    caption_str += (', %d' % roi[1])
  print(caption_str)

  # retrieve the "moved distance value" for every sample time and every roi
  #
  for t in sample_times:
    col_dist_of_rois = ("%s" % (t))
    for roi in rois:
      roi_tbl_name = ("ROI_%d" % roi[0])
      sql = ("SELECT t,xy_dist_log10x1000 FROM %s WHERE t = %d" % (roi_tbl_name, t))
      c.execute(sql)
      col_dist_of_rois += (", %d" % (c.fetchone()[1]))

    print(col_dist_of_rois)


  conn.close()

if __name__ == "__main__":
    main(sys.argv)

