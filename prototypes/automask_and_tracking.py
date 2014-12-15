__author__ = 'quentin'


from pysolovideo.tracking.roi_builders import SleepDepROIBuilder
from pysolovideo.tracking.cameras import MovieVirtualCamera
from pysolovideo.tracking.monitor import Monitor

from pysolovideo.tracking.trackers import AdaptiveBGModel
from pysolovideo.tracking.interactors import SystemPlaySoundOnStop
from pysolovideo.tracking.interactors import SleepDepInteractor
from pysolovideo.hardware_control.arduino_api import SleepDepriverInterface





cam = MovieVirtualCamera("/stk/pysolo_video_samples/motion_in_dark_one_tube_at_a_time.avi")
#cam = MovieVirtualCamera("/stk/pysolo_video_samples/long_realistic_recording_with_motion.avi")
#cam = MovieVirtualCamera("/stk/pysolo_video_samples/long_realistic_recording.avi")
# sdi = SleepDepriverInterface()
roi_builder = SleepDepROIBuilder()
rois = roi_builder(cam)

inters = [SystemPlaySoundOnStop(500 + i * 30) for i in range(len(rois))]
# inters = [SleepDepInteractor(i, sdi) for i in range(len(rois))]





monit = Monitor(cam, AdaptiveBGModel, rois, interactors= inters, draw_results=True)
monit.run()

#