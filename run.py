#conda activate test123
#D:\Andriod\SDK\platform-tools> adb forward tcp:5277 tcp:5277
import time
import copy
import torch
import shutil
from PIL import Image
import cv2
import threading
import re

from MobileAgent.api import inference_chat
from MobileAgent.text_localization import ocr
from MobileAgent.icon_localization import det
from MobileAgent.controller import get_screenshot, tap,type, home,send_command
from MobileAgent.prompt import get_action_prompt, get_evaluate_prompt,get_evaluate_prompt2
from MobileAgent.chat import init_action_chat, init_evaluate_chat,add_response, \
    add_response_two_image, ask_gpt4

from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from modelscope import snapshot_download, AutoModelForCausalLM, AutoTokenizer, GenerationConfig
from dashscope import MultiModalConversation
import dashscope
import concurrent

import subprocess
import os
####################################### Edit your Setting #########################################
# Your test app input in prompt.py AND here
#app_type:1media 2messaging 3navigation 4POI 5IOT （6video 7games 8browsers）6weather

app_type=1
test_name="patreon"



#将字符串格式和时间格式互换
a=time.localtime()
#时间转换为字符串（格式可以查表）
if not os.path.exists(test_name):
    os.mkdir(test_name)
else:
    shutil.rmtree(test_name)
    os.mkdir(test_name)
with open(f'.\\{test_name}\chat.txt', 'a') as file:
    file.write(time.strftime("%Y--%m--%d %H:%M:%S\n", a))
chat_file = open(f'.\\{test_name}\chat.txt', "a")  # 打开文件作为交互显示

# 临时文件夹和截图文件夹
temp_file = "temp"  # 临时文件夹路径
screenshot = "screenshot"  # 截图文件夹路径

# 如果临时文件夹不存在，则创建该文件夹；否则先删除该文件夹及其内容，然后重新创建
if not os.path.exists(temp_file):
    os.mkdir(temp_file)
else:
    shutil.rmtree(temp_file)
    os.mkdir(temp_file)

# 如果截图文件夹不存在，则创建该文件夹
if not os.path.exists(screenshot):
    os.mkdir(screenshot)

#os.system('adb forward tcp:5277 tcp:5277')
process = subprocess.Popen(["D:\\Andriod\\SDK\\extras\\google\\auto\\desktop-head-unit.exe"],
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,  # 这里合并stderr到stdout
                           text=True,
                           universal_newlines=True,
                           bufsize=1)
#app_type:1media 2messaging 3navigation 4POI 5IOT 6video 7games 8browsers
num=0
match app_type: #点击链规则数量
    case 1:  # Media
        num = 1
    case 2:  # messaging
        num = 5
    case 3:  # Navigation
        num = 3
    case 4 :  # POI
        num = 1
    case 5:  #IOT
        num = 1
    case 6: #weather【待完善】
        num= 3

# Your GPT-4o API URL
API_url = "https://api.xty.app/v1"

# Your GPT-4o API Token
token = ""

# Choose between "api" and "local". api: use the qwen api. local: use the local qwen checkpoint
caption_call_method = "api"

#https://bailian.console.aliyun.com/#/model-market/detail/qwen-vl-plus
# Choose between "qwen-vl-plus" and "qwen-vl-max" if use api method. Choose between "qwen-vl-chat" and "qwen-vl-chat-int4" if use local method.
caption_model = "qwen-vl-plus"

# If you choose the api caption call method, input your Qwen api here
qwen_api = ""

# You can add operational knowledge to help Agent operate more accurately.
add_info = "If you want to tap an icon of an app, use the action \"tap\". If you want to exit an app, use the action \"Home\"\n"

###################################################################################################

def pic_matching(image1_path, image2_path):
    img1 = cv2.imread(image1_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(image2_path, cv2.IMREAD_GRAYSCALE)
    # 使用ORB检测特征点
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)
    # 创建BFMatcher对象
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    # 匹配描述符
    matches = bf.match(des1, des2)
    # 根据匹配距离排序
    matches = sorted(matches, key=lambda x: x.distance)
    # 计算匹配的特征点数占两个图像中最小特征点数量的百分比
    min_total_points = min(len(kp1), len(kp2))
    matching_percentage = (len(matches) / min_total_points) * 100
    # 如果匹配的特征点占比超过90%，返回True，否则返回False
    if matching_percentage >= 85:
        return True
    else:
        return False

# 获取指定文件夹下的所有文件名
def get_all_files_in_folder(folder_path):
    file_list = []
    for file_name in os.listdir(folder_path):
        file_list.append(file_name)
    return file_list

# 裁剪图像并保存为JPEG格式。i为文件名编号。如果裁剪框的宽度或高度小于10像素，函数将返回不做任何操作
def crop(image, box, i):
    image = Image.open(image)  # 打开输入图像
    x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])  # 转换裁剪框坐标为整数
    if x1 >= x2-10 or y1 >= y2-10:  # 如果裁剪框的大小小于10像素，则不执行裁剪
        return
    cropped_image = image.crop((x1, y1, x2, y2))  # 裁剪图像
    cropped_image.save(f"./temp/{i}.jpg")  # 保存裁剪后的图像为JPEG格式

def generate_local(tokenizer, model, image_file, query):
    """
    使用本地模型生成对图像和查询的响应。
    参数：
    - tokenizer: 用于处理输入数据的tokenizer对象
    - model: 使用的模型对象
    - image_file: 输入图像的文件路径
    - query: 用户输入的查询文本

    该函数将图像和文本信息通过tokenizer进行格式化后，传递给模型进行推理，最后返回模型生成的响应。
    """
    # 使用tokenizer将图像文件和查询文本格式化为模型可以理解的输入格式
    query = tokenizer.from_list_format([
        {'image': image_file},
        {'text': query},
    ])
    # 使用模型生成响应，返回生成的文本响应和一些元数据
    response, _ = model.chat(tokenizer, query=query, history=None)
    return response

# process_image处理单张图像并生成对图像的描述或响应。调用MultiModalConversation API处理
def process_image(image, query):
    dashscope.api_key = qwen_api  # 设置API密钥，用于身份验证
    image = "file://" + image  # 转换图像路径为URL格式
    # 构建用户消息，包含图像和查询文本
    messages = [{
        'role': 'user',
        'content': [
            {'image': image},  # 图像内容
            {'text': query},   # 查询文本内容
        ]
    }]

    # 调用MultiModalConversation API进行处理，获取响应
    response = MultiModalConversation.call(model=caption_model, messages=messages)

    try:
        # 解析API响应，获取图像描述或响应文本
        response = response['output']['choices'][0]['message']['content'][0]["text"]
    except:
        # 如果发生错误，返回默认的提示信息
        response = "This is an icon."

    return response

#批量处理图像和查询文本，并生成图像的描述或响应。
def generate_api(images, query):
    icon_map = {}  # 存储图像索引与生成的响应的映射
    # 使用ThreadPoolExecutor并行处理多个图像
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # 提交每张图像的处理任务
        futures = {executor.submit(process_image, image, query): i for i, image in enumerate(images)}
        # 等待任务完成并获取每个任务的结果
        for future in concurrent.futures.as_completed(futures):
            i = futures[future]  # 获取图像索引
            time.sleep(1.5)
            response = future.result()  # 获取响应
            icon_map[i + 1] = response  # 将响应存储到字典中，索引加1
    return icon_map  # 返回所有图像的响应字典

#合并相邻的文本块，将在视觉上接近的文本块组合在一起。输入：文本块的列表，坐标列表。输出：合并后的文本，坐标列表。
def merge_text_blocks(text_list, coordinates_list):
    # 初始化合并后的文本块和坐标列表
    merged_text_blocks = []
    merged_coordinates = []
    # 对文本块按其左上角 (x1, y1) 位置进行排序，首先按 y1 排序，再按 x1 排序
    sorted_indices = sorted(range(len(coordinates_list)),
                            key=lambda k: (coordinates_list[k][1], coordinates_list[k][0]))
    sorted_text_list = [text_list[i] for i in sorted_indices]
    sorted_coordinates_list = [coordinates_list[i] for i in sorted_indices]
    # 获取排序后的文本块数量
    num_blocks = len(sorted_text_list)
    # 标记是否已经合并的文本块，初始时都没有被合并
    merge = [False] * num_blocks
    # 遍历每个文本块，尝试将其与相邻的文本块合并
    for i in range(num_blocks):
        # 如果当前文本块已经被合并，则跳过
        if merge[i]:
            continue
        # 设置当前文本块为合并组的锚点（初始为当前文本块）
        anchor = i
        # 初始化合并组，包含当前锚点的文本和坐标
        group_text = [sorted_text_list[anchor]]
        group_coordinates = [sorted_coordinates_list[anchor]]
        # 尝试将当前文本块与后续的文本块合并
        for j in range(i + 1, num_blocks):
            if merge[j]:    # 跳过本身
                continue
            # 判断当前文本块与后续文本块是否符合合并条件：
            # 1. 横坐标 (x1, x2) 相差较小，水平上足够接近。
            # 2. 当前文本块的底部与下一个文本块的顶部在垂直方向上足够接近。
            # 3. 高度差异在一个容忍范围内。
            if abs(sorted_coordinates_list[anchor][0] - sorted_coordinates_list[j][0]) < 10 and \
                    sorted_coordinates_list[j][1] - sorted_coordinates_list[anchor][3] >= -10 and \
                    sorted_coordinates_list[j][1] - sorted_coordinates_list[anchor][3] < 30 and \
                    abs(sorted_coordinates_list[anchor][3] - sorted_coordinates_list[anchor][1] - (
                            sorted_coordinates_list[j][3] - sorted_coordinates_list[j][1])) < 10:
                # 如果符合条件，则将后续文本块加入合并组
                group_text.append(sorted_text_list[j])
                group_coordinates.append(sorted_coordinates_list[j])
                # 标记当前文本块已被合并
                merge[anchor] = True
                # 更新锚点为当前合并的文本块
                anchor = j
                merge[anchor] = True

        # 合并后的文本块内容
        merged_text = "\n".join(group_text)
        # 合并后的边界框坐标：最左边的 x1，最上面的 y1，最右边的 x2，最下面的 y2
        min_x1 = min(group_coordinates, key=lambda x: x[0])[0]
        min_y1 = min(group_coordinates, key=lambda x: x[1])[1]
        max_x2 = max(group_coordinates, key=lambda x: x[2])[2]
        max_y2 = max(group_coordinates, key=lambda x: x[3])[3]
        # 将合并后的文本和坐标添加到结果列表中
        merged_text_blocks.append(merged_text)
        merged_coordinates.append([min_x1, min_y1, max_x2, max_y2])
    # 返回合并后的文本块和坐标
    return merged_text_blocks, merged_coordinates

def is_overlapping(a, b):
    """
    判断坐标范围a和b是否有重叠。
    a和b的坐标格式为 [x1, y1, x2, y2]。
    """
    return not (a[2] < b[0] or a[3] < b[1] or a[0] > b[2] or a[1] > b[3])

def merge_coordinates(icons):
    """
    合并图标坐标，直到没有重叠关系。
    删去边栏的操作x<600 and y>400
    """
    merged_icons = icons.copy()
    # 标志是否有合并发生
    merged = True
    #s=0
    while merged:
        # print(merged_icons)
        # s=s+1
        merged = False
        to_remove = []
        to_add = []
        # 检查每一对图标是否有重叠
        for i in range(len(merged_icons)):
            for j in range(i + 1, len(merged_icons)):
                icon_a = merged_icons[i]
                icon_b = merged_icons[j]
                if is_overlapping(icon_a['coordinates'], icon_b['coordinates']):
                    # print(f'{s}:{len(merged_icons)},{i},{j}\n{icon_a["coordinates"]},{icon_b["coordinates"]}')
                    # 合并两个图标
                    new_coordinates = [
                        min(icon_a['coordinates'][0], icon_b['coordinates'][0]),  # x1
                        min(icon_a['coordinates'][1], icon_b['coordinates'][1]),  # y1
                        max(icon_a['coordinates'][2], icon_b['coordinates'][2]),  # x2
                        max(icon_a['coordinates'][3], icon_b['coordinates'][3])  # y2
                    ]
                    new_text = icon_a['text'] + " " + icon_b['text']
                    # 合并后的新图标
                    new_icon = {'coordinates': new_coordinates, 'text': new_text}
                    # 删除两个已合并的图标
                    if j not in to_remove:
                        to_remove.append(j)
                    if i not in to_remove:
                        to_remove.append(i)
                    if to_add==[]:
                        to_add.append(new_icon)
                    # 添加合并后的新图标
                    elif all(new_icon['coordinates'] != icon['coordinates'] for icon in to_add):
                        to_add.append(new_icon)
                    merged = True
        # 删除重叠图标并添加新的合并图标
        for idx in sorted(to_remove, reverse=True):
            # print(f"{idx}del")
            del merged_icons[idx]
        # 添加新合并的图标
        merged_icons.extend(to_add)
        # print(to_add)
        # os.system("pause")

    merged_icons=[item for item in merged_icons if not (item['coordinates'][0] < 600 and item['coordinates'][1] > 400)]
    return merged_icons


def draw_bounds(image, perception_infos):
    num = 0
    for perception_info in perception_infos:
        x1, y1, x2, y2 = perception_info["coordinates"]
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)  # red color
        text_size = cv2.getTextSize(str(num), cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
        text_w, text_h = text_size
        cv2.rectangle(image, (x1, y1 - 30), (x1 + text_w, y1), (0, 0, 255), -1)  # Red background
        # Draw the text with white font color
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        font_color = (255, 255, 255)  # White color
        cv2.putText(image, str(num), (x1, y1 - 5), font, font_scale, font_color, 2)
        num += 1
    return image

def get_perception_infos(process):
    """
    该函数从指定的手机截图中提取感知信息，包括文本、图标及其对应的位置信息，并返回这些信息。
    返回：
    - perception_infos: 包含文本和图标信息的字典列表，每个字典包括 'text' 和 'coordinates' 键。
    - width: 截图的宽度。height: 截图的高度。
    """
    # 如果临时文件夹不存在，则创建该文件夹；否则先删除该文件夹及其内容，然后重新创建
    if not os.path.exists(temp_file):
        os.mkdir(temp_file)
    else:
        shutil.rmtree(temp_file)
        os.mkdir(temp_file)
    # 步骤1: 获取手机屏幕截图
    screenshot_file=get_screenshot(process,test_name)
    # 步骤2: 获取截图的尺寸（宽度和高度）
    width, height = Image.open(screenshot_file).size
    # 步骤3: 使用 OCR 识别截图中的文本及其坐标
    text, coordinates = ocr(screenshot_file, ocr_detection, ocr_recognition)
    # 步骤4: 合并相邻的文本块
    text, coordinates = merge_text_blocks(text, coordinates)    #最左边的 x1，最上面的 y1，最右边的 x2，最下面的 y2

    # 步骤6: 创建感知信息列表，包含文本和坐标
    perception_infos = []
    for i in range(len(coordinates)):
        perception_info = {"coordinates": coordinates[i],"text": "text: " + text[i]}
        perception_infos.append(perception_info)
    # 步骤7: 使用目标检测模型识别截图中的图标
    coordinates = det(screenshot_file, "icon", groundingdino_model)
    # 步骤8: 将识别到的图标信息添加到感知信息列表中
    for i in range(len(coordinates)):
        perception_info = {"coordinates": coordinates[i],"text": "icon"}
        perception_infos.append(perception_info)
    # 步骤9: 获取所有的图标坐标，并裁剪出图标的区域
    image_box = []
    image_id = []
    for i in range(len(perception_infos)):
        if perception_infos[i]['text'] == 'icon':
            image_box.append(perception_infos[i]['coordinates'])
            image_id.append(i)
    # 步骤10: 对每个图标进行裁剪，并保存到临时文件夹
    for i in range(len(image_box)):
        crop(screenshot_file, image_box[i], image_id[i])
    # 步骤11: 获取裁剪后的图标图片文件
    images = get_all_files_in_folder(temp_file)
    if len(images) > 0:
        # 对图标图片按照文件名排序
        images = sorted(images, key=lambda x: int(x.split('/')[-1].split('.')[0]))
        image_id = [int(image.split('/')[-1].split('.')[0]) for image in images]
        # 步骤12: 生成图标的描述
        icon_map = {}
        prompt = 'This image is an icon from a phone screen. Please briefly describe the icon function or meanings within 8 words.'
        # 本地生成图标描述
        if caption_call_method == "local":
            for i in range(len(images)):
                image_path = os.path.join(temp_file, images[i])
                icon_width, icon_height = Image.open(image_path).size
                # 判断图标是否太大或太小，忽略不合适的图标
                if icon_height > 0.8 * height or icon_width * icon_height > 0.2 * width * height:
                    des = "None"
                else:
                    des = generate_local(tokenizer, model, image_path, prompt)
                icon_map[i + 1] = des
        else:
            # 使用API生成图标描述
            for i in range(len(images)):
                images[i] = os.path.join(temp_file, images[i])
            icon_map = generate_api(images, prompt)
        # 步骤13: 将生成的图标描述更新到感知信息中
        for i, j in zip(image_id, range(1, len(image_id) + 1)):

            if icon_map.get(j):
                perception_infos[i]['text'] = "icon: " + icon_map[j]

        merged_icons = merge_coordinates(perception_infos)
        #perception_infos=ask_gpt4(merged_icons,token)
        perception_infos=merged_icons

    # 步骤14: 将感知信息中的坐标更新为中心点的整数坐标，框出文本并标号,设置文本样式和字体大小
    image = cv2.imread(screenshot_file)
    merged_icons = merge_coordinates(perception_infos)
    image_with_bounds = draw_bounds(image, merged_icons)
    output_image_path = screenshot_file[: -3] + "png"
    cv2.imwrite(output_image_path, image_with_bounds)
    for i in range(len(perception_infos)):
        perception_infos[i]['coordinates']= [(perception_infos[i]['coordinates'][0] + perception_infos[i]['coordinates'][2]) / 2,(perception_infos[i]['coordinates'][1] +perception_infos[i]['coordinates'][3]) / 2]

    # 步骤15: 返回感知信息、截图的宽度和高度
    return perception_infos, width, height,output_image_path

#重启应用，回到先前状态
def check_relaunch():
    # 从开机状态home页面OCR打开app
    home(process)
    time.sleep(5)
    perception_infos, width, height,screenshot1 =get_perception_infos(process)
    x,y=perception_infos[0]['coordinates']
    for i in range(len(perception_infos)):  # 遍历所有感知信息查找键盘
        if test_name.lower() in perception_infos[i]['text'].lower():
            x, y = perception_infos[i]['coordinates']
            tap(process, int(x), int(y))
            time.sleep(5)
            break
    # app中OCR点击图标改变状态
    perception_infos, width, height, screenshot2 = get_perception_infos(process)
    after_shot=screenshot2
    for perception_info in perception_infos:  # 遍历所有感知信息查找clickable图标
        x2, y2 = perception_info['coordinates']
        if y2<=400:  #去除底边栏
            tap(process, int(x2), int(y2))
            time.sleep(5)
            after_shot=get_screenshot(process,test_name)
            if (not pic_matching(screenshot2[: -3] + "jpg",after_shot)): #如果改变了状态，操作前后截图不同
                break

    # home再打开app页面
    home(process)
    time.sleep(3)
    home(process)
    time.sleep(3)
    tap(process, int(x), int(y))
    time.sleep(3)
    # 对比页面state
    check_shot = get_screenshot(process,test_name)
    if (pic_matching(check_shot, after_shot)):  # 如果重启前后截图相同
        return  True
    else:
        return False


'''#启动应用的自动播放检测
#命令行输入keycode media_play/pause通过返回值进行判断
#检测是否有声音
def check_autoplay():
    send_command(process, f'keycode media_play')
    time.sleep(5)
    send_command(process, f'keycode media_pause')
    time.sleep(3)
    #开启对应应用.从开机状态home页面OCR打开app
    home(process)
    time.sleep(5)
    perception_infos, width, height, screenshot1 = get_perception_infos(process)
    x, y = perception_infos[0]['coordinates']
    for i in range(len(perception_infos)):
        if test_name.lower() in perception_infos[i]['text'].lower():
            x, y = perception_infos[i]['coordinates']
            tap(process, int(x), int(y))
            time.sleep(5)
            break
    send_command(process, f'keycode media_play_pause')
    time.sleep(10)
    if output_stack and "start" in output_stack[-1]:
        return True
    print(output_stack[-1])
    return False

# 定义一个读取输出的函数
def read_output(process):
    while True:
        output = process.stdout.readline()
        if output == '':
            break
        output_stack.append(output)  # 将输出压入栈中
        # print(output, end='')

# 创建一个栈，用于存储输出
output_stack = []
time.sleep(5)
# 开始一个线程来读取输出，这样我们就不会阻塞主线程
output_thread = threading.Thread(target=read_output, args=(process,))
output_thread.daemon = True
output_thread.start()
'''


send_command(process,'location lat long NAN NAN 50 NAN') #模拟驾驶状态

### Load caption model ###
device = "cuda"  # 设置设备为GPU（如果可用）
torch.manual_seed(1234)  # 设置随机种子，确保结果可复现

# 根据所选的caption调用方法加载相应的模型
if caption_call_method == "local":
    # 如果选择本地调用模型
    if caption_model == "qwen-vl-chat":
        # 加载 "Qwen-VL-Chat" 模型
        model_dir = snapshot_download('qwen/Qwen-VL-Chat', revision='v1.1.0')  # 从远程下载模型快照
        model = AutoModelForCausalLM.from_pretrained(model_dir, device_map=device, trust_remote_code=True).eval()  # 加载预训练模型到指定设备并设置为评估模式
        model.generation_config = GenerationConfig.from_pretrained(model_dir, trust_remote_code=True)  # 加载生成配置
    elif caption_model == "qwen-vl-chat-int4":
        # 加载 "Qwen-VL-Chat-Int4" 模型
        qwen_dir = snapshot_download("qwen/Qwen-VL-Chat-Int4", revision='v1.0.0')  # 下载模型
        model = AutoModelForCausalLM.from_pretrained(qwen_dir, device_map=device, trust_remote_code=True, use_safetensors=True).eval()  # 加载Int4版本的模型
        model.generation_config = GenerationConfig.from_pretrained(qwen_dir, trust_remote_code=True, do_sample=False)  # 配置生成设置（禁用采样）
    else:
        # 如果本地模型选择不正确，打印错误信息并退出
        print("If you choose local caption method, you must choose the caption model from \"Qwen-vl-chat\" and \"Qwen-vl-chat-int4\"")
        exit(0)
    # 加载分词器
    tokenizer = AutoTokenizer.from_pretrained(qwen_dir, trust_remote_code=True)
elif caption_call_method == "api":
    # 如果选择API调用，暂时未实现相关代码（留空）
    pass
else:
    # 如果未选择有效的调用方法，打印错误信息并退出
    print("You must choose the caption model call function from \"local\" and \"api\"")
    exit(0)


### Load ocr and icon detection model ###
# 加载图像识别和OCR模型

# 下载GroundingDINO模型，用于图像目标检测
groundingdino_dir = snapshot_download('AI-ModelScope/GroundingDINO', revision='v1.0.0')
groundingdino_model = pipeline('grounding-dino-task', model=groundingdino_dir)  # 加载目标检测模型

# 加载OCR检测和识别模型
ocr_detection = pipeline(Tasks.ocr_detection, model='damo/cv_resnet18_ocr-detection-line-level_damo')  # 用于检测OCR文本行
ocr_recognition = pipeline(Tasks.ocr_recognition, model='damo/cv_convnextTiny_ocr-recognition-document_damo')  # 用于识别OCR文本内容

#检查重启规则
#EP-2 When the app is relaunched from the home screen, the app must restore the app state as closely as possible to the previous state.
if check_relaunch():
    print("EP-2 is OK.")
    chat_file.write(f"EP-2 is OK.\n")
else:
    print("EP-2 is not ok.")
    chat_file.write(f"EP-2 is not OK.\n")

# if app_type==1:
#     if check_autoplay():
#         print("MA-1 is OK.")
#         chat_file.write(f"MA-1 is OK.\n")
#     else:
#         print("MA-1 is not ok.")
#         chat_file.write(f"MA-1 is not OK.\n")

# 初始化记录历史的变量
thought_history = []  # 思维历史记录，用于存储模型的思考过程
summary_history = []  # 总结历史记录，用于存储每次对话后的总结
action_history = []  # 动作历史记录，用于存储模型的动作
summary = ""  # 当前对话的总结
action = ""  # 当前对话的行动
memory = ""  # 模型的记忆，任务进展
insight = ""  # 模型的洞察力




stop_flag = False
error_flag = False
keyboard = False  # 默认没有虚拟键盘
screenshot_file=""
i=1 #用于指示点击链检查规则
while i<=num: # 开始一个循环，直到检查完规则
    #print(f'num:i={i},num={num}')
    stop_flag = False
    iter = 0  # 初始化迭代计数器

    while not stop_flag:  # 开始一个无限循环，直到遇到“Stop”指令或者iter询问操作7次
        #print(f'flag:i={i},num={num}')
        iter += 1  # 每次循环迭代时计数器递增
        if iter == 1:  # 只有在第一次迭代时执行以下代码块
            perception_infos, width, height,screenshot_file = get_perception_infos(process)  # 获取设备的感知信息，包括宽高
            # 删除临时文件夹
            if os.path.exists(temp_file):  # 确保文件夹存在
                shutil.rmtree(temp_file)  # 删除
            # 重新创建临时文件夹
            os.makedirs(temp_file, exist_ok=True)  # 创建临时文件夹，exist_ok=True 表示文件夹已存在时不报错
            for perception_info in perception_infos:  # 遍历所有感知信息查找键盘
                if 'Keyboard' in perception_info['text'] or 'keyboard' in perception_info['text'] or '键盘' in perception_info['text']:  # 如果感知信息包含 "ADB Keyboard" 字样，认为设备上有虚拟键盘
                    chat_file.write(f"keyboard:{str(perception_info)}")
                    print(f"keyboard:{str(perception_info)}")
                    keyboard = True  # 标记键盘存在
                    break  # 找到虚拟键盘后停止循环
        elif iter == 8: #每个点击链最多操作7次
            break

        # 获取action agent的prompt，生成下一步的行动指令
        prompt_action = get_action_prompt(i,perception_infos, width, height, keyboard, summary_history,
                                          action_history, add_info, memory)
        # 初始化聊天动作对象，角色设定
        chat_action = init_action_chat()
        chat_action = add_response("user", prompt_action, chat_action, screenshot_file)
        #os.system(f"copy {screenshot_file} screenshot/{time.time()}.jpg")
        # 打印当前决策状态和输出
        status = "#" * 50 + " Decision " + "#" * 50
        print(status)
        # 调用推理接口，生成指导决策output_action
        output_action = inference_chat(chat_action, API_url, token)

        # index = chat_action.find("{'type': 'image_url'")
        chat_file.write("action-input: "+str(re.sub(r'\{\'type\': \'image_url\'[^}]*\}', '', str(chat_action))))
        chat_file.write("action-output: "+str(output_action))
        # 从推理结果中解析出实际动作
        action = output_action.split("### Action ###")[-1].split("### Operation ###")[0].replace("\n", " ").replace(
            "  ", " ").strip()
        #chat_action = add_response("assistant", output_action, chat_action)
        print('#' * len(status))

        if "Tap" in action:
            number = int(action.split("(")[-1].split(")")[0]) # 将标号转为整数
            x,y=perception_infos[number]['coordinates']
            tap(process, int(x), int(y))

        elif "Type" in action:
            if "(text)" not in action:  # 如果行动中没有明确指定文本
                text = action.split("(")[-1].split(")")[0]  # 以括号为界限提取文本内容
            else:  # 如果行动中包含 "(text)"
                text = action.split(" \"")[-1].split("\"")[0]  # 以双引号为界限提取文本内容
            text.replace("Type ", "")
            type(text)  # 执行文本输入操作

        elif "Home" in action:
            home(process)

        time.sleep(5)  # 暂停5秒，确保系统稳定或等待上一操作完成
        # 备份当前的感知信息、截图和键盘状态
        last_perception_infos = copy.deepcopy(perception_infos)  # 深拷贝（复制而非引用）当前感知信息，以便后续比较
        last_screenshot_file = screenshot_file  # 设置上一个截图的路径
        last_keyboard = keyboard  # 保存当前键盘状态
        last_action=action
        # 获取新的感知信息和屏幕尺寸
        perception_infos, width, height, screenshot_file = get_perception_infos(process)
        # 清理临时文件夹并重新创建
        shutil.rmtree(temp_file)
        os.mkdir(temp_file)
        count=0
        while pic_matching(last_screenshot_file[: -3] + "jpg",screenshot_file[: -3] + "jpg"):
            count+=1
            if count>3:
                stop_flag = True
                break
            #操作前后截图特征点匹配95%，无效操作
            error_flag = True
            perception_infos = copy.deepcopy(last_perception_infos)  # 深拷贝（复制而非引用）当前感知信息，以便后续比较
            screenshot_file = last_screenshot_file  # 设置上一个截图的路径
            keyboard = last_keyboard  # 保存当前键盘状态
            #再次询问，给出新指导
            prompt_action = get_action_prompt(i, perception_infos, width, height, keyboard, summary_history,
                                              action_history, add_info, memory,error_flag,last_action,False)
            # 初始化聊天动作对象，角色设定
            chat_action = init_action_chat()
            chat_action = add_response("user", prompt_action, chat_action, screenshot_file)
            #os.system(f"copy {screenshot_file} screenshot/{time.time()}.jpg")
            # 打印当前决策状态和输出
            status = "#" * 50 + " Decision " + "#" * 50
            print(status)
            # 调用推理接口，生成指导决策output_action
            output_action = inference_chat(chat_action, API_url, token)

            # index = chat_action.find("{'type': 'image_url'")
            chat_file.write("action-input: " + str(re.sub(r'\{\'type\': \'image_url\'[^}]*\}', '', str(chat_action))))
            chat_file.write("action-output: " + str(output_action))
            # 从推理结果中解析出实际动作
            action = output_action.split("### Action ###")[-1].split("### Operation ###")[0].replace("\n", " ").replace(
                "  ", " ").strip()
            print('#' * len(status))
            if "Tap" in action:
                number = int(action.split("(")[-1].split(")")[0])  # 将标号转为整数
                x, y = perception_infos[number]['coordinates']
                tap(process, int(x), int(y))
            elif "Type" in action:
                if "(text)" not in action:  # 如果行动中没有明确指定文本
                    text = action.split("(")[-1].split(")")[0]  # 以括号为界限提取文本内容
                else:  # 如果行动中包含 "(text)"
                    text = action.split(" \"")[-1].split("\"")[0]  # 以双引号为界限提取文本内容
                text.replace("Type ", "")
                type(text)  # 执行文本输入操作
            elif "Home" in action:
                home(process)
            time.sleep(3)  # 暂停3秒，确保系统稳定或等待上一操作完成
            #截图再判断
            # 备份当前的感知信息、截图和键盘状态
            last_perception_infos = copy.deepcopy(perception_infos)  # 深拷贝（复制而非引用）当前感知信息，以便后续比较
            last_screenshot_file = screenshot_file  # 设置上一个截图的路径
            last_keyboard = keyboard  # 保存当前键盘状态
            last_action+=f", {action}"
            # 获取新的感知信息和屏幕尺寸
            perception_infos, width, height, screenshot_file = get_perception_infos(process)

        thought = output_action.split("### Thought ###")[-1].split("### Action ###")[0].replace("\n", " ").replace(":",
                                                                                                                   "").replace(
            "  ", " ").strip()
        summary = output_action.split("### Operation ###")[-1].split("### Summary ###")[0].replace("\n", " ").replace(
            "  ", " ").strip()
        memory = output_action.split("### Summary ###")[-1].replace("\n", " ").replace("  ", " ").strip()

        # 假设默认没有虚拟键盘，遍历感知信息来判断
        keyboard = False
        for perception_info in perception_infos:
            if 'Keyboard' in perception_info['text'] or 'keyboard' in perception_info['text'] or '键盘' in perception_info['text']:  # 如果感知信息中有ADB虚拟键盘的标记，说明设备上有虚拟键盘
                keyboard = True  # 设置键盘存在标志
                chat_file.write(f"keyboard:{str(perception_info)}")
                print(f"keyboard:{str(perception_info)}")
                break  # 找到键盘后退出循环
        # 判断截图是否违规
        # 生成evaluate agent的prompt，包含了当前的和上一个状态（如截图、感知信息等）
        prompt_evaluate = get_evaluate_prompt(i,last_perception_infos, perception_infos, width, height,
                                            last_keyboard, keyboard, summary, action, add_info,False)
        chat_evaluate = init_evaluate_chat()  # 初始化evaluate agent，角色设定
        chat_evaluate = add_response_two_image("user", prompt_evaluate, chat_evaluate,
                                              [last_screenshot_file, screenshot_file])  # 将prompt和截图*2添加到日志中
        # 打印状态和输出结果
        status = "#" * 50 + " Evaluation " + "#" * 50
        print(status)
        output_evaluate = inference_chat(chat_evaluate,  API_url, token)
        #chat_file.write("evaluate-input: "+str(chat_evaluate))
        chat_file.write("evaluate-input: " + str(re.sub(r'\{\'type\': \'image_url\'[^}]*\}', '', str(chat_evaluate))))
        chat_file.write("evaluate-output: " + str(output_evaluate))
        #evaluate = output_evaluate.split("### Thought ###")[-1].replace("\n", " ").strip()  # 从输出中提取反思部分
        chat_evaluate = add_response("assistant", output_evaluate, chat_evaluate)  # 将机器人的反思回应添加到聊天记录
        print('#' * len(status))

        if "Stop" in output_evaluate:  # 任务结束
            stop_flag=True  # 结束循环
            #print(f'stop:i={i},num={num}')

        # 输出违规情况
        #if 'Find non-compliance' in output_evaluate:
        print(f"{screenshot_file} - {output_evaluate}")
        chat_file.write(f"{screenshot_file} - {output_evaluate}")
        # else:
        #     chat_file.write(f"{screenshot_file} - {evaluate}")
        '''if 'Find non-compliance' in output_evaluate:
            pattern = r'\b[A-Za-z]+-\d+\b'
            list1 = set(re.findall(pattern, output_evaluate))

            prompt_evaluate2 = get_evaluate_prompt2(i, last_perception_infos, perception_infos, width, height,
                                                    last_keyboard, keyboard, summary, action, add_info, True)
            chat_evaluate = init_evaluate_chat()  # 初始化evaluate agent，角色设定
            chat_evaluate = add_response_two_image("user", prompt_evaluate, chat_evaluate,
                                                   [last_screenshot_file, screenshot_file])  # 将prompt和截图*2添加到日志中
            # 打印状态和输出结果
            status = "#" * 50 + " Evaluation2 " + "#" * 50
            print(status)
            output_evaluate2 = inference_chat(chat_evaluate, API_url, token)
            # chat_file.write("evaluate-input: "+str(chat_evaluate))
            chat_file.write(
                "evaluate2-input: " + str(re.sub(r'\{\'type\': \'image_url\'[^}]*\}', '', str(chat_evaluate))))
            chat_file.write("evaluate2-output: " + str(output_evaluate))
            # evaluate = output_evaluate.split("### Thought ###")[-1].replace("\n", " ").strip()  # 从输出中提取反思部分
            chat_evaluate = add_response("assistant", output_evaluate, chat_evaluate)  # 将机器人的反思回应添加到聊天记录
            print('#' * len(status))
            list2 = set(re.findall(pattern, output_evaluate2))
            # 求交集
            intersection = list1.intersection(list2)
            if intersection:
                print("result:", intersection)
                chat_file.write("result:" + str(intersection))
            else:
                print("result: All is compiled.")
                chat_file.write(f"result:All is compiled.")'''

        thought_history.append(thought)
        summary_history.append(summary)
        action_history.append(action)
    i=i+1

iter = 0  # 初始化计数器
# free_flag=True
stop_flag=False
while not stop_flag:  # 开始一个无限循环，直到遇到“Stop”指令或者iter询问操作7次
    #print(f'flag:i={i},num={num}')
    iter += 1  # 每次循环迭代时计数器递增
    if iter == 1:  # 只有在第一次迭代时执行以下代码块
        perception_infos, width, height,screenshot_file = get_perception_infos(process)  # 获取设备的感知信息，包括宽高
        # 删除临时文件夹
        if os.path.exists(temp_file):  # 确保文件夹存在
            shutil.rmtree(temp_file)  # 删除
        # 重新创建临时文件夹
        os.makedirs(temp_file, exist_ok=True)  # 创建临时文件夹，exist_ok=True 表示文件夹已存在时不报错
        for perception_info in perception_infos:  # 遍历所有感知信息查找键盘
            if 'Keyboard' in perception_info['text'] or 'keyboard' in perception_info['text'] or '键盘' in perception_info['text']:  # 如果感知信息包含 "ADB Keyboard" 字样，认为设备上有虚拟键盘
                chat_file.write(f"keyboard:{str(perception_info)}")
                print(f"keyboard:{str(perception_info)}")
                keyboard = True  # 标记键盘存在
                break  # 找到虚拟键盘后停止循环
    elif iter == 8: #每个点击链最多操作7次
        break

    # 获取action agent的prompt，生成下一步的行动指令
    prompt_action = get_action_prompt(i,perception_infos, width, height, keyboard, summary_history,
                                      action_history, add_info, memory,False,"",True)
    # 初始化聊天动作对象，角色设定
    chat_action = init_action_chat()
    chat_action = add_response("user", prompt_action, chat_action, screenshot_file)
    #os.system(f"copy {screenshot_file} screenshot/{time.time()}.jpg")
    # 打印当前决策状态和输出
    status = "#" * 50 + " Decision " + "#" * 50
    print(status)
    # 调用推理接口，生成指导决策output_action
    output_action = inference_chat(chat_action, API_url, token)

    # index = chat_action.find("{'type': 'image_url'")
    chat_file.write("action-input: "+str(re.sub(r'\{\'type\': \'image_url\'[^}]*\}', '', str(chat_action))))
    chat_file.write("action-output: "+str(output_action))
    # 从推理结果中解析出实际动作
    action = output_action.split("### Action ###")[-1].split("### Operation ###")[0].replace("\n", " ").replace(
        "  ", " ").strip()
    #chat_action = add_response("assistant", output_action, chat_action)
    print('#' * len(status))

    if "Tap" in action:
        number = int(action.split("(")[-1].split(")")[0]) # 将标号转为整数
        x,y=perception_infos[number]['coordinates']
        tap(process, int(x), int(y))

    elif "Type" in action:
        if "(text)" not in action:  # 如果行动中没有明确指定文本
            text = action.split("(")[-1].split(")")[0]  # 以括号为界限提取文本内容
        else:  # 如果行动中包含 "(text)"
            text = action.split(" \"")[-1].split("\"")[0]  # 以双引号为界限提取文本内容
        text.replace("Type ", "")
        type(text)  # 执行文本输入操作

    elif "Home" in action:
        home(process)

    time.sleep(5)  # 暂停5秒，确保系统稳定或等待上一操作完成
    # 备份当前的感知信息、截图和键盘状态
    last_perception_infos = copy.deepcopy(perception_infos)  # 深拷贝（复制而非引用）当前感知信息，以便后续比较
    last_screenshot_file = screenshot_file  # 设置上一个截图的路径
    last_keyboard = keyboard  # 保存当前键盘状态
    last_action=action
    # 获取新的感知信息和屏幕尺寸
    perception_infos, width, height, screenshot_file = get_perception_infos(process)
    # 清理临时文件夹并重新创建
    shutil.rmtree(temp_file)
    os.mkdir(temp_file)
    count=0
    while pic_matching(last_screenshot_file[: -3] + "jpg",screenshot_file[: -3] + "jpg"):
        count+=1
        if count>3:
            stop_flag = True
            break
        #操作前后截图特征点匹配95%，无效操作
        error_flag = True
        perception_infos = copy.deepcopy(last_perception_infos)  # 深拷贝（复制而非引用）当前感知信息，以便后续比较
        screenshot_file = last_screenshot_file  # 设置上一个截图的路径
        keyboard = last_keyboard  # 保存当前键盘状态
        #再次询问，给出新指导
        prompt_action = get_action_prompt(i, perception_infos, width, height, keyboard, summary_history,
                                          action_history, add_info, memory,error_flag,last_action,True)
        # 初始化聊天动作对象，角色设定
        chat_action = init_action_chat()
        chat_action = add_response("user", prompt_action, chat_action, screenshot_file)
        #os.system(f"copy {screenshot_file} screenshot/{time.time()}.jpg")
        # 打印当前决策状态和输出
        status = "#" * 50 + " Decision " + "#" * 50
        print(status)
        # 调用推理接口，生成指导决策output_action
        output_action = inference_chat(chat_action, API_url, token)

        # index = chat_action.find("{'type': 'image_url'")
        chat_file.write("action-input: " + str(re.sub(r'\{\'type\': \'image_url\'[^}]*\}', '', str(chat_action))))
        chat_file.write("action-output: " + str(output_action))
        # 从推理结果中解析出实际动作
        action = output_action.split("### Action ###")[-1].split("### Operation ###")[0].replace("\n", " ").replace(
            "  ", " ").strip()
        print('#' * len(status))
        if "Tap" in action:
            number = int(action.split("(")[-1].split(")")[0])  # 将标号转为整数
            x, y = perception_infos[number]['coordinates']
            tap(process, int(x), int(y))
        elif "Type" in action:
            if "(text)" not in action:  # 如果行动中没有明确指定文本
                text = action.split("(")[-1].split(")")[0]  # 以括号为界限提取文本内容
            else:  # 如果行动中包含 "(text)"
                text = action.split(" \"")[-1].split("\"")[0]  # 以双引号为界限提取文本内容
            text.replace("Type ", "")
            type(text)  # 执行文本输入操作
        elif "Home" in action:
            home(process)
        time.sleep(3)  # 暂停3秒，确保系统稳定或等待上一操作完成
        #截图再判断
        # 备份当前的感知信息、截图和键盘状态
        last_perception_infos = copy.deepcopy(perception_infos)  # 深拷贝（复制而非引用）当前感知信息，以便后续比较
        last_screenshot_file = screenshot_file  # 设置上一个截图的路径
        last_keyboard = keyboard  # 保存当前键盘状态
        last_action+=f", {action}"
        # 获取新的感知信息和屏幕尺寸
        perception_infos, width, height, screenshot_file = get_perception_infos(process)

    thought = output_action.split("### Thought ###")[-1].split("### Action ###")[0].replace("\n", " ").replace(":",
                                                                                                               "").replace(
        "  ", " ").strip()
    summary = output_action.split("### Operation ###")[-1].split("### Summary ###")[0].replace("\n", " ").replace(
        "  ", " ").strip()
    memory = output_action.split("### Summary ###")[-1].replace("\n", " ").replace("  ", " ").strip()

    # 假设默认没有虚拟键盘，遍历感知信息来判断
    keyboard = False
    for perception_info in perception_infos:
        if 'Keyboard' in perception_info['text'] or 'keyboard' in perception_info['text'] or '键盘' in perception_info['text']:  # 如果感知信息中有ADB虚拟键盘的标记，说明设备上有虚拟键盘
            keyboard = True  # 设置键盘存在标志
            chat_file.write(f"keyboard:{str(perception_info)}")
            print(f"keyboard:{str(perception_info)}")
            break  # 找到键盘后退出循环
    # 判断截图是否违规
    # 生成evaluate agent的prompt，包含了当前的和上一个状态（如截图、感知信息等）
    prompt_evaluate = get_evaluate_prompt(i,last_perception_infos, perception_infos, width, height,
                                        last_keyboard, keyboard, summary, action, add_info,True)
    chat_evaluate = init_evaluate_chat()  # 初始化evaluate agent，角色设定
    chat_evaluate = add_response_two_image("user", prompt_evaluate, chat_evaluate,
                                          [last_screenshot_file, screenshot_file])  # 将prompt和截图*2添加到日志中
    # 打印状态和输出结果
    status = "#" * 50 + " Evaluation " + "#" * 50
    print(status)
    output_evaluate = inference_chat(chat_evaluate,  API_url, token)
    #chat_file.write("evaluate-input: "+str(chat_evaluate))
    chat_file.write("evaluate-input: " + str(re.sub(r'\{\'type\': \'image_url\'[^}]*\}', '', str(chat_evaluate))))
    chat_file.write("evaluate-output: " + str(output_evaluate))
    #evaluate = output_evaluate.split("### Thought ###")[-1].replace("\n", " ").strip()  # 从输出中提取反思部分
    chat_evaluate = add_response("assistant", output_evaluate, chat_evaluate)  # 将机器人的反思回应添加到聊天记录
    print('#' * len(status))

    if "Stop" in output_evaluate:  # 任务结束
        stop_flag=True  # 结束循环
        #print(f'stop:i={i},num={num}')

    # 输出违规情况

    print(f"{screenshot_file} - {output_evaluate}")
    chat_file.write(f"{screenshot_file} - {output_evaluate}")
    '''if 'Find non-compliance' in output_evaluate:
        pattern = r'\b[A-Za-z]+-\d+\b'
        list1 = set(re.findall(pattern, output_evaluate))

        prompt_evaluate2 = get_evaluate_prompt2(i, last_perception_infos, perception_infos, width, height,
                                              last_keyboard, keyboard, summary, action, add_info, True)
        chat_evaluate = init_evaluate_chat()  # 初始化evaluate agent，角色设定
        chat_evaluate = add_response_two_image("user", prompt_evaluate, chat_evaluate,
                                               [last_screenshot_file, screenshot_file])  # 将prompt和截图*2添加到日志中
        # 打印状态和输出结果
        status = "#" * 50 + " Evaluation2 " + "#" * 50
        print(status)
        output_evaluate2 = inference_chat(chat_evaluate, API_url, token)
        # chat_file.write("evaluate-input: "+str(chat_evaluate))
        chat_file.write("evaluate2-input: " + str(re.sub(r'\{\'type\': \'image_url\'[^}]*\}', '', str(chat_evaluate))))
        chat_file.write("evaluate2-output: " + str(output_evaluate))
        # evaluate = output_evaluate.split("### Thought ###")[-1].replace("\n", " ").strip()  # 从输出中提取反思部分
        chat_evaluate = add_response("assistant", output_evaluate, chat_evaluate)  # 将机器人的反思回应添加到聊天记录
        print('#' * len(status))
        list2 = set(re.findall(pattern, output_evaluate2))
        # 求交集
        intersection = list1.intersection(list2)
        if intersection:
            print("result:", intersection)
            chat_file.write("result:"+str(intersection))
        else:
            print("result: All is compiled.")
            chat_file.write(f"result:All is compiled.")
'''
    thought_history.append(thought)
    summary_history.append(summary)
    action_history.append(action)

chat_file.close()  # 关闭文件
home(process)
time.sleep(5)