from flask import Flask, render_template, Response, request, send_from_directory, redirect
import werkzeug.serving as serving
from sbNative.runtimetools import get_path
import time
from PIL import Image
import io
from traceback import print_exc
from urllib.parse import unquote
from pathlib import Path
import os
import json
from libs import cameraParser
from .state import State, SETTING_KEYS, abs_motor_type, abs_camera_type, abs_leds_type, create_progress_response
import socket
import logging
log = logging.getLogger('werkzeug')


org_mk_server = serving.make_server


def wrapper(*args, **kwargs):
    State.server = org_mk_server(*args, **kwargs)
    return State.server


serving.make_server = wrapper

app = Flask(__name__,
            template_folder=str(get_path() / "deps" / "flask" / "templates"),
            static_folder=str(get_path() / "deps" / "flask" / "static"))


if str(get_path()) == ".":
    State.image_dir = Path(__file__).parent.parent / "images"
else:
    State.image_dir = get_path().parent / "images"

State.isGPIO = False

try:
    from . import gpio_handler
except ImportError:
    print_exc()
    print("An Import Error occured, this might be because of your device not having GPIO pins. In This case ignore this Error, otherwise inspect the traceback above.")
else:
    State.isGPIO = True


def generate_live_image():
    while True:
        time.sleep(.1)

        try:
            pil_img = Image.frombytes(
                "RGB", (State.imgWidth, State.imgHeight), State.pData)
        except TypeError:
            yield (b'--frame\r\n'
               b'Content-Type: text\r\n\r\n' + b"It seems a temporary issue has occured..." + b'\r\n')
        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format="jpeg")

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + img_byte_arr.getvalue() + b'\r\n')


def reset_camera_properties():
    try:
        State.camera.Close()
    except AttributeError:
        pass

    State.imgWidth, State.imgHeight, State.pData = None, None, None

    State.curr_device = None
    State.resolution_idx = None
    State.camera = abs_camera_type()
    State.microscope_start = 0
    State.microscope_end = 0
    State.microscope_position = 0
    State.real_motor_position = 0
    State.recording = False
    State.start_motor_and_prepare_recording_running = False
    State.image_count = 1
    State.recording_progress = 0
    State.current_recording_task = None
    State.current_image_index = 0
    State.current_lighting_index = 0
    State.busy_capturing = False
    State.with_bms_cam = False

    ## possible user configs
    State.distance_per_motor_rotation = 100.0
    State.motor_rotation_units = 3
    State.steps_per_motor_rotation = 400
    State.GPIO_motor_pins = [21, 20, 19, 16]
    State.GPIO_default_on = False
    State.GPIO_camera_pin = 26
    State.digi_cam_delay = 1
    State.shake_rest_delay = 2
    State.lowercase_motor_steps = 1
    State.uppercase_motor_steps = 25
    State.sleep_time_after_step = 2.5
    State.whatsapp_api_key = -1
    State.whatsapp_number = -1


    State.load_configuration()
    if State.execution_mode:
        print("logging level is now only errors")
        log.setLevel(logging.ERROR)
    else:
        print("logging everything")
        log.setLevel(logging.INFO)

    if State.isGPIO:
        State.motor = gpio_handler.Motor(State.GPIO_motor_pins)
        State.motor.calibrate()
        State.leds = gpio_handler.LEDS([20, 16])
    else:
        State.motor = abs_motor_type()
        State.leds = abs_leds_type()

    State.leds.all_on()



reset_camera_properties()


@app.route("/settings/<_key>", methods=["GET"])
def get_setting(_key):
    if "whatsapp" in _key.lower():
        return "Not so fast, i thought of this...", 200
    return str(getattr(State, _key.replace("-","_"), "")), 200


@app.route("/settings/<_key>/<value>", methods=["POST"])
def set_setting(_key, value):
    _perm_and_reload_requiering = ["GPIO_camera_pin", "GPIO_motor_pins", "execution-mode"]
    
    key = _key.replace("-","_")
    print(key)
    if key not in SETTING_KEYS:
        return f"There is no such setting like {_key}!", 400
    
    setattr(State, key, SETTING_KEYS[key]((value)))
    State.save_configuration_data()
    
    if key in _perm_and_reload_requiering:
        reset_camera_properties()
    else:
        State.load_configuration()

    if key == "GPIO_camera_pin":
        print("Snapping test camera")
        if State.isGPIO:
            temp_camera = gpio_handler.Camera(State.GPIO_camera_pin)
            temp_camera.Snap()
            temp_camera.Close()
            del temp_camera
        else:
            return "There is no GPIO connection so this couldn't be tested, the value was set regardless!", 299
        
    
    if key == "GPIO_motor_pins":
        print("Moving motor")
        if State.isGPIO:
            time.sleep(3)
            for _ in State.motor.pins:
                State.microscope_position += 1
                time.sleep(.5)
            
            time.sleep(2)
            for _ in State.motor.pins:
                State.microscope_position -= 1
                time.sleep(.5)

        else:
            return "There is no GPIO connection so this couldn't be tested, the value was set regardless!", 299
    
    if key == "execution_mode":
        print("execution mode changed")
        if State.execution_mode:
            print("logging level is now only errors")
            log.setLevel(logging.ERROR)
        else:
            print("logging everything")
            log.setLevel(logging.INFO)
    
    if key in _perm_and_reload_requiering:
        return "Warning, the changes made to the motor to prepare a recording have been reset by a reload", 299
    return "", 200

@app.route("/cam-select")
def camera_select():
    return render_template("cameraselect.html")


@app.route("/settings")
def settings():
    return render_template("settings.html")


@app.route("/liveview")
def liveview():
    if bool(request.args.get("with_bms_cam")) is False:
        State.with_bms_cam = True
    else:
        State.with_bms_cam = False
    ## set the camera
    
    if State.with_bms_cam:
        if (State.curr_device is None or 
            State.resolution_idx is None):
            return "One or more of the parameters necessary for the BMS camera have not been set, please return to the main page and choose to use another way of capturing an image or set all the necessary parameters!", 400
    
        if State.camera is not None:
            State.camera.Close()
        State.camera = cameraParser.bmscam.Bmscam.Open(State.curr_device.id)

        if State.camera:
            State.camera.put_eSize(State.resolution_idx)
            State.resolution_idx = State.camera.get_eSize()

            State.imgWidth = State.curr_device.model.res[State.resolution_idx].width
            State.imgHeight = State.curr_device.model.res[State.resolution_idx].height

            State.camera.put_Option(
                cameraParser.bmscam.BMSCAM_OPTION_BYTEORDER, 0)
            State.camera.put_AutoExpoEnable(1)

            State.pData = bytes(cameraParser.bmscam.TDIBWIDTHBYTES(
                State.imgWidth * 24) * State.imgHeight)

            try:
                State.camera.StartPullModeWithCallback(
                    cameraParser.event_callback, ())
            except cameraParser.bmscam.HRESULTException as e:
                print("Failed to start camera.", e)
                State.camera.Close()
                return "Failed to start camera. " + e, 500
    else:
        if State.isGPIO:
            State.camera = gpio_handler.Camera(State.GPIO_camera_pin)
        else:
            State.camera = abs_camera_type()

    return render_template("liveview.html")


@app.route("/stepsetter")
def stepsetter():
    return render_template("stepsetter.html")


@app.route('/favicon.svg')
def favicon():
    _path = get_path()
    if str(_path) == ".":
        _path = Path(__file__).parent
    return send_from_directory(str(_path / "deps" / "flask" / "static"),
                               'favicon.svg', mimetype='image/svg+xml')


@app.route("/image-count/<count>", methods=["POST"])
def set_image_count(count):
    if State.recording:
        return "Currently recording, change the value when done or abort the program!", 400
    State.image_count = int(float(count))
    return "", 200


@app.route("/cameras", methods=["GET"])
def get_cameras():
    ret = ""
    for idx, device in cameraParser.list_devices():
        ret += f'<option value="{idx}">{device.displayname}: {device.id}</option>\n'

    return ret.strip("\n")

@app.route("/recording-progress", methods=["GET"])
def recording_progress():
    return create_progress_response()


@app.route("/camera/<camera_idx>", methods=["POST"])
def set_camera(camera_idx):
    if State.recording:
        return "Currently recording, change the value when done or abort the program!", 400
    if State.curr_device is not None:
        reset_camera_properties()
    try:
        State.curr_device = State.bms_enum[int(camera_idx)]
    except AttributeError:
        return "Failed to select this device, try loading this page again and reselecting the camera!", 400
    
    ret = ""
    for idx, reso in cameraParser.get_current_devices_resolution_options(State.curr_device):
        ret += f'<option value="{idx}">{reso[0]} x {reso[1]}</option>\n'

    return ret.strip("\n")


@app.route("/resolution/<reso_idx>", methods=["POST"])
def set_resolution(reso_idx):
    if State.recording:
        return "Currently recording, change the value when done or abort the program!", 400
    State.resolution_idx = int(reso_idx)
    return "", 200


@app.route("/files/directory/list/<enc_directory>")
def list_directory(enc_directory):
    if enc_directory == "null":
        plib_dir = Path(State.image_dir)
    else:
        directory = unquote(unquote(enc_directory))
        plib_dir = Path(directory)

    ret = {}

    if plib_dir != plib_dir.parent:  # if plib_dir is not most parent folder
        ret[".."] = str(plib_dir.parent)

    for subfolder in os.listdir(plib_dir):
        if os.path.isdir(str(plib_dir / subfolder)):
            ret[subfolder] = str(plib_dir / subfolder)

    State.image_dir = plib_dir
    return json.dumps(ret)


@app.route("/files/directory/get")
def get_current_images_directory():
    return str(State.image_dir)


@app.route("/record-images")
def start_recording():
    if State.recording:
        return "Already started recording", 400
    
    if State.image_count <= 1:
        return "You may not take less than 2 images!", 400

    if State.image_count > abs(State.microscope_end - State.microscope_start):
        return "You may not take more images than Steps taken by the motor, this is redundant due to having multiple images in the same position.", 400
    
    State.recording = True
    return "", 200


@app.route("/microscope/current")
def current_pos():
    return str(State.microscope_position)


@app.route("/microscope/move-by/<amount>")
def move_by(amount):
    if State.recording:
        return "Currently recording, change the value when done or abort the program!", 400
    State.microscope_position += int(float(amount))
    return str(State.microscope_position)

@app.route("/microscope/move-to/<position>")
def move_to(position):
    if State.recording:
        return "Currently recording, change the value when done or abort the program!", 400
    State.microscope_position = int(float(position))
    return str(State.microscope_position)


@app.route("/microscope/move/start", methods=["GET"])
def move_start():
    if State.recording:
        return "Currently recording, change the position when done or abort the program!", 400
    State.microscope_position = State.microscope_start
    return str(State.microscope_position)


@app.route("/microscope/move/end", methods=["GET"])
def move_end():
    if State.recording:
        return "Currently recording, change the position when done or abort the program!", 400
    State.microscope_position = State.microscope_end
    return str(State.microscope_position)


@app.route("/microscope/start", methods=["GET", "POST"], defaults={"pos": None})
@app.route("/microscope/start/<pos>", methods=["POST"])
def set_start(pos):
    if request.method == "POST":
        if State.recording:
            return "Currently recording, change the value when done or abort the program!", 400
        if pos:
            State.microscope_start = int(float(pos))
        else:
            State.microscope_start = State.microscope_position

    return str(State.microscope_start)


@app.route("/microscope/end",  methods=["GET", "POST"], defaults={"pos": None})
@app.route("/microscope/end/<pos>", methods=["POST"])
def set_end(pos):
    if request.method == "POST":
        if State.recording:
            return "Currently recording, change the value when done or abort the program!", 400
        if pos:
            State.microscope_end = int(float(pos))
        else:
            State.microscope_end = State.microscope_position

    return str(State.microscope_end)


@app.route("/live-stream")
def live_stream():
    if not State.with_bms_cam:
        return Response("You chose not to use a bms camera, rather one controlled by the GPIO!", 299)
    if not State.imgWidth or not State.imgHeight or not State.pData:
        return Response("The camera has seemingly not been started yet", status=400)

    return Response(generate_live_image(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    if State.isGPIO:
        ip = "10.3.141.1"
    else:
        ip = socket.gethostbyname(socket.gethostname())
    return redirect(f"http://{ip}/cam-select")
