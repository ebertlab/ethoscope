#!/bin/bash
#
# Example command to extract a still image from a video using ffmpeg.
# Extract a single frame (-vframes 1) from the input file (-i <infile>) using a sequence
# starting at 0.5s from beginning (-ss 0.5) with a duration of 1s (-t 1)
# and write it to output file in the image format "image2" (-f image2).
# 
ffmpeg -ss 0.5 -i Basler_acA5472-17um__23065142__20200109_152536071.mp4 -t 1 -vframes 1 -f image2 irbacklit_20200109_1525.jpg


# Another example command to crop out partial area of a video.
# ffmpeg -i in.mp4 -filter:v "crop=out_w:out_h:x:y" out.mp4
#
# Where the options are as follows:
#    out_w is the width of the output rectangle
#    out_h is the height of the output rectangle
#    x and y specify the top left corner of the output rectangle

ffmpeg -i Basler_acA5472-17um__23065142__20200109_152536071.mp4 -filter:v "crop=766:415:2716:1826" Basler_acA5472-17um__23065142__20200109_152536071_cropped.mp4

