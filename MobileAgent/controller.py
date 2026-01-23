# get_screenshot截取设备屏幕截图并保存为JPEG格式的文件
# tap slide back home type 模拟操作事件

import os
import time
import subprocess
from PIL import Image


#定义一个发送命令并读取输出的函数
def send_command(process, command):
    process.stdin.write(command + "\n")
    process.stdin.flush()

#截取设备屏幕截图并保存为JPEG格式的文件。本地存储截图的路径"./screenshot/screenshot.jpeg"
def get_screenshot(process,test_name):
    # 定义本地存储截图的路径
    image_path = os.path.join(os.getcwd(),f"screenshot\\screenshot.png")
    send_command(process, f'screenshot {image_path}')
    time.sleep(2) #必要的
    save_path = os.path.join(os.getcwd(),f"{test_name}\\{time.time()}.jpg")
    # 打开PNG格式的截图
    image = Image.open(image_path)
    # 将截图从PNG格式转换为JPEG格式并保存
    image.convert("RGB").save(save_path, "JPEG")
    # 删除临时的PNG文件
    os.remove(image_path)
    return save_path

# tap模拟触摸事件，点击指定的屏幕坐标（x, y）
def tap(process, x, y):
    # print(f'tap {x} {y}')
    send_command(process, f'tap {x} {y}')

# type模拟键盘输入，向设备输入指定的文本。
def type(text):
    # 替换换行符为下划线（为了防止输入多个换行符导致错误）
    text = text.replace("\\n", "_").replace("\n", "_")
    for char in text:
        if char == ' ':
            # 如果是空格，模拟输入空格
            command = f"adb shell input text %s"
            subprocess.run(command, capture_output=True, text=True, shell=True)
        elif char == '_':
            # 如果是下划线（替代换行符），模拟回车键
            command = f"adb shell input keyevent 66"
            subprocess.run(command, capture_output=True, text=True, shell=True)
        elif 'a' <= char <= 'z' or 'A' <= char <= 'Z' or char.isdigit():
            # 如果是字母或数字，模拟输入该字符
            command = f"adb shell input text {char}"
            subprocess.run(command, capture_output=True, text=True, shell=True)
        elif char in '-.,!?@\'°/:;()':
            # 对于常见的标点符号，直接模拟输入
            command =f"adb shell input text \"{char}\""
            subprocess.run(command, capture_output=True, text=True, shell=True)
        else:
            # 对于其他特殊字符，使用广播命令来输入
            command =f"adb shell am broadcast -a ADB_INPUT_TEXT --es msg \"{char}\""
            subprocess.run(command, capture_output=True, text=True, shell=True)

# slide模拟滑动事件，从屏幕坐标(x1, y1)滑动到(x2, y2)。
# 删除该操作，DHU无法实现

# back模拟设备的返回按钮操作。
# def back(process):
#     send_command(process, 'keycode back')

def home(process):
# home模拟按下设备的主页按钮，返回主屏幕。
    send_command(process, 'keycode home')

