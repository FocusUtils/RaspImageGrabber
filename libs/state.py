from dataclasses import dataclass
from typing import Any, ClassVar, get_type_hints, Union
import subprocess
import werkzeug.serving as serving
from platformdirs import user_config_dir
from pathlib import Path
import os
import json
import time
import colorama
from typeguard import check_type, TypeCheckError


if __name__ == '__main__':
    from deps import bmscam
else:
    from .deps import bmscam


## SETTING_KEYS are the possible settings mapped to the method used to cast them from the website to the backend
global CONFIGURATION_FILE_PATH
global SETTING_KEYS
CONFIGURATION_FILE_PATH = Path(user_config_dir("MFSIG", "RICHARD_GALFI")) / "mfsig_user_config.json"
SETTING_KEYS = {
    "steps_per_motor_rotation": int,
    "GPIO_motor_pins": json.loads,
    "GPIO_default_on": lambda s: {"False": False, "True": True}[s],
    "GPIO_camera_pin": int,
    "distance_per_motor_rotation": float,
    "motor_rotation_units": int,
    "digi_cam_delay": float,
    "shake_rest_delay": float,
    "lowercase_motor_steps": int,
    "uppercase_motor_steps": int,
    "sleep_time_after_step": float,
    "whatsapp_number": str,
    "whatsapp_api_key": str,
    "execution_mode": lambda s: {"False": False, "True": True}[s],
}

print(CONFIGURATION_FILE_PATH)
if not os.path.exists(str(CONFIGURATION_FILE_PATH)):
    if not os.path.exists(str(CONFIGURATION_FILE_PATH.parent)):
        os.makedirs(str(CONFIGURATION_FILE_PATH.parent), exist_ok=True)

    print(f"A clean configuration file for your user has been created at {CONFIGURATION_FILE_PATH}:\n")
    with open(str(CONFIGURATION_FILE_PATH), "w") as wf:
        wf.write("{}")

with open(str(CONFIGURATION_FILE_PATH), "r") as rf:
    try:
        json.loads(rf.read())
    except ValueError:
        print(f"WARNING, YOUR JSON CONFIGURATION FILE IS NOT JSON LOADABLE, THIS WAS THE PREVIOUS CONTENT WHICH WAS REPLACED WITH A CLEAN FILE AT THE LOCATION {CONFIGURATION_FILE_PATH}:\n")

        rf.close()

        with open(str(CONFIGURATION_FILE_PATH), "w") as wf:
            wf.write("{}")



class State:
    execution_mode: ClassVar[bool] = False

print(State.execution_mode)

class ABSType:
    pass

class Meta(type):
    def __setattr__(self, __name: str, __value: Any) -> None:
        if State.execution_mode:
            return super().__setattr__(__name, __value)
        hints = get_type_hints(self)
        
        class_hint = hints.get(__name)
        if not class_hint:
            return super().__setattr__(__name, __value)
        hint = class_hint.__dict__.get("__args__")[0]
        try:
            
            v = check_type(__value, hint)
            return super().__setattr__(__name, v)
        except TypeCheckError:
            raise ValueError(f"The property {__name} only takes {hint}, got {type(__value)} <{__value}> instead.")

abs_motor_type = type("Motor", (ABSType,), dict({
    "step_forward": lambda *_:print("real motor position:", State.real_motor_position),
    "step_backward": lambda *_:print("real motor position:", State.real_motor_position),
    "cleanup": lambda *_:_,
    "calibrate": lambda *_:_,
}))

def fake_snap_func(*_):
    State.progress()

abs_camera_type = type("Camera", (ABSType,), dict({
    "Close": lambda *_:_,
    "Snap": fake_snap_func
}))

@dataclass
class State(metaclass=Meta):
    image_dir: ClassVar[Path]
    microscope_position: ClassVar[int]
    microscope_end: ClassVar[int]
    microscope_start: ClassVar[int]
    curr_device: ClassVar[Union[bmscam.BmscamDeviceV2, None]]
    resolution_idx: ClassVar[Union[int, None]]
    imgWidth: ClassVar[Union[int, None]]
    imgHeight: ClassVar[Union[int, None]]
    pData: ClassVar[Union[bytes, None]]
    camera: ClassVar[Union[bmscam.Bmscam, abs_camera_type]]
    recording: ClassVar[bool]
    start_motor_and_prepare_recording: ClassVar[bool]
    real_motor_position: ClassVar[int]
    isGPIO: ClassVar[bool]
    motor: ClassVar[abs_motor_type]
    server: ClassVar[serving.BaseWSGIServer]
    image_count: ClassVar[int]
    final_image_dir: ClassVar[Path]
    with_bms_cam: ClassVar[bool]
    bms_enum: ClassVar[list]
    recording_progress: ClassVar[Union[int, None]]
    current_image_index: ClassVar[Union[int, None]]
    busy_capturing: ClassVar[bool]
    current_recording_task: ClassVar[Union[str, None]]
    
    ## user configurables
    steps_per_motor_rotation: ClassVar[int]
    distance_per_motor_rotation: ClassVar[float]
    motor_rotation_units: ClassVar[int]
    GPIO_motor_pins: ClassVar[list]
    GPIO_camera_pin: ClassVar[Union[int, None]]
    GPIO_default_on: ClassVar[bool]
    digi_cam_delay: ClassVar[float]
    shake_rest_delay: ClassVar[float]
    lowercase_motor_steps: ClassVar[int]
    uppercase_motor_steps: ClassVar[int]
    sleep_time_after_step: ClassVar[float]
    whatsapp_number: ClassVar[int]
    whatsapp_api_key: ClassVar[int]
    execution_mode: ClassVar[bool] = False


    @classmethod
    def progress(cls):
        State.recording_progress = int((State.current_image_index) / (State.image_count) * 100)
        print(State.recording_progress)
        State.busy_capturing = False


    @classmethod
    def save_configuration_data(cls):
        global SETTING_KEYS
        with open(str(CONFIGURATION_FILE_PATH), "w") as wf:
            content = json.dumps(
                {key: getattr(State, key, None) for key in SETTING_KEYS.keys()},
                indent=4
            )
            wf.write(content)
            wf.truncate()


    @classmethod
    def load_configuration(cls, j=None):
        global CONFIGURATION_FILE_PATH
        if not j:
            for tries in range(1,11):
                with open(str(CONFIGURATION_FILE_PATH), "r") as rf:
                    content = rf.read()
                    try:
                        j = json.loads(content)
                    except json.JSONDecodeError:
                        pass
                    else:
                        break
                    print(f"{colorama.Fore.YELLOW}FAILED TO LOAD CONFIGURATION, RETRYING IN {tries*100} MS (ATTEMPT {tries}){colorama.Fore.RESET}")
                    time.sleep(tries/10)
            else:
                print(f"{colorama.Fore.RED}FAILED TO LOAD CONFIGURATION AFTER {tries} TRIES AND {(tries/2*(2 + (tries-1)))*100} MS{colorama.Fore.RESET}")


        if "steps_per_motor_rotation" in j.keys():
            State.steps_per_motor_rotation = j["steps_per_motor_rotation"]
        if "GPIO_motor_pins" in j.keys():
            State.GPIO_motor_pins = j["GPIO_motor_pins"]
        if "GPIO_default_on" in j.keys():
            State.GPIO_default_on = j["GPIO_default_on"]
        if "GPIO_camera_pin" in j.keys():
            State.GPIO_camera_pin = j["GPIO_camera_pin"]
        if "distance_per_motor_rotation" in j.keys():
            State.distance_per_motor_rotation = j["distance_per_motor_rotation"]
        if "motor_rotation_units" in j.keys():
            State.motor_rotation_units = j["motor_rotation_units"]
        

        if "digi_cam_delay" in j.keys():
            State.digi_cam_delay = j["digi_cam_delay"]

        if "shake_rest_delay" in j.keys():
            State.shake_rest_delay = j["shake_rest_delay"]
        
        if "lowercase_motor_steps" in j.keys():
            State.lowercase_motor_steps = j["lowercase_motor_steps"]

        if "uppercase_motor_steps" in j.keys():
            State.uppercase_motor_steps = j["uppercase_motor_steps"]
        
        if "sleep_time_after_step" in j.keys():
            State.sleep_time_after_step = j["sleep_time_after_step"]
        
        if "execution-mode" in j.keys():
            State.execution_mode = j["execution-mode"]
        
        try:
            if "whatsapp_number" in j.keys():
                State.whatsapp_number = str(j["whatsapp_number"])
        except ValueError:pass

        try:
            if "whatsapp_api_key" in j.keys():
                State.whatsapp_api_key = j["whatsapp_api_key"]
        except ValueError:pass
        
        try:
            if "execution_mode" in j.keys():
                State.execution_mode = j["execution_mode"]
        except ValueError:pass

def outgoing_webrequest(func):
    def wrapper(*args, **kwargs):
        if State.isGPIO:
            subprocess.run("sudo systemctl stop dnsmasq".split(" "))
        ret = func(*args, **kwargs)
        if State.isGPIO:
            subprocess.run("sudo systemctl start dnsmasq".split(" "))
        return ret
    return wrapper
        
