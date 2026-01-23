


import os
import time
import subprocess
from PIL import Image
def send_command(process, command):
    process.stdin.write(command + "\n")
    process.stdin.flush()
def get_screenshot(process,test_name):
    image_path = os.path.join(os.getcwd(),f"screenshot\\screenshot.png")
    send_command(process, f'screenshot {image_path}')
    time.sleep(2)
    save_path = os.path.join(os.getcwd(),f"{test_name}\\{time.time()}.jpg")
    image = Image.open(image_path)
    image.convert("RGB").save(save_path, "JPEG")
    os.remove(image_path)
    return save_path
def tap(process, x, y):
    send_command(process, f'tap {x} {y}')
def type(text):
    text = text.replace("\\n", "_").replace("\n", "_")
    for char in text:
        if char == ' ':
            command = f"adb shell input text %s"
            subprocess.run(command, capture_output=True, text=True, shell=True)
        elif char == '_':
            command = f"adb shell input keyevent 66"
            subprocess.run(command, capture_output=True, text=True, shell=True)
        elif 'a' <= char <= 'z' or 'A' <= char <= 'Z' or char.isdigit():
            command = f"adb shell input text {char}"
            subprocess.run(command, capture_output=True, text=True, shell=True)
        elif char in '-.,!?@\'°/:;()':
            command =f"adb shell input text \"{char}\""
            subprocess.run(command, capture_output=True, text=True, shell=True)
        else:
            command =f"adb shell am broadcast -a ADB_INPUT_TEXT --es msg \"{char}\""
            subprocess.run(command, capture_output=True, text=True, shell=True)


def home(process):
    send_command(process, 'keycode home')