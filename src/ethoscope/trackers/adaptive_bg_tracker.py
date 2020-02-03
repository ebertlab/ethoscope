
__author__ = 'quentin'

from collections import deque
from math import log10, sqrt, pi
import cv2

try:
    CV_VERSION = int(cv2.__version__.split(".")[0])
except:
    CV_VERSION = 2


import numpy as np
from scipy import ndimage
from ethoscope.core.variables import XPosVariable, YPosVariable, XYDistance, WidthVariable, HeightVariable, PhiVariable, Label
from ethoscope.core.data_point import DataPoint
from ethoscope.trackers.trackers import BaseTracker, NoPositionError

import logging


class ObjectModel(object):
    """
    A class to model, update and predict foreground object (i.e. tracked animal).
    """
    _sqrt_2_pi = sqrt(2.0 * pi)
    def __init__(self, history_length=1000):
        #fixme this should be time, not number of points!
        self._features_header = [
            "fg_model_area",
            "fg_model_height",
            #"fg_model_aspect_ratio",
            "fg_model_mean_grey"
        ]

        self._history_length = history_length
        self._ring_buff = np.zeros((self._history_length, len(self._features_header)), dtype=np.float32, order="F")
        self._std_buff = np.zeros((self._history_length, len(self._features_header)), dtype=np.float32, order="F")
        self._ring_buff_idx=0
        self._is_ready = False
        self._roi_img_buff = None
        self._mask_img_buff = None
        self._img_buff_shape = np.array([0,0])

        self._last_updated_time = 0
        # If the model is not updated for this duration, it is reset. Patches #39
        self._max_unupdated_duration = 1 *  60 * 1000.0 #ms

    @property
    def is_ready(self):
        return self._is_ready
    @property
    def features_header(self):
        return self._features_header


    def update(self, img, contour,time):
        self._last_updated_time = time
        self._ring_buff[self._ring_buff_idx] = self.compute_features(img,contour)

        self._ring_buff_idx += 1

        if self._ring_buff_idx == self._history_length:
            self._is_ready = True
            self._ring_buff_idx = 0


        return self._ring_buff[self._ring_buff_idx]

    def distance(self, features,time):
        if time - self._last_updated_time > self._max_unupdated_duration:
            logging.warning("FG model not updated for too long. Resetting.")
            self.__init__(self._history_length)
            return 0

        if not self._is_ready:
            last_row = self._ring_buff_idx + 1
        else:
            last_row = self._history_length

        means = np.mean(self._ring_buff[:last_row ], 0)

        np.subtract(self._ring_buff[:last_row], means, self._std_buff[:last_row])
        np.abs(self._std_buff[:last_row], self._std_buff[:last_row])

        stds = np.mean(self._std_buff[:last_row], 0)
        if (stds == 0).any():
            return 0

        a = 1 / (stds* self._sqrt_2_pi)

        b = np.exp(- (features - means) ** 2  / (2 * stds ** 2))

        likelihoods =  a * b

        if np.any(likelihoods==0):
            return 0
        #print features, means
        logls = np.sum(np.log10(likelihoods)) / len(likelihoods)
        return -1.0 * logls


    def compute_features(self, img, contour):
        x,y,w,h = cv2.boundingRect(contour)

        if self._roi_img_buff is None or np.any(self._roi_img_buff.shape < img.shape[0:2]) :
            # dynamically reallocate buffer if needed
            self._img_buff_shape[1] =  max(self._img_buff_shape[1],w)
            self._img_buff_shape[0] =  max(self._img_buff_shape[0], h)

            self._roi_img_buff = np.zeros(self._img_buff_shape, np.uint8)
            self._mask_img_buff = np.zeros_like(self._roi_img_buff)

        sub_mask = self._mask_img_buff[0 : h, 0 : w]

        sub_grey = self._roi_img_buff[ 0 : h, 0: w]

        cv2.cvtColor(img[y : y + h, x : x + w, :],cv2.COLOR_BGR2GRAY,sub_grey)
        sub_mask.fill(0)

        cv2.drawContours(sub_mask,[contour],-1, 255,-1,offset=(-x,-y))
        mean_col = cv2.mean(sub_grey, sub_mask)[0]


        (_,_) ,(width,height), angle  = cv2.minAreaRect(contour)
        width, height= max(width,height), min(width,height)
        ar = ((height+1) / (width+1))
        #todo speed should use time
        #
        # if len(self.positions) > 2:
        #
        #     pm, pmm = self._positions[-1],self._positions[-2]
        #     xm, xmm = pm["x"], pmm["x"]
        #     ym, ymm = pm["y"], pmm["y"]
        #
        #     instantaneous_speed = abs(xm + 1j*ym - xmm + 1j*ymm)
        # else:
        #     instantaneous_speed = 0
        # if np.isnan(instantaneous_speed):
        #     instantaneous_speed = 0

        features = np.array([log10(cv2.contourArea(contour) + 1.0),
                            height + 1,
                            #sqrt(ar),
                            #instantaneous_speed +1.0,
                            mean_col +1
                            # 1.0
                             ])

        return features


class BackgroundModel(object):
    """
    A class to model background. It uses a dynamic running average and support arbitrary and heterogeneous frame rates
    """
    def __init__(self, max_half_life=100. * 1000, min_half_life=1. * 1000, increment=1.2):
        # the maximal half life of a pixel from background, in seconds
        self._max_half_life = float(max_half_life)
        # the minimal one
        self._min_half_life = float(min_half_life)

        # starts with the fastest learning rate
        self._current_half_life = self._min_half_life

        # fixme theoritically this should depend on time, not frame index
        self._increment = increment
        # the mean background
        self._bg_mean = None
        # self._bg_sd = None

        self._buff_alpha_matrix = None
        self._buff_invert_alpha_mat = None
        # the time stamp of the frame last used to update
        self.last_t = 0

    @property
    def bg_img(self):
        return self._bg_mean

    def increase_learning_rate(self):
        self._current_half_life  /=  self._increment

    def decrease_learning_rate(self):
        self._current_half_life  *=  self._increment

    def update(self, img_t, t, fg_mask=None):
        dt = float(t - self.last_t)
        if dt < 0:
            # raise EthoscopeException("Negative time interval between two consecutive frames")
            raise NoPositionError("Negative time interval between two consecutive frames")

        # clip the half life to possible value:
        self._current_half_life = np.clip(self._current_half_life, self._min_half_life, self._max_half_life)

        # ensure preallocated buffers exist. otherwise, initialise them
        if self._bg_mean is None:
            self._bg_mean = img_t.astype(np.float32)
            # self._bg_sd = np.zeros_like(img_t)
            # self._bg_sd.fill(128)

        if self._buff_alpha_matrix is None:
            self._buff_alpha_matrix = np.ones_like(img_t,dtype = np.float32)

        # the learning rate, alpha, is an exponential function of half life
        # it correspond to how much the present frame should account for the background

        lam =  np.log(2) / self._current_half_life
        # how much the current frame should be accounted for
        alpha = 1 - np.exp(-lam * dt)

        # set-p a matrix of learning rate. it is 0 where foreground map is true
        self._buff_alpha_matrix.fill(alpha)
        if fg_mask is not None:
            cv2.dilate(fg_mask,None,fg_mask)
            cv2.subtract(self._buff_alpha_matrix, self._buff_alpha_matrix, self._buff_alpha_matrix, mask=fg_mask)

        if self._buff_invert_alpha_mat is None:
            self._buff_invert_alpha_mat = 1 - self._buff_alpha_matrix
        else:
            np.subtract(1, self._buff_alpha_matrix, self._buff_invert_alpha_mat)

        np.multiply(self._buff_alpha_matrix, img_t, self._buff_alpha_matrix)
        np.multiply(self._buff_invert_alpha_mat, self._bg_mean, self._buff_invert_alpha_mat)
        np.add(self._buff_alpha_matrix, self._buff_invert_alpha_mat, self._bg_mean)

        self.last_t = t


class AdaptiveBGModel(BaseTracker):
    _description = {"overview": "The default tracker for fruit flies. One animal per ROI.",
                    "arguments": []}

    fg_model = ObjectModel()

    # L.Zi.: propagate *args, **kwargs, don't know what 'data' is for.
    #def __init__(self, roi, data=None):
    def __init__(self, roi, *args, **kwargs):
        """
        An adaptive background subtraction model to find position of one animal in one roi.

        TODO more description here
        :param roi:
        :param data:
        :return:
        """
        data = None
        self._previous_shape=None
        self._object_expected_size = 0.035 # proportion of the roi main axis
        self._max_area = (5 * self._object_expected_size) ** 2

        self._smooth_mode = deque()
        self._smooth_mode_tstamp = deque()
        self._smooth_mode_window_dt = 30 * 1000 #miliseconds


        self._bg_model = BackgroundModel()
        self._max_m_log_lik = 6.
        self._buff_grey = None
        self._buff_object = None
        self._buff_object_old = None
        self._buff_grey_blurred = None
        self._buff_fg = None
        self._buff_convolved_mask = None
        self._buff_fg_backup = None
        self._buff_fg_diff = None
        self._old_sum_fg = 0

        # L. Zi.: video writer to produce optional single roi processing debug video
        self._dbg_roi_video_writer = None
        self._dbg_single_roi_value = -1
        self._dbg_single_roi_do_rec = False
        self._dbg_single_roi_video_filename = None
        if ("dbg_roi_value" in kwargs
            and "dbg_roi_video_filename" in kwargs
            and len(kwargs["dbg_roi_video_filename"]) > 0):
          for a in kwargs:
             if a == "dbg_roi_value":
               self._dbg_single_roi_value = kwargs["dbg_roi_value"]
               self._dbg_single_roi_do_rec = True
             if a == "dbg_roi_video_filename":
               self._dbg_single_roi_video_filename = kwargs["dbg_roi_video_filename"]

        super(AdaptiveBGModel, self).__init__(roi, data)

    def __del__(self):
        # L. Zi.: for closing video output file when doing single roi processing debug video
        #if self._dbg_roi_video_writer is not None:
        #    self._dbg_roi_video_writer.release()
        pass

    def enable_single_roi_debugging(self, roi_value, video_filename):
        self._dbg_single_roi_value = roi_value
        self._dbg_single_roi_video_filename = video_filename
        self._dbg_single_roi_do_rec = True
        
    def disable_single_roi_debugging(self, roi_value, video_filename):
        self._dbg_single_roi_do_rec = False

    def _pre_process_input_minimal(self, img, mask, t, darker_fg=True):
        blur_rad = int(self._object_expected_size * np.max(img.shape) / 2.0)

        if blur_rad % 2 == 0:
            blur_rad += 1

        if self._buff_grey is None:
            self._buff_grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            if mask is None:
                mask = np.ones_like(self._buff_grey) * 255

        cv2.cvtColor(img, cv2.COLOR_BGR2GRAY, self._buff_grey)
        
        cv2.GaussianBlur(self._buff_grey,(blur_rad,blur_rad),1.2, self._buff_grey)
        if darker_fg:
            cv2.subtract(255, self._buff_grey, self._buff_grey)

        mean = cv2.mean(self._buff_grey, mask)

        scale = 128. / mean[0]

        logging.debug("_pre_process_input_minimal: cv2.multiply(%s, %s)" % (self._buff_grey, scale))
        cv2.multiply(self._buff_grey, scale, dst = self._buff_grey)


        if mask is not None:
            cv2.bitwise_and(self._buff_grey, mask, self._buff_grey)
            return self._buff_grey

    def _pre_process_input(self, img, mask, t):

        blur_rad = int(self._object_expected_size * np.max(img.shape) * 2.0)
        if blur_rad % 2 == 0:
            blur_rad += 1


        if self._buff_grey is None:
            self._buff_grey = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            self._buff_grey_blurred = np.empty_like(self._buff_grey)
            # self._buff_grey_blurred = np.empty_like(self._buff_grey)
            if mask is None:
                mask = np.ones_like(self._buff_grey) * 255

            mask_conv = cv2.blur(mask,(blur_rad, blur_rad))

            self._buff_convolved_mask  = (1/255.0 *  mask_conv.astype(np.float32))


        cv2.cvtColor(img,cv2.COLOR_BGR2GRAY, self._buff_grey)

        hist = cv2.calcHist([self._buff_grey], [0], None, [256], [0,255]).ravel()
        hist = np.convolve(hist, [1] * 3)
        mode =  np.argmax(hist)

        self._smooth_mode.append(mode)
        self._smooth_mode_tstamp.append(t)

        if len(self._smooth_mode_tstamp) >2 and self._smooth_mode_tstamp[-1] - self._smooth_mode_tstamp[0] > self._smooth_mode_window_dt:
            self._smooth_mode.popleft()
            self._smooth_mode_tstamp.popleft()


        mode = np.mean(list(self._smooth_mode))
        scale = 128. / mode

        # cv2.GaussianBlur(self._buff_grey,(5,5), 1.5,self._buff_grey)

        cv2.multiply(self._buff_grey, scale, dst = self._buff_grey)


        cv2.bitwise_and(self._buff_grey, mask, self._buff_grey)

        cv2.blur(self._buff_grey,(blur_rad, blur_rad), self._buff_grey_blurred)
        #fixme could be optimised
        self._buff_grey_blurred = (self._buff_grey_blurred / self._buff_convolved_mask).astype(np.uint8)


        cv2.absdiff(self._buff_grey, self._buff_grey_blurred, self._buff_grey)

        if mask is not None:
            cv2.bitwise_and(self._buff_grey, mask, self._buff_grey)
            return self._buff_grey


    def _find_position(self, img, mask, t):

        grey = self._pre_process_input_minimal(img, mask, t)
        # grey = self._pre_process_input(img, mask, t)
        if logging.getLogger().isEnabledFor(logging.DEBUG) and self._roi._value == 67:
          cv2.namedWindow("PreProc", cv2.WINDOW_NORMAL)
          cv2.resizeWindow("PreProc", 800, 600)
          cv2.imshow("PreProc", grey)
          cv2.waitKey(0)

        try:
            return self._track(img, grey, mask, t)
        except NoPositionError:
            self._bg_model.update(grey, t)
            raise NoPositionError


    def _track(self, img, grey, mask, t):

        if self._bg_model.bg_img is None:
            self._buff_fg = np.empty_like(grey)
            self._buff_object= np.empty_like(grey)
            self._buff_fg_backup = np.empty_like(grey)
  #          self._buff_fg_diff = np.empty_like(grey)
            self._old_pos = 0.0 +0.0j
   #         self._old_sum_fg = 0
            raise NoPositionError

        bg = self._bg_model.bg_img.astype(np.uint8)

        cv2.subtract(grey, bg, self._buff_fg)

        cv2.threshold(self._buff_fg, 20, 255, cv2.THRESH_TOZERO, dst=self._buff_fg)

        # L.Zi. make a copy of extracted foreground to illustrate detection for debugging
        fg_cpy = np.copy(self._buff_fg)

        # cv2.bitwise_and(self._buff_fg_backup,self._buff_fg,dst=self._buff_fg_diff)
        # sum_fg = cv2.countNonZero(self._buff_fg)

        self._buff_fg_backup = np.copy(self._buff_fg)

        n_fg_pix = np.count_nonzero(self._buff_fg)
        prop_fg_pix  = n_fg_pix / (1.0 * grey.shape[0] * grey.shape[1])
        is_ambiguous = False

        if  prop_fg_pix > self._max_area:
            self._bg_model.increase_learning_rate()
            raise NoPositionError

        if  prop_fg_pix == 0:
            self._bg_model.increase_learning_rate()
            raise NoPositionError

        if CV_VERSION == 3:
            _, contours, hierarchy = cv2.findContours(self._buff_fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        else:
            contours, hierarchy = cv2.findContours(self._buff_fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        contours = [cv2.approxPolyDP(c,1.2,True) for c in contours]

        if len(contours) == 0:
            self._bg_model.increase_learning_rate()
            raise NoPositionError

        elif len(contours) > 1:
            if not self.fg_model.is_ready:
                raise NoPositionError
            # hulls = [cv2.convexHull( c) for c in contours]
            hulls = contours
            #hulls = merge_blobs(hulls)

            hulls = [h for h in hulls if h.shape[0] >= 3]

            if len(hulls) < 1:
                raise NoPositionError

            elif len(hulls) > 1:
                is_ambiguous = True
            cluster_features = [self.fg_model.compute_features(img, h) for h in hulls]
            all_distances = [self.fg_model.distance(cf,t) for cf in cluster_features]
            good_clust = np.argmin(all_distances)

            hull = hulls[good_clust]
            distance = all_distances[good_clust]
        else:
            hull = contours[0]
            if hull.shape[0] < 3:
                self._bg_model.increase_learning_rate()
                raise NoPositionError

            features = self.fg_model.compute_features(img, hull)
            distance = self.fg_model.distance(features,t)

        if distance > self._max_m_log_lik:
            self._bg_model.increase_learning_rate()
            raise NoPositionError


        (x, y), (w, h), angle  = cv2.minAreaRect(hull)

        if w < h:
            angle -= 90
            w, h = h, w
        angle = angle % 180

        h_im = min(grey.shape)
        w_im = max(grey.shape)
        max_h = 2 * h_im
        if w > max_h or h > max_h:
            raise NoPositionError

        #todo center mass just on the ellipse area
        cv2.bitwise_and(self._buff_fg_backup, self._buff_fg, self._buff_fg_backup)

        y,x = ndimage.measurements.center_of_mass(self._buff_fg_backup)

        pos = x + 1.0j * y

        # L. Zi.: 
        #pos /= w_im

        #xy_dist = round(log10(1./float(w_im) + abs(pos - self._old_pos))*1000)
        # L. Zi.: want linear motion distance
        xy_dist = round(abs(pos - self._old_pos))

        # cv2.bitwise_and(self._buff_fg_diff,self._buff_fg,dst=self._buff_fg_diff)
        # sum_diff = cv2.countNonZero(self._buff_fg_diff)
        # xor_dist = (sum_fg  + self._old_sum_fg - 2*sum_diff)  / float(sum_fg  + self._old_sum_fg)
        # xor_dist *=1000.
        # self._old_sum_fg = sum_fg
        self._old_pos = pos


        if mask is not None:
            cv2.bitwise_and(self._buff_fg, mask, self._buff_fg)

        if is_ambiguous:
            self._bg_model.increase_learning_rate()
            self._bg_model.update(grey, t)
        else:
            self._bg_model.decrease_learning_rate()
            self._bg_model.update(grey, t, self._buff_fg)

        self.fg_model.update(img, hull,t)

        x_var = XPosVariable(int(round(x)))
        y_var = YPosVariable(int(round(y)))
        distance = XYDistance(int(xy_dist))
        #xor_dist = XorDistance(int(xor_dist))
        w_var = WidthVariable(int(round(w)))
        h_var = HeightVariable(int(round(h)))
        phi_var = PhiVariable(int(round(angle)))
        # mlogl =   mLogLik(int(distance*1000))

        # L. Zi.: produce and show adaptive background processing results
        if self._dbg_single_roi_do_rec:
          if self._roi._value == self._dbg_single_roi_value:
            animal_colour = (255, 255, 255)
            cv2.ellipse(fg_cpy, ((x, y), (int(w * 1.5), int(h * 1.5)), angle), animal_colour, 1, cv2.LINE_AA)
            grey_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            h = round(self._roi.rectangle[3])
            w = round(self._roi.rectangle[2])
            # draw roi value
            cv2.putText(fg_cpy, str(self._roi._value), (5, h - 10),
                            cv2.FONT_HERSHEY_DUPLEX, 1, (255,255,255))
            # draw motion distance of detected animal since last frame
            cv2.putText(fg_cpy, str(int(xy_dist)), (5, 25),      
                            cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255))
            txt = str(int(t))
            (txt_w, txt_h), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_DUPLEX, 1, 1)
            cv2.putText(fg_cpy, txt, (w - txt_w - 5, 25),
                            cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255))
            vis = np.concatenate((grey_img, bg, fg_cpy), axis=1)
            #vis = np.concatenate((grey_img, grey, fg_cpy), axis=1)
            cv2.namedWindow("Processing", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Processing", 1800, 600)
            cv2.imshow("Processing", vis)
            cv2.waitKey(100)
            # record a video
            if self._dbg_roi_video_writer is None:
                fourcc_string = 'DIVX'
                fourcc = cv2.VideoWriter_fourcc(*fourcc_string)
                self._dbg_roi_video_writer = cv2.VideoWriter(self._dbg_single_roi_video_filename,
                                                             fourcc,
                                                             2.0, (vis.shape[1], vis.shape[0]),
                                                             isColor=False)
            self._dbg_roi_video_writer.write(vis)


        out = DataPoint([x_var, y_var, w_var, h_var,
                         phi_var,
                         #mlogl,
                         distance,
                         #xor_dist
                        #Label(0)
                         ])


        self._previous_shape=np.copy(hull)
        return [out]
