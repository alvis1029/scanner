#!/usr/bin/env python2

import rospy
import std_msgs.msg
import detection_msgs.msg
from std_msgs.msg import Float64, Int8

import numpy as np
from matplotlib import cm
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class SetMaxSpeed:
    def __init__(self, max_speed_pub, det_pub):
        self.max_speed_pub = max_speed_pub
        self.det_pub = det_pub

    def symmetric_gaussian(self, pos, mu, Sigma):
        """Return the multivariate Gaussian distribution on array pos."""

        n = mu.shape[0]
        Sigma_det = np.linalg.det(Sigma)
        Sigma_inv = np.linalg.inv(Sigma)
        N = np.sqrt((2*np.pi)**n * Sigma_det)
        # This einsum call calculates (x-mu)T.Sigma-1.(x-mu) in a vectorized
        # way across all the input variables.
        fac = np.einsum('...k,kl,...l->...', pos-mu, Sigma_inv, pos-mu)

        return np.exp(-fac / 2) / N

    def social_speed(self, dx, dy, MAX_SPEED):
        x = np.arange(-3, 3, 0.1)
        y = np.arange(-3, 3, 0.1)
        X, Y = np.meshgrid(x, y)

        # Mean vector and covariance matrix
        mu = np.array([0.0, 0.0])
        Sigma = np.array([[ 0.5, 0.0 ], [ 0.0, 0.5 ]])

        # Pack X and Y into a single 3-dimensional array
        pos = np.empty(X.shape + (2,))
        pos[:, :, 0] = X
        pos[:, :, 1] = Y

        # The distribution on the variables X, Y packed into pos.
        Z = self.symmetric_gaussian(pos, mu, Sigma)

        # fig = plt.figure()
        # ax = fig.gca(projection='3d')
        # ax.plot_surface(X, Y, Z, rstride=3, cstride=3, linewidth=1, antialiased=True, cmap=cm.viridis)
        # plt.contour(X, Y, Z)
        # plt.show()

        final_max_speed = (1.0 - Z[29+dx, 29+dy] / Z[29, 29]) * MAX_SPEED
        # rospy.logwarn("modify velocity to %lf", final_max_speed)
        self.max_speed_pub.publish(final_max_speed)

    def get_distance_callback(self, msg):
        min = 100000.0
        target = -1

        for i in range(len(msg.dets_list)):
            if (msg.dets_list[i].x * msg.dets_list[i].x + msg.dets_list[i].y * msg.dets_list[i].y)  < min:
                min = msg.dets_list[i].x * msg.dets_list[i].x + msg.dets_list[i].y * msg.dets_list[i].y
                target = i
        # rospy.logwarn("Distance is %lf", np.sqrt(msg.dets_list[target].x * msg.dets_list[target].x + msg.dets_list[target].y * msg.dets_list[target].y))
        if target != -1 :
            self.social_speed(int(msg.dets_list[target].x/0.2), int(msg.dets_list[target].y/0.2), 0.4)
        else :
            self.social_speed(30, 30, 0.4)

        self.det_pub.publish(len(msg.dets_list))

def main():
    rospy.init_node("Setting_Max_Speed")
    max_speed_pub = rospy.Publisher("/navigation_controller/max_speed", Float64, queue_size=10)
    det_pub = rospy.Publisher("/people/num", Int8, queue_size=10)
    modifier = SetMaxSpeed(max_speed_pub, det_pub)
    sub = rospy.Subscriber("/det3d_result", detection_msgs.msg.Det3DArray, modifier.get_distance_callback)
    rospy.spin()

if __name__ == '__main__':
    main()
    