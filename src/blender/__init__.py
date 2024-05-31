import os
import platform
import subprocess
import sys

import bpy
from bpy.utils import register_class, unregister_class

from .reachy_marionette import ReachyMarionette
from .actions_gpt import ActionsGPT

# Addon metadata
bl_info = {
    "name": "ReachyMarionette",
            "author": "Energinet",
            "version": (1, 0, 0),
            "blender": (4, 0, 1),
            "location": "Toolbar > ReachyMarionette",
            "description": "Connects to the Reachy robot from Pollen Robotics, to stream angles of joints in Reachy rig.",
            "category": "Animation"
}

# Install missing packages to Blenders Python install


def install_packages(packages):

    if platform.system() == 'win32':

        python_exe = os.path.join(sys.prefix, 'bin', 'python.exe')
        target = os.path.join(sys.prefix, 'lib', 'site-packages')

        subprocess.call([python_exe, '-m', 'ensurepip'])
        subprocess.call(
            [python_exe, '-m', 'pip', 'install', '--upgrade', 'pip'])

        for package in packages:
            subprocess.call([python_exe, '-m', 'pip', 'install',
                            '--upgrade', package, '-t', target])

    else:
        for package in packages:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package])


try:
    import openai
    import reachy_sdk
    import requests

except:
    print("openai and/or reachy_sdk module not found, installing with pip...")

    install_packages(["openai", "reachy-sdk", "requests"])

    import openai
    import reachy_sdk
    import requests

    print("Done installing packages")


# Global object
reachy = ReachyMarionette()
gpt = ActionsGPT()


# Classes

class SceneProperties(bpy.types.PropertyGroup):
    # Defining custom properties to be used by the addon panel

    def callback_kinematics(self, context):
        # Toggle IK constraint on bones that has thems
        scene_properties = context.scene.scn_prop

        for bone in bpy.context.active_object.pose.bones:

            if not 'IK' in bone.constraints:
                continue

            if scene_properties.Kinematics == 'FK':
                bone.constraints['IK'].enabled = False
            elif scene_properties.Kinematics == 'IK':
                bone.constraints['IK'].enabled = True

    IPaddress: bpy.props.StringProperty(
        name="IP adress",
        description="Reachy's IP adress (default = localhost)",
        default="localhost")  # type: ignore (stops warning squiggles)

    Kinematics: bpy.props.EnumProperty(
        name="Kinematics",
        description="Choose if rig is controlled by forward kinematics (FK) or inverse kinematics (IK).",
        items=[('FK', 'FK', ''),
               ('IK', 'IK', '')],
        default='FK',
        update=callback_kinematics)  # type: ignore (stops warning squiggles)

    Promt: bpy.props.StringProperty(
        name="Promt",
        description="Promt for ChatGPT",
        default="")  # type: ignore (stops warning squiggles)


class REACHYMARIONETTE_OT_ConnectReachy(bpy.types.Operator):
    # Handling connection to Reachy
    bl_idname = "reachy_marionette.connect_reachy"
    bl_label = "Connect to Reachy Robot via IP-adress"

    def execute(self, context):
        scene_properties = context.scene.scn_prop

        reachy.connect_reachy(self.report, scene_properties.IPaddress)

        return {'FINISHED'}


class REACHYMARIONETTE_OT_DisconnectReachy(bpy.types.Operator):
    # Handling connection to Reachy
    bl_idname = "reachy_marionette.disconnect_reachy"
    bl_label = "Disconnect current connection to Reachy"

    def execute(self, context):

        reachy.disconnect_reachy(self.report)

        return {'FINISHED'}


class REACHYMARIONETTE_OT_SendPose(bpy.types.Operator):
    # Get angles from Blender rig, and send to Reachy

    bl_idname = "reachy_marionette.send_pose"
    bl_label = "Send current pose once"

    def execute(self, context):

        reachy.send_angles(self.report)

        return {'FINISHED'}


class REACHYMARIONETTE_OT_StreamPose(bpy.types.Operator):
    # Continously get angles from Blender rig, and stream to Reachy

    bl_idname = "reachy_marionette.stream_angles"
    bl_label = "Live streaming of bone angles"

    def __init__(self):
        print("Stream starting...")

    def __del__(self):
        print("Stream ended")

    def modal(self, context, event):
        if event.type == 'ESC':
            reachy.set_state_idle()

            self.report({'INFO'}, "ESC key pressed, stopping stream")
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)

        reachy.stream_angles_enable(self.report)

        return {'RUNNING_MODAL'}


class REACHYMARIONETTE_OT_AnimatePose(bpy.types.Operator):
    # Go through animation timeline and get angles from Blender rig, and send to Reachy

    bl_idname = "reachy_marionette.animate_pose"
    bl_label = "Go through animation timeline and send poses"

    def __init__(self):
        print("Animation starting...")

    def __del__(self):
        print("Animation ended")

    def modal(self, context, event):
        if event.type == 'ESC':
            reachy.set_state_idle()

            self.report({'INFO'}, "ESC key pressed, stopping animation")
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)

        reachy.animate_angles(self.report)

        return {'RUNNING_MODAL'}


class REACHYMARIONETTE_OT_ActivateGPT(bpy.types.Operator):

    bl_idname = "reachy_marionette.activate_gpt"
    bl_label = "Start ChatGPT client"

    def execute(self, context):

        if not gpt.activate(self.report):
            return {'CANCELLED'}

        return {'FINISHED'}


class REACHYMARIONETTE_OT_SendRequest(bpy.types.Operator):
    # Select action

    bl_idname = "reachy_marionette.action_selection"
    bl_label = "Select action"

    def execute(self, context):
        scene_properties = context.scene.scn_prop

        gpt.send_request(scene_properties.Promt, reachy, self.report)

        return {'FINISHED'}


class REACHYMARIONETTE_PT_Panel(bpy.types.Panel):
    # Addon panel displaying options

    bl_label = "Stream Angles"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ReachyMarionette"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene_properties = context.scene.scn_prop

        layout.prop(scene_properties, "IPaddress")

        layout.row().operator(REACHYMARIONETTE_OT_ConnectReachy.bl_idname,
                              text="Connect to Reachy", icon='PLUGIN')

        layout.row().operator(REACHYMARIONETTE_OT_DisconnectReachy.bl_idname,
                              text="Disconnect Reachy", icon='UNLINKED')

        layout.prop(scene_properties, "Kinematics")

        layout.row().operator(REACHYMARIONETTE_OT_SendPose.bl_idname,
                              text="Send Pose", icon='ARMATURE_DATA')

        layout.row().operator(REACHYMARIONETTE_OT_StreamPose.bl_idname,
                              text="Stream Pose", icon='ARMATURE_DATA')

        layout.row().operator(REACHYMARIONETTE_OT_AnimatePose.bl_idname,
                              text="Animate Pose", icon='ARMATURE_DATA')

        layout.row().operator(REACHYMARIONETTE_OT_ActivateGPT.bl_idname,
                              text="Activate GPT", icon='ARMATURE_DATA')

        layout.prop(scene_properties, "Promt")

        layout.row().operator(REACHYMARIONETTE_OT_SendRequest.bl_idname,
                              text="Send Request", icon='ARMATURE_DATA')


classes = (
    SceneProperties,
    REACHYMARIONETTE_OT_ConnectReachy,
    REACHYMARIONETTE_OT_DisconnectReachy,
    REACHYMARIONETTE_OT_SendPose,
    REACHYMARIONETTE_OT_StreamPose,
    REACHYMARIONETTE_OT_AnimatePose,
    REACHYMARIONETTE_OT_ActivateGPT,
    REACHYMARIONETTE_OT_SendRequest,
    REACHYMARIONETTE_PT_Panel
)


def register():
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.scn_prop = bpy.props.PointerProperty(type=SceneProperties)


def unregister():
    for cls in (classes):
        unregister_class(cls)

    del bpy.types.Scene.scn_prop

    def temp(_x, _y):
        ...

    reachy.disconnect_reachy(temp)


if __name__ == "__main__":
    register()
