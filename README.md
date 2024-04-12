# ReachyMarionette

Copies poses of robot rig in Blender to physical (or simulated) Reachy robot.

<!-- vscode-markdown-toc -->
* 1. [Requirements](#Requirements)
* 2. [Setup](#Setup)
	* 2.1. [Unity Reachy Simulation](#UnityReachySimulation)
	* 2.2. [Blender Rig](#BlenderRig)
	* 2.3. [Blender Addon](#BlenderAddon)
* 3. [Usage](#Usage)
* 4. [Development Setup With VSCode](#DevelopmentSetupWithVSCode)
	* 4.1. [Blender Deployment](#BlenderDeployment)

<!-- vscode-markdown-toc-config
	numbering=true
	autoSave=true
	/vscode-markdown-toc-config -->
<!-- /vscode-markdown-toc -->



##  1. <a name='Requirements'></a>Requirements
*Tested with Windows 11.*

- Unity <= 2022.3.15f1
- Blender <= 4.1
- VSCode
- Python == 3.9.7


##  2. <a name='Setup'></a>Setup 

###  2.1. <a name='UnityReachySimulation'></a>Unity Reachy Simulation

If physical robot is not available, Pollen Robotics has created a simulaiton of Reachy 2021 in Unity, find package [here](https://github.com/pollen-robotics/reachy2021-unity-package).

The IP adress to input into the addon is then `localhost`.

###  2.2. <a name='BlenderRig'></a>Blender Rig

> TODO: Upload Blender file of Reachy Rig.


###  2.3. <a name='BlenderAddon'></a>Blender Addon



In Blender, navigate to `Edit > Preferences... > Add-Ons`.

Press `Install`.

Navigate to the addon Zip file, click `Install Add-on`.

##  3. <a name='Usage'></a>Usage

Start robot (physical or Unity simulation).

In Blender, find the `ReachyMarionette` tab in the N Panel (if not visible press `N`).

Enter the [IP adress of Reachy](https://docs.pollen-robotics.com/sdk/getting-started/finding-ip/), or if Reachy is simulated with Unity use `localhost`.

Change the pose of the rig, and press `Send Pose` to have Reachy mimic the pose of the rig in Blender.

##  4. <a name='DevelopmentSetupWithVSCode'></a>Development Setup With VSCode

Install Python dependencies with:
```
pip3 install -r requirements.txt
```

Alternatively, it is recommended to use a virtual environment, like pipenv or Anaconda. Install dependencies with:
```
pipenv install
```

Open VSCode and download the extension `Blender Development` by Jaques Lucke. 

###  4.1. <a name='BlenderDeployment'></a>Blender Deployment

> If addon is installed through `.zip` file, disable it first.

Activate pipenv from terminal and open VSCode:
```
pipenv shell
code ./<subfolder>
```

Start Blender  from VSCode with `Ctrl + Shift + P` and search for `Blender: Start`. Use the location of your Blender install. 
> If there is an error, check out [this video](https://youtu.be/YUytEtaVrrc?t=469) for how to fix it.

From here you can use `Ctrl + Shift + P` and choose `Blender: Reload Addons` to update Addons in Blender.

> NOTE: The `__init__.py` file is the addon entry point from Blender, so all Blender classes should be registered here. This is only an affect of the VSCode Blender extension.
