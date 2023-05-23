import sys
import pygame
import numpy as np
from PIL import Image
import time

from .deps import bmscam

from sbNative.debugtools import log

bms_enum = bmscam.Bmscam.EnumV2()

def list_devices():
    return [(i, device) for i,device in enumerate(bms_enum)]

def get_current_devices_resolution_options(curr_device):
    return [(i, (curr_device.model.res[i].width, curr_device.model.res[i].height)) for i in range(0, curr_device.model.preview)]

def handleImageEvent(camera, pData):
    try:
        camera.PullImageV3(pData, 0, 24, 0, None)
        print("pulled img")
    except bmscam.HRESULTException as e:
        log(e)
        print("Couldn't pull Still image")


def handleStillImageEvent():
    info = bmscam.BmscamFrameInfoV3()
    try:
        camera.PullImageV3(None, 1, 24, 0, info)
    except bmscam.HRESULTException as e:
        log(e)
        print("Couldn't pull Still image")
    else:
        if info.width > 0 and info.height > 0:
            buff = bytes(bmscam.TDIBWIDTHBYTES(info.width * 24) * info.height)
            try:
                camera.PullImageV3(buff, 1, 24, 0, info)
            except bmscam.HRESULTException:
                pass
            else:
                pil_image = Image.frombytes("RGB", (imgWidth, imgHeight), buff)
                pil_image.save("Image.png")
        

def event_callback(n_event, ctx):
    camera, pData = ctx
    if camera:
        if bmscam.BMSCAM_EVENT_IMAGE == n_event:
            handleImageEvent(camera, pData)

        elif bmscam.BMSCAM_EVENT_EXPOSURE == n_event:
            # self.handleExpoEvent()
            pass
        elif bmscam.BMSCAM_EVENT_TEMPTINT == n_event:
            # self.handleTempTintEvent()
            pass
        elif bmscam.BMSCAM_EVENT_STILLIMAGE == n_event:
            handleStillImageEvent()
            pass
        elif bmscam.BMSCAM_EVENT_ERROR == n_event:
            camera.Close()
            log("Warning", "Generic Error.")
        elif bmscam.BMSCAM_EVENT_DISCONNECTED == n_event:
            camera.Close()
            log("Warning", "Camera disconnect.")