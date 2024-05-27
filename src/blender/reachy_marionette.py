from enum import Enum
import mathutils
import numpy as np
import functools
import threading

import bpy
from reachy_sdk import ReachySDK
from reachy_sdk.reachy_sdk import flush_communication
from reachy_sdk.trajectory import goto
from reachy_sdk.trajectory.interpolation import InterpolationMode


class State(Enum):
    IDLE = 1
    STREAMING = 2
    ANIMATING = 3


class ReachyMarionette():

    def __init__(self):

        self.reachy = None
        self.state = State.IDLE
        self.threads = []

        self.stream_interval = 2.0

    def __del__(self):
        self.stream_angles_disable()

        for thread in self.threads:
            thread.join()

    def set_state_idle(self):
        self.state == State.IDLE

    # Helper functions from rigify plugin

    def get_pose_matrix_in_other_space(self, mat, pose_bone):
        """ Returns the transform matrix relative to pose_bone's current
        transform space. In other words, presuming that mat is in
        armature space, slapping the returned matrix onto pose_bone
        should give it the armature-space transforms of mat.
        TODO: try to handle cases with axis-scaled parents better.
        """
        rest = pose_bone.bone.matrix_local.copy()
        rest_inv = rest.inverted()

        if pose_bone.parent.name != "Root":
            par_mat = pose_bone.parent.matrix.copy()
            par_inv = par_mat.inverted()
            par_rest = pose_bone.parent.bone.matrix_local.copy()
        else:
            par_mat = mathutils.Matrix()
            par_inv = mathutils.Matrix()
            par_rest = mathutils.Matrix()

        # Get matrix in bone's current transform space
        smat = rest_inv @ (par_rest @ (par_inv @ mat))

        return smat

    def get_bones_rotation(self, pose_bone, axis):

        mat = self.get_pose_matrix_in_other_space(pose_bone.matrix, pose_bone)

        if axis == 0:
            return mat.to_euler().x
        elif axis == 1:
            return mat.to_euler().y
        elif axis == 2:
            return mat.to_euler().z

    def angle_of_bone(self, name):

        bone = bpy.context.object.pose.bones[name]
        # Get unconstrained axis
        axis_rot = (np.array(bone.lock_rotation) == False).nonzero()[0][0]

        return np.rad2deg(self.get_bones_rotation(bone, axis_rot))

    def connect_reachy(self, report_function, ip='localhost'):

        if self.reachy != None:
            report_function(
                {'INFO'}, "Connection already established at '%s'" % ip)
            return

        # Try connection
        try:
            self.reachy = ReachySDK(host=ip)
            self.reachy.turn_on('reachy')
            report_function({'INFO'}, "Connection established succesfully!")

        except:
            report_function(
                {'ERROR'}, ("Could not find connection at '%s'" % ip))

    def disconnect_reachy(self, report_function):

        # Try connection
        if self.reachy != None:
            self.reachy_reset_pose()
            # self.reachy.turn_off_smoothly('reachy')
            # flush_communication()
            report_function({'WARNING'}, "Proper disconnection disabled!")
            self.reachy = None
            report_function({'INFO'}, "Disconnected Reachy")

        else:
            report_function({'INFO'}, "No Reachy is connected")

    def send_angles(self, report_function):

        if self.reachy == None:
            report_function({'ERROR'}, "Reachy not connected!")
            return

        if bpy.context.object.type != 'ARMATURE':
            report_function({'ERROR'}, "Please select Armature")
            return

        joint_angle_positions = {
            # Right arm
            self.reachy.r_arm.r_shoulder_pitch: self.angle_of_bone("shoulder_pitch.R"),
            self.reachy.r_arm.r_shoulder_roll: self.angle_of_bone("shoulder_roll.R"),
            self.reachy.r_arm.r_arm_yaw: self.angle_of_bone("shoulder_yaw.R"),
            self.reachy.r_arm.r_elbow_pitch: self.angle_of_bone("elbow_pitch.R"),
            self.reachy.r_arm.r_forearm_yaw: self.angle_of_bone("forearm_yaw.R"),
            self.reachy.r_arm.r_wrist_pitch: self.angle_of_bone("wrist_pitch.R"),
            self.reachy.r_arm.r_wrist_roll: self.angle_of_bone("wrist_roll.R"),
            self.reachy.r_arm.r_gripper: self.angle_of_bone("gripper.R"),
            # Left arm
            self.reachy.l_arm.l_shoulder_pitch: self.angle_of_bone("shoulder_pitch.L"),
            self.reachy.l_arm.l_shoulder_roll: self.angle_of_bone("shoulder_roll.L"),
            self.reachy.l_arm.l_arm_yaw: self.angle_of_bone("shoulder_yaw.L"),
            self.reachy.l_arm.l_elbow_pitch: self.angle_of_bone("elbow_pitch.L"),
            self.reachy.l_arm.l_forearm_yaw: self.angle_of_bone("forearm_yaw.L"),
            self.reachy.l_arm.l_wrist_pitch: self.angle_of_bone("wrist_pitch.L"),
            self.reachy.l_arm.l_wrist_roll: self.angle_of_bone("wrist_roll.L"),
            self.reachy.l_arm.l_gripper: self.angle_of_bone("gripper.L"),
        }

        # Duration is faster than the interval, to finish before the next thread
        thread = threading.Thread(
            target=self.reachy_goto, args=[joint_angle_positions, self.stream_interval * 0.5])
        self.threads.append(thread)
        thread.start()

    def reachy_goto(self, joint_angles, duration=1.0):

        goto(
            goal_positions=joint_angles,
            duration=duration,
            interpolation_mode=InterpolationMode.MINIMUM_JERK
        )

    def stream_angles(self, report_function):
            self.send_angles(report_function)
        if self.state == State.STREAMING:
            return self.stream_interval  # Seconds till next function call
        else:
            return None

    def stream_angles_enable(self, report_function):

        if not self.state == State.STREAMING:
            self.state = State.STREAMING

            # Create Blender timer
            bpy.app.timers.register(functools.partial(
                self.stream_angles, report_function))

        else:
            report_function({'INFO'}, "Streaming is already on progress")


    def reachy_reset_pose(self):
        joint_angle_positions = {
            # Right arm
            self.reachy.r_arm.r_shoulder_pitch: 0,
            self.reachy.r_arm.r_shoulder_roll: 0,
            self.reachy.r_arm.r_arm_yaw: 0,
            self.reachy.r_arm.r_elbow_pitch: 0,
            self.reachy.r_arm.r_forearm_yaw: 0,
            self.reachy.r_arm.r_wrist_pitch: 0,
            self.reachy.r_arm.r_wrist_roll: 0,
            self.reachy.r_arm.r_gripper: 0,
            # Left arm
            self.reachy.l_arm.l_shoulder_pitch: 0,
            self.reachy.l_arm.l_shoulder_roll: 0,
            self.reachy.l_arm.l_arm_yaw: 0,
            self.reachy.l_arm.l_elbow_pitch: 0,
            self.reachy.l_arm.l_forearm_yaw: 0,
            self.reachy.l_arm.l_wrist_pitch: 0,
            self.reachy.l_arm.l_wrist_roll: 0,
            self.reachy.l_arm.l_gripper: 0
        }

        goto(
            goal_positions=joint_angle_positions,
            duration=1.0,
            interpolation_mode=InterpolationMode.MINIMUM_JERK
        )
