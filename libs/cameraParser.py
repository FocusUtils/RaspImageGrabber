import sys
import numpy as np
from PIL import Image
import time
from pathlib import Path
from .deps import bmscam
from .state import State
import importlib
from sbNative.debugtools import log


def list_devices():
    State.bms_enum = bmscam.Bmscam.EnumV2()
    return [(i, device) for i,device in enumerate(State.bms_enum)]

def get_current_devices_resolution_options(curr_device):
    return [(i, (curr_device.model.res[i].width, curr_device.model.res[i].height)) for i in range(0, curr_device.model.preview)]

def handleImageEvent():
    try:
        State.camera.PullImageV3(State.pData, 0, 24, 0, None)
    except bmscam.HRESULTException as e:
        log(e)

def handleStillImageEvent():
    info = bmscam.BmscamFrameInfoV3()
    try:
        State.camera.PullImageV3(None, 1, 24, 0, info)
    except bmscam.HRESULTException as e:
        log(e)
    else:
        if info.width > 0 and info.height > 0:
            buff = bytes(bmscam.TDIBWIDTHBYTES(info.width * 24) * info.height)
            try:
                State.camera.PullImageV3(buff, 1, 24, 0, info)
            except bmscam.HRESULTException:
                pass
            else:
                pil_image = Image.frombytes("RGB", (info.width, info.height), buff)
                pil_image.save(str(Path(State.final_image_dir) / f"Image_{State.current_image_index}_{State.current_lighting_index}.tiff"))
                State.progress()
        

def event_callback(n_event, _):
    if State.camera:
        if bmscam.BMSCAM_EVENT_IMAGE == n_event:
            handleImageEvent()

        elif bmscam.BMSCAM_EVENT_EXPOSURE == n_event:
            # self.handleExpoEvent()
            pass
        elif bmscam.BMSCAM_EVENT_TEMPTINT == n_event:
            # self.handleTempTintEvent()
            pass
        elif bmscam.BMSCAM_EVENT_STILLIMAGE == n_event:
            handleStillImageEvent()
            
        elif bmscam.BMSCAM_EVENT_ERROR == n_event:
            State.camera.Close()
            log("Warning", "Generic Error.")

        elif bmscam.BMSCAM_EVENT_DISCONNECTED == n_event:
            State.camera.Close()
            log("Warning", "Camera disconnect.")
