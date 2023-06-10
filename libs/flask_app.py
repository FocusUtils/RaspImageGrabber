from flask import Flask, render_template, Response, request, send_from_directory
from sbNative.runtimetools import get_path
import time
import numpy as np
from PIL import Image
import io
import threading
from traceback import print_exc
from urllib.parse import unquote
from pathlib import Path
import os
import json
import datetime
import sys


app = Flask(__name__,
            template_folder=str(get_path() / "deps" / "flask" / "templates"),
            static_folder=str(get_path() / "deps" / "flask" / "static"))


global image_dir
global microscope_position
global microscope_end
global microscope_start
global curr_device
global resolution_idx
global imgWidth, imgHeight, pData
global camera
global recording
global complete_config_running
global real_motor_position
global isGPIO
global motor


if str(get_path()) == ".":
    image_dir = str(Path(__file__).parent.parent / "images")
else:
    image_dir = str(get_path().parent / "images")
isGPIO = False
microscope_start = None
microscope_end = None
microscope_position = 0
real_motor_position = 0
recording = False
complete_config_running = False

try:
    from . import gpio_handler
except ImportError:
    print_exc()
    print("An Import Error occured, this might be because of your device not having GPIO pins. In This case ignore this Error, otherwise inspect the traceback above.")
else:
    isGPIO = True
    motor = gpio_handler.Motor([16, 19, 20, 21])
    motor.calibrate()


def reset_camera_properties():
    global curr_device
    global resolution_idx
    global imgWidth, imgHeight, pData
    global camera

    try:
        camera.Close()
    except:
        pass

    imgWidth, imgHeight, pData = None, None, None

    curr_device = None
    resolution_idx = None
    camera = None


reset_camera_properties()


def complete_config(*, with_bms_cam=True):
    print("COMPLETING CONFIG, STATING MOTOR")
    global complete_config_running
    if complete_config_running:
        return
    complete_config_running = True

    global imgWidth, imgHeight, pData
    global curr_device
    global resolution_idx
    global camera
    global real_motor_position
    global microscope_end
    global microscope_start
    global microscope_position
    global isGPIO
    global motor
    global image_dir

    now = datetime.datetime.now()
    formated_datetime = now.strftime("%Y_%m_%d_at_%H_%M_%S")


    print(image_dir)
    final_image_dir = Path(image_dir) / f"BMSCAM_Images_from_{formated_datetime}"
    print(final_image_dir)
    
    if with_bms_cam:
        os.mkdir(final_image_dir)
        camera = app.camparser.bmscam.Bmscam.Open(curr_device.id)

        if camera:
            camera.put_eSize(resolution_idx)
            resolution_idx = camera.get_eSize()

            imgWidth = curr_device.model.res[resolution_idx].width
            imgHeight = curr_device.model.res[resolution_idx].height

            camera.put_Option(app.camparser.bmscam.BMSCAM_OPTION_BYTEORDER, 0)
            camera.put_AutoExpoEnable(1)

            pData = bytes(app.camparser.bmscam.TDIBWIDTHBYTES(
                imgWidth * 24) * imgHeight)

            try:
                camera.StartPullModeWithCallback(
                    app.camparser.event_callback, (camera, pData, final_image_dir))
            except app.camparser.bmscam.HRESULTException as e:
                print("Failed to start camera.", e)
                camera.Close()

    print("IS GPIO:", isGPIO)
    if isGPIO:
        while True:
            if recording:
                break

            if real_motor_position < microscope_position:
                motor.step_forward()
                real_motor_position += 1
                
            elif real_motor_position > microscope_position:
                motor.step_backward()
                real_motor_position -= 1
            
            else:
                time.sleep(.5)
        
    else:
        while True:
            if recording:
                break
            time.sleep(.5)

    # making start smaller than end
    if microscope_start > microscope_end:
        microscope_end, microscope_start = microscope_start, microscope_end

    # moving to start position
    distance_to_start = microscope_start - real_motor_position 
    if distance_to_start > 0:
        for _ in range(distance_to_start):
            motor.step_forward()
    elif distance_to_start < 0:
        for _ in range(-distance_to_start):
            motor.step_backward()
    
    microscope_position = real_motor_position = microscope_start

    time.sleep(3)
    
    # start recording
    while real_motor_position < microscope_end:
        motor.step_forward()
        real_motor_position += 1
        time.sleep(2)
        camera.Snap(0)
    
    sys.exit()
        


@app.route("/")
def camera_select():
    return render_template("cameraselect.html")


@app.route('/favicon.svg')
def favicon():
    print("here", os.path.join(app.root_path, 'static'))
    _path = get_path()
    if str(_path) == ".":
        _path = Path(__file__).parent
    return send_from_directory(str(_path / "deps" / "flask" / "static"),
                               'favicon.svg', mimetype='image/svg+xml')


@app.route("/cameras", methods=["GET"])
def get_cameras():
    ret = ""
    for idx, device in app.camparser.list_devices():
        ret += f'<option value="{idx}">{device.displayname}: {device.id}</option>\n'

    return ret.strip("\n")


@app.route("/camera/<camera_idx>", methods=["POST"])
def set_camera(camera_idx):
    global curr_device
    global camera
    if not curr_device is None:
        reset_camera_properties()

    curr_device = app.camparser.bms_enum[int(camera_idx)]

    ret = ""
    for idx, reso in app.camparser.get_current_devices_resolution_options(curr_device):
        ret += f'<option value="{idx}">{reso[0]} x {reso[1]}</option>\n'

    return ret.strip("\n")


@app.route("/resolution/<reso_idx>", methods=["POST"])
def set_resolution(reso_idx):
    global imgWidth, imgHeight, pData
    global curr_device
    global resolution_idx
    global camera
    if not resolution_idx is None:
        temp_curr_device = curr_device
        reset_camera_properties()
        if not temp_curr_device is None:
            print("restoring old camera config")
            curr_device = temp_curr_device
            camera = app.camparser.bmscam.Bmscam.Open(curr_device.id)

    resolution_idx = int(reso_idx)
    th = threading.Thread(target=complete_config)
    th.start()
    return "", 200


@app.route("/files/directory/list/<enc_directory>")
def list_directory(enc_directory):
    global image_dir
    if enc_directory == "null":
        plib_dir = Path(image_dir)
    else:
        directory = unquote(unquote(enc_directory))
        plib_dir = Path(directory)
    
    ret = {}

    if not (plib_dir == plib_dir.parent): ## if plib_dir is not most parent folder
        ret[".."] = str(plib_dir.parent)

    for subfolder in os.listdir(plib_dir):
        if os.path.isdir(str(plib_dir / subfolder)):
            ret[subfolder] = str(plib_dir / subfolder)
    
    image_dir = plib_dir
    print(image_dir)
    return json.dumps(ret)
    
    
@app.route("/files/directory/get")
def get_current_images_directory():
    return image_dir    


@app.route("/microscope/move/<amount>")
def move_down(amount):
    global microscope_position
    microscope_position += int(amount)
    return str(microscope_position)


@app.route("/record-images")
def start_recording():
    global recording
    if recording:
        return "Already started recording", 400

    recording = True

    return "", 200

@app.route("/microscope/current")
def current_pos():
    global microscope_position
    return str(microscope_position)


@app.route("/microscope/move/start", methods=["GET"])
def move_start():
    global microscope_position
    global microscope_start
    microscope_position = microscope_start
    return str(microscope_position)

@app.route("/microscope/move/end", methods=["GET"])
def move_end():
    global microscope_position
    global microscope_end
    microscope_position = microscope_end
    return str(microscope_position)


@app.route("/microscope/start", methods=["GET", "POST"])
def set_start():
    global microscope_position
    global microscope_start
    if request.method == "POST":
        microscope_start = microscope_position

    elif request.method == "CONNECT":
        microscope_position = microscope_start

    return str(microscope_start)


@app.route("/microscope/end",  methods=["GET", "POST"])
def set_end():
    global microscope_position
    global microscope_end
    if request.method == "POST":
        microscope_end = microscope_position

    return str(microscope_end)


@app.route("/liveview")
def liveview():
    if bool(request.args.get("with_bms_cam")):
        th = threading.Thread(target=complete_config, kwargs={"with_bms_cam": 0})
        th.start()
    return render_template("liveview.html")


@app.route("/live-stream")
def live_stream():
    global imgWidth, imgHeight, pData

    if not imgWidth or not imgHeight or not pData:
        print("The camera has seemingly not been started yet")
        return Response("The camera has seemingly not been started yet", status=400)

    return Response(app.get_live_image(imgWidth, imgHeight, pData),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    def generate_example_live_image():
        image = np.zeros([680, 896, 3], dtype=np.uint8)
        image.fill(0)

        for tr in [[0, 0], [0, 890], [674, 0], [674, 890]]:
            for x in range(5):
                for y in range(5):
                    image[tr[0]+x, tr[1]+y][0] = 255

        while True:
            time.sleep(.1)
            output = np.copy(np.array(image))

            pil_img = Image.fromarray(output)

            img_byte_arr = io.BytesIO()
            pil_img.save(img_byte_arr, format="jpeg")

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + img_byte_arr.getvalue() + b'\r\n')

    app.get_live_image = generate_example_live_image
    app.run(host="192.168.2.113", port=5000)
