from enum import Enum
import functools
import mathutils
import numpy as np
import socket
import threading

import bpy
from reachy_sdk import ReachySDK
from reachy_sdk.reachy_sdk import flush_communication
from reachy_sdk.trajectory import goto
from reachy_sdk.trajectory.interpolation import InterpolationMode


class State(Enum):
    IDLE = 0
    STREAMING = 1
    ANIMATING = 2


class ReachyMarionette:

    def __init__(self):

        self.reachy = None
        self.state = State.IDLE
        self.threads = []

        self.stream_interval = 2.0

    def __del__(self):
        self.set_state_idle()

        for thread in self.threads:
            thread.join()

    def set_state_idle(self):
        self.state = State.IDLE

    # Helper functions from rigify plugin

    def get_pose_matrix_in_other_space(self, mat, pose_bone):
        """Returns the transform matrix relative to pose_bone's current
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

    def ensure_connection(self, report_blender, ip="localhost", timeout=0.1):

        port = 50055  # Reachy's sdk_port, only open when robot is connected

        try:
            with socket.create_connection((ip, port), timeout):
                return True
        except OSError:
            report_blender(
                {"WARNING"},
                "Reachy connection not available",
            )

            if self.reachy != None:
                report_blender(
                    {"WARNING"},
                    "Deleting existing reachy instance, Reachy was not shut down properly",
                )
                self.reachy = None

            return False

    def connect_reachy(self, report_blender, ip="localhost"):

        self.ensure_connection(report_blender)

        if self.reachy != None:
            report_blender({"INFO"}, "Connection already established at '%s'" % ip)
            return

        # Try connection
        try:
            self.reachy = ReachySDK(host=ip)
            self.reachy.turn_on("reachy")
            report_blender({"INFO"}, "Connection established succesfully!")

        except:
            report_blender({"ERROR"}, ("Could not find connection at '%s'" % ip))

    def disconnect_reachy(self, report_blender):

        self.ensure_connection(report_blender)

        # Try connection
        if self.reachy != None:
            self.reachy_reset_pose()
            # self.reachy.turn_off_smoothly('reachy')
            # flush_communication()
            report_blender({"WARNING"}, "Proper disconnection disabled!")
            self.reachy = None
            report_blender({"INFO"}, "Disconnected Reachy")

        else:
            report_blender({"INFO"}, "No Reachy is connected")

    def reachy_goto(self, joint_angles, duration=1.0):

        goto(
            goal_positions=joint_angles,
            duration=duration,
            interpolation_mode=InterpolationMode.MINIMUM_JERK,
        )

    def send_angles(self, report_blender, duration=1.0, threaded=False):

        self.ensure_connection(report_blender)

        if self.reachy == None:
            report_blender({"ERROR"}, "Reachy not connected!")
            return

        if bpy.context.object.type != "ARMATURE":
            report_blender({"ERROR"}, "Please select Armature")
            return

        joint_angle_positions = {
            # Right arm
            self.reachy.r_arm.r_shoulder_pitch: self.angle_of_bone("shoulder_pitch.R")
            * (-1),
            self.reachy.r_arm.r_shoulder_roll: self.angle_of_bone("shoulder_roll.R"),
            self.reachy.r_arm.r_arm_yaw: self.angle_of_bone("shoulder_yaw.R") * (-1),
            self.reachy.r_arm.r_elbow_pitch: self.angle_of_bone("elbow_pitch.R"),
            self.reachy.r_arm.r_forearm_yaw: self.angle_of_bone("forearm_yaw.R") * (-1),
            self.reachy.r_arm.r_wrist_pitch: self.angle_of_bone("wrist_pitch.R"),
            self.reachy.r_arm.r_wrist_roll: self.angle_of_bone("wrist_roll.R"),
            self.reachy.r_arm.r_gripper: self.angle_of_bone("gripper.R"),
            # Left arm
            self.reachy.l_arm.l_shoulder_pitch: self.angle_of_bone("shoulder_pitch.L"),
            self.reachy.l_arm.l_shoulder_roll: self.angle_of_bone("shoulder_roll.L"),
            self.reachy.l_arm.l_arm_yaw: self.angle_of_bone("shoulder_yaw.L") * (-1),
            self.reachy.l_arm.l_elbow_pitch: self.angle_of_bone("elbow_pitch.L"),
            self.reachy.l_arm.l_forearm_yaw: self.angle_of_bone("forearm_yaw.L"),
            self.reachy.l_arm.l_wrist_pitch: self.angle_of_bone("wrist_pitch.L"),
            self.reachy.l_arm.l_wrist_roll: self.angle_of_bone("wrist_roll.L"),
            self.reachy.l_arm.l_gripper: self.angle_of_bone("gripper.L"),
        }

        if threaded:
            thread = threading.Thread(
                target=self.reachy_goto, args=[joint_angle_positions, duration]
            )
            self.threads.append(thread)
            thread.start()

        else:
            self.reachy_goto(joint_angle_positions, duration)

    def stream_angles(self, report_blender):

        self.ensure_connection(report_blender)

        if self.state == State.STREAMING:
            # Duration is faster than the interval, to finish before the next thread
            self.send_angles(
                report_blender, duration=self.stream_interval * 0.5, threaded=True
            )
            return self.stream_interval  # Seconds till next function call
        else:
            return None

    def stream_angles_enable(self, report_blender):

        self.ensure_connection(report_blender)

        if not self.state == State.STREAMING:
            self.state = State.STREAMING

            # Create Blender timer
            bpy.app.timers.register(
                functools.partial(self.stream_angles, report_blender)
            )

        else:
            report_blender({"INFO"}, "Streaming is already in progress,")

    def animate_angles(self, report_blender):

        self.ensure_connection(report_blender)

        if not self.state == State.ANIMATING:
            self.state = State.ANIMATING

            frame_prev = 0
            bpy.data.scenes["Scene"].show_keys_from_selected_only = False
            bpy.data.scenes["Scene"].frame_set(frame_prev)

            # Get to initial pose
            self.send_angles(report_blender, duration=1.0, threaded=False)

            # Iterate through all keyframes
            while (
                bpy.ops.screen.keyframe_jump(next=True) == {"FINISHED"}
                and self.state == State.ANIMATING
            ):

                frame_diff = bpy.data.scenes["Scene"].frame_current - frame_prev
                duration = frame_diff / bpy.context.scene.render.fps
                frame_prev = bpy.data.scenes["Scene"].frame_current

                # Wait for movement to complete before moving on to next keyframe
                self.send_angles(report_blender, duration, threaded=False)

            self.state = State.IDLE

        else:
            report_blender({"INFO"}, "Animation is already in progress,")

    def reachy_reset_pose(self):
        joint_angles = {
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
            self.reachy.l_arm.l_gripper: 0,
        }

        self.reachy_goto(joint_angles, 1.0)
