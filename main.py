import time
import datetime
import os
import threading
from libs import flask_app
from libs.state import State
import websockets
from websockets.server import serve
import asyncio
import time
from libs.notifier import send_text_to_whatsapp
from sbNative.runtimetools import get_path
from libs.state import create_progress_response
import traceback
from colorama import Fore


def start_motor_and_prepare_recording():
    if State.start_motor_and_prepare_recording_running:
        return
    State.start_motor_and_prepare_recording_running = True

    while True:
        State.current_recording_task = "No current task, waiting for recording start!"
        while True:
            if State.recording:
                break
            
            if State.real_motor_position < State.microscope_position:
                start = time.perf_counter_ns()
                State.real_motor_position += 1
                State.motor.step_forward()

            elif State.real_motor_position > State.microscope_position:
                State.real_motor_position -= 1
                State.motor.step_backward()

            else:
                time.sleep(.001)

        if State.with_bms_cam:
            State.current_recording_task = "Creating destination directory..."
            now = datetime.datetime.now()
            formated_datetime = now.strftime("%Y_%m_%d_at_%H_%M_%S")

            State.final_image_dir = State.image_dir / f"BMSCAM_Images_from_{formated_datetime}"
            os.mkdir(str(State.final_image_dir))

        # making start smaller than end
        State.current_recording_task = "Moving the motor to the start position..."
        if State.microscope_start > State.microscope_end:
            State.microscope_end, State.microscope_start = State.microscope_start, State.microscope_end

        # moving to start position
        distance_to_start = State.microscope_start - State.real_motor_position
        if distance_to_start > 0:
            for _ in range(distance_to_start):
                State.motor.step_forward()
                State.real_motor_position += 1

        elif distance_to_start < 0:
            for _ in range(-distance_to_start):
                State.motor.step_backward()
                State.real_motor_position -= 1

        State.microscope_position = State.real_motor_position = State.microscope_start

        State.current_recording_task = "Shortly resting to ensure stability..."
        time.sleep(3)

        
        # start recording
        State.leds.all_off()
        State.current_image_index = 0
        State.current_recording_task = "Taking pictures..."
        target_total_steps = State.microscope_end - State.microscope_start
        
        target_steps = []

        for _i in range(0, State.image_count):
            target_steps.append(int(State.microscope_start + target_total_steps * (_i / (State.image_count-1))))

        for ts_curr in target_steps:
            for _ in range(ts_curr - State.real_motor_position):
                State.motor.step_forward()
                State.real_motor_position += 1

            time.sleep(State.shake_rest_delay)
            
            State.leds.on(0)
            State.busy_capturing = True
            State.current_lighting_index = 0
            State.camera.Snap(0) ## res index 0 and lighting index 0
            while State.busy_capturing:
                time.sleep(.1)

            State.leds.off(0)
            State.leds.on(1)
            State.busy_capturing = True
            State.current_lighting_index = 1
            State.camera.Snap(0) ## res index 0 and lighting index 1 
            while State.busy_capturing:
                time.sleep(.1)
            State.leds.off(1)
            State.current_image_index += 1

        time.sleep(.5)
        State.recording_progress = 0
        State.current_recording_task = "Resetting attributes and notifying you..."
        try:
            send_text_to_whatsapp("Your recording is done!")
        except Exception as e:
            traceback.print_exc()
            ## print in yellow
            print(f"{Fore.YELLOW}The error above occured while trying to send whatsapp message{Fore.RESET}")
            
        State.start_motor_and_prepare_recording_running = False
        State.recording = False
        State.leds.all_on()
        try:
            State.camera.Close()
        except AttributeError:
            pass

async def respond(websocket):
    try:
        async for msg in websocket:
            for _ in range(20):
                if create_progress_response() != msg:
                    break
                time.sleep(.1)
                
            await websocket.send(create_progress_response())
    except (websockets.exceptions.ConnectionClosedError, websockets.exceptions.ConnectionClosedOK) as e:
        print(e)

async def websocket_coro():
    async with serve(respond, "0.0.0.0", 65432):
        await asyncio.Future()

def start_ws():
    asyncio.run(websocket_coro())
    

if __name__ == "__main__":
    os.chdir(get_path())
    th = threading.Thread(target=start_motor_and_prepare_recording)
    th.start()
    threading.Thread(target=start_ws).start()
    flask_app.app.run(host="0.0.0.0", port=80, threaded=True)
