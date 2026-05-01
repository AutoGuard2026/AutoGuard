
import time
import copy
import torch
import shutil
from PIL import Image
import cv2
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



app_type=
test_name=""




a=time.localtime()
if not os.path.exists(test_name):
    os.mkdir(test_name)
else:
    shutil.rmtree(test_name)
    os.mkdir(test_name)
with open(f'.\\{test_name}\chat.txt', 'a') as file:
    file.write(time.strftime("%Y--%m--%d %H:%M:%S\n", a))
chat_file = open(f'.\\{test_name}\chat.txt', "a")


temp_file = "temp"
screenshot = "screenshot"

if not os.path.exists(temp_file):
    os.mkdir(temp_file)
else:
    shutil.rmtree(temp_file)
    os.mkdir(temp_file)

if not os.path.exists(screenshot):
    os.mkdir(screenshot)

process = subprocess.Popen(["D:\\Andriod\\SDK\\extras\\google\\auto\\desktop-head-unit.exe"],
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           text=True,
                           universal_newlines=True,
                           bufsize=1)
num=0
match app_type:
    case 1:
        num = 1
    case 2:
        num = 5
    case 3:
        num = 3
    case 4 :
        num = 1
    case 5:
        num = 1
    case 6:
        num= 3
API_url = ""
token = ""
caption_call_method = "api"
caption_model = "qwen-vl-plus"
qwen_api = ""
add_info = "If you want to tap an icon of an app, use the action \"tap\". If you want to exit an app, use the action \"Home\"\n"

def pic_matching(image1_path, image2_path):
    img1 = cv2.imread(image1_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(image2_path, cv2.IMREAD_GRAYSCALE)
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    matches = sorted(matches, key=lambda x: x.distance)
    min_total_points = min(len(kp1), len(kp2))
    matching_percentage = (len(matches) / min_total_points) * 100
    if matching_percentage >= 85:
        return True
    else:
        return False

def get_all_files_in_folder(folder_path):
    file_list = []
    for file_name in os.listdir(folder_path):
        file_list.append(file_name)
    return file_list


def crop(image, box, i):
    image = Image.open(image)
    x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
    if x1 >= x2-10 or y1 >= y2-10:
        return
    cropped_image = image.crop((x1, y1, x2, y2))
    cropped_image.save(f"./temp/{i}.jpg")

def generate_local(tokenizer, model, image_file, query):

    query = tokenizer.from_list_format([
        {'image': image_file},
        {'text': query},
    ])
    response, _ = model.chat(tokenizer, query=query, history=None)
    return response

def process_image(image, query):
    dashscope.api_key = qwen_api
    image = "file://" + image
    messages = [{
        'role': 'user',
        'content': [
            {'image': image},
            {'text': query},
        ]
    }]
    response = MultiModalConversation.call(model=caption_model, messages=messages)
    try:
        response = response['output']['choices'][0]['message']['content'][0]["text"]
    except:
        response = "This is an icon."

    return response


def generate_api(images, query):
    icon_map = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_image, image, query): i for i, image in enumerate(images)}
        for future in concurrent.futures.as_completed(futures):
            i = futures[future]
            time.sleep(1.5)
            response = future.result()
            icon_map[i + 1] = response
    return icon_map

def merge_text_blocks(text_list, coordinates_list):
    merged_text_blocks = []
    merged_coordinates = []
    sorted_indices = sorted(range(len(coordinates_list)),
                            key=lambda k: (coordinates_list[k][1], coordinates_list[k][0]))
    sorted_text_list = [text_list[i] for i in sorted_indices]
    sorted_coordinates_list = [coordinates_list[i] for i in sorted_indices]
    num_blocks = len(sorted_text_list)
    merge = [False] * num_blocks
    for i in range(num_blocks):
        if merge[i]:
            continue
        anchor = i
        group_text = [sorted_text_list[anchor]]
        group_coordinates = [sorted_coordinates_list[anchor]]
        for j in range(i + 1, num_blocks):
            if merge[j]:
                continue
            if abs(sorted_coordinates_list[anchor][0] - sorted_coordinates_list[j][0]) < 10 and \
                    sorted_coordinates_list[j][1] - sorted_coordinates_list[anchor][3] >= -10 and \
                    sorted_coordinates_list[j][1] - sorted_coordinates_list[anchor][3] < 30 and \
                    abs(sorted_coordinates_list[anchor][3] - sorted_coordinates_list[anchor][1] - (
                            sorted_coordinates_list[j][3] - sorted_coordinates_list[j][1])) < 10:
                group_text.append(sorted_text_list[j])
                group_coordinates.append(sorted_coordinates_list[j])
                merge[anchor] = True
                anchor = j
                merge[anchor] = True

        merged_text = "\n".join(group_text)
        min_x1 = min(group_coordinates, key=lambda x: x[0])[0]
        min_y1 = min(group_coordinates, key=lambda x: x[1])[1]
        max_x2 = max(group_coordinates, key=lambda x: x[2])[2]
        max_y2 = max(group_coordinates, key=lambda x: x[3])[3]
        merged_text_blocks.append(merged_text)
        merged_coordinates.append([min_x1, min_y1, max_x2, max_y2])

    return merged_text_blocks, merged_coordinates

def is_overlapping(a, b):
    return not (a[2] < b[0] or a[3] < b[1] or a[0] > b[2] or a[1] > b[3])

def merge_coordinates(icons):

    merged_icons = icons.copy()
    merged = True
    while merged:
        merged = False
        to_remove = []
        to_add = []
        for i in range(len(merged_icons)):
            for j in range(i + 1, len(merged_icons)):
                icon_a = merged_icons[i]
                icon_b = merged_icons[j]
                if is_overlapping(icon_a['coordinates'], icon_b['coordinates']):

                    new_coordinates = [
                        min(icon_a['coordinates'][0], icon_b['coordinates'][0]),
                        min(icon_a['coordinates'][1], icon_b['coordinates'][1]),
                        max(icon_a['coordinates'][2], icon_b['coordinates'][2]),
                        max(icon_a['coordinates'][3], icon_b['coordinates'][3])
                    ]
                    new_text = icon_a['text'] + " " + icon_b['text']
                    new_icon = {'coordinates': new_coordinates, 'text': new_text}
                    if j not in to_remove:
                        to_remove.append(j)
                    if i not in to_remove:
                        to_remove.append(i)
                    if to_add==[]:
                        to_add.append(new_icon)
                    elif all(new_icon['coordinates'] != icon['coordinates'] for icon in to_add):
                        to_add.append(new_icon)
                    merged = True
        for idx in sorted(to_remove, reverse=True):
            del merged_icons[idx]
        merged_icons.extend(to_add)
    merged_icons=[item for item in merged_icons if not (item['coordinates'][0] < 600 and item['coordinates'][1] > 400)]
    return merged_icons


def draw_bounds(image, perception_infos):
    num = 0
    for perception_info in perception_infos:
        x1, y1, x2, y2 = perception_info["coordinates"]
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
        text_size = cv2.getTextSize(str(num), cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
        text_w, text_h = text_size
        cv2.rectangle(image, (x1, y1 - 30), (x1 + text_w, y1), (0, 0, 255), -1)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        font_color = (255, 255, 255)
        cv2.putText(image, str(num), (x1, y1 - 5), font, font_scale, font_color, 2)
        num += 1
    return image

def get_perception_infos(process):
    if not os.path.exists(temp_file):
        os.mkdir(temp_file)
    else:
        shutil.rmtree(temp_file)
        os.mkdir(temp_file)
    screenshot_file=get_screenshot(process,test_name)
    width, height = Image.open(screenshot_file).size
    text, coordinates = ocr(screenshot_file, ocr_detection, ocr_recognition)
    text, coordinates = merge_text_blocks(text, coordinates)

    perception_infos = []
    for i in range(len(coordinates)):
        perception_info = {"coordinates": coordinates[i],"text": "text: " + text[i]}
        perception_infos.append(perception_info)
    coordinates = det(screenshot_file, "icon", groundingdino_model)
    for i in range(len(coordinates)):
        perception_info = {"coordinates": coordinates[i],"text": "icon"}
        perception_infos.append(perception_info)
    image_box = []
    image_id = []
    for i in range(len(perception_infos)):
        if perception_infos[i]['text'] == 'icon':
            image_box.append(perception_infos[i]['coordinates'])
            image_id.append(i)
    for i in range(len(image_box)):
        crop(screenshot_file, image_box[i], image_id[i])
    images = get_all_files_in_folder(temp_file)
    if len(images) > 0:
        images = sorted(images, key=lambda x: int(x.split('/')[-1].split('.')[0]))
        image_id = [int(image.split('/')[-1].split('.')[0]) for image in images]
        icon_map = {}
        prompt = 'This image is an icon from a phone screen. Please briefly describe the icon function or meanings within 8 words.'
        if caption_call_method == "local":
            for i in range(len(images)):
                image_path = os.path.join(temp_file, images[i])
                icon_width, icon_height = Image.open(image_path).size
                if icon_height > 0.8 * height or icon_width * icon_height > 0.2 * width * height:
                    des = "None"
                else:
                    des = generate_local(tokenizer, model, image_path, prompt)
                icon_map[i + 1] = des
        else:
            for i in range(len(images)):
                images[i] = os.path.join(temp_file, images[i])
            icon_map = generate_api(images, prompt)
        for i, j in zip(image_id, range(1, len(image_id) + 1)):

            if icon_map.get(j):
                perception_infos[i]['text'] = "icon: " + icon_map[j]

        merged_icons = merge_coordinates(perception_infos)
        perception_infos=merged_icons

    image = cv2.imread(screenshot_file)
    merged_icons = merge_coordinates(perception_infos)
    image_with_bounds = draw_bounds(image, merged_icons)
    output_image_path = screenshot_file[: -3] + "png"
    cv2.imwrite(output_image_path, image_with_bounds)
    for i in range(len(perception_infos)):
        perception_infos[i]['coordinates']= [(perception_infos[i]['coordinates'][0] + perception_infos[i]['coordinates'][2]) / 2,(perception_infos[i]['coordinates'][1] +perception_infos[i]['coordinates'][3]) / 2]
    return perception_infos, width, height,output_image_path

def check_relaunch():
    home(process)
    time.sleep(5)
    perception_infos, width, height,screenshot1 =get_perception_infos(process)
    x,y=perception_infos[0]['coordinates']
    for i in range(len(perception_infos)):
        if test_name.lower() in perception_infos[i]['text'].lower():
            x, y = perception_infos[i]['coordinates']
            tap(process, int(x), int(y))
            time.sleep(5)
            break

    perception_infos, width, height, screenshot2 = get_perception_infos(process)
    after_shot=screenshot2
    for perception_info in perception_infos:
        x2, y2 = perception_info['coordinates']
        if y2<=400:
            tap(process, int(x2), int(y2))
            time.sleep(5)
            after_shot=get_screenshot(process,test_name)
            if (not pic_matching(screenshot2[: -3] + "jpg",after_shot)):
                break
    home(process)
    time.sleep(3)
    home(process)
    time.sleep(3)
    tap(process, int(x), int(y))
    time.sleep(3)

    check_shot = get_screenshot(process,test_name)
    if (pic_matching(check_shot, after_shot)):
        return  True
    else:
        return False

send_command(process,'location lat long NAN NAN 50 NAN')
device = "cuda"
torch.manual_seed(1234)


if caption_call_method == "local":
    if caption_model == "qwen-vl-chat":
        model_dir = snapshot_download('qwen/Qwen-VL-Chat', revision='v1.1.0')
        model = AutoModelForCausalLM.from_pretrained(model_dir, device_map=device, trust_remote_code=True).eval()
        model.generation_config = GenerationConfig.from_pretrained(model_dir, trust_remote_code=True)
    elif caption_model == "qwen-vl-chat-int4":
        qwen_dir = snapshot_download("qwen/Qwen-VL-Chat-Int4", revision='v1.0.0')
        model = AutoModelForCausalLM.from_pretrained(qwen_dir, device_map=device, trust_remote_code=True, use_safetensors=True).eval()
        model.generation_config = GenerationConfig.from_pretrained(qwen_dir, trust_remote_code=True, do_sample=False)
    else:
        print("If you choose local caption method, you must choose the caption model from \"Qwen-vl-chat\" and \"Qwen-vl-chat-int4\"")
        exit(0)
    tokenizer = AutoTokenizer.from_pretrained(qwen_dir, trust_remote_code=True)
elif caption_call_method == "api":
    pass
else:
    print("You must choose the caption model call function from \"local\" and \"api\"")
    exit(0)

groundingdino_dir = snapshot_download('AI-ModelScope/GroundingDINO', revision='v1.0.0')
groundingdino_model = pipeline('grounding-dino-task', model=groundingdino_dir)

ocr_detection = pipeline(Tasks.ocr_detection, model='damo/cv_resnet18_ocr-detection-line-level_damo')
ocr_recognition = pipeline(Tasks.ocr_recognition, model='damo/cv_convnextTiny_ocr-recognition-document_damo')

if check_relaunch():
    print("EP-2 is OK.")
    chat_file.write(f"EP-2 is OK.\n")
else:
    print("EP-2 is not ok.")
    chat_file.write(f"EP-2 is not OK.\n")


thought_history = []  
summary_history = []
action_history = []
summary = ""
action = ""
memory = ""
insight = ""




stop_flag = False
error_flag = False
keyboard = False
screenshot_file=""
i=1
while i<=num:
    stop_flag = False
    iter = 0

    while not stop_flag:
        iter += 1
        if iter == 1:
            perception_infos, width, height,screenshot_file = get_perception_infos(process)
            if os.path.exists(temp_file):
                shutil.rmtree(temp_file)
            os.makedirs(temp_file, exist_ok=True)
            for perception_info in perception_infos:
                if 'Keyboard' in perception_info['text'] or 'keyboard' in perception_info['text'] or '键盘' in perception_info['text']:
                    chat_file.write(f"keyboard:{str(perception_info)}")
                    print(f"keyboard:{str(perception_info)}")
                    keyboard = True
                    break
        elif iter == 8:
            break
        prompt_action = get_action_prompt(i,perception_infos, width, height, keyboard, summary_history,
                                          action_history, add_info, memory)
        chat_action = init_action_chat()
        chat_action = add_response("user", prompt_action, chat_action, screenshot_file)

        status = "#" * 50 + " Decision " + "#" * 50
        print(status)
        output_action = inference_chat(chat_action, API_url, token)
        chat_file.write("action-input: "+str(re.sub(r'\{\'type\': \'image_url\'[^}]*\}', '', str(chat_action))))
        chat_file.write("action-output: "+str(output_action))
        action = output_action.split("### Action ###")[-1].split("### Operation ###")[0].replace("\n", " ").replace(
            "  ", " ").strip()
        print('

        if "Tap" in action:
            number = int(action.split("(")[-1].split(")")[0])
            x,y=perception_infos[number]['coordinates']
            tap(process, int(x), int(y))

        elif "Type" in action:
            if "(text)" not in action:
                text = action.split("(")[-1].split(")")[0]
            else:
                text = action.split(" \"")[-1].split("\"")[0]
            text.replace("Type ", "")
            type(text)

        elif "Home" in action:
            home(process)

        time.sleep(5)

        last_perception_infos = copy.deepcopy(perception_infos)
        last_screenshot_file = screenshot_file
        last_keyboard = keyboard
        last_action=action
        perception_infos, width, height, screenshot_file = get_perception_infos(process)
        shutil.rmtree(temp_file)
        os.mkdir(temp_file)
        count=0
        while pic_matching(last_screenshot_file[: -3] + "jpg",screenshot_file[: -3] + "jpg"):
            count+=1
            if count>3:
                stop_flag = True
                break
            error_flag = True
            perception_infos = copy.deepcopy(last_perception_infos)
            screenshot_file = last_screenshot_file
            keyboard = last_keyboard

            prompt_action = get_action_prompt(i, perception_infos, width, height, keyboard, summary_history,
                                              action_history, add_info, memory,error_flag,last_action,False)
            chat_action = init_action_chat()
            chat_action = add_response("user", prompt_action, chat_action, screenshot_file)

            status = "#" * 50 + " Decision " + "#" * 50
            print(status)
            output_action = inference_chat(chat_action, API_url, token)
            chat_file.write("action-input: " + str(re.sub(r'\{\'type\': \'image_url\'[^}]*\}', '', str(chat_action))))
            chat_file.write("action-output: " + str(output_action))
            action = output_action.split("### Action ###")[-1].split("### Operation ###")[0].replace("\n", " ").replace(
                "  ", " ").strip()
            print('#' * len(status))
            if "Tap" in action:
                number = int(action.split("(")[-1].split(")")[0])
                x, y = perception_infos[number]['coordinates']
                tap(process, int(x), int(y))
            elif "Type" in action:
                if "(text)" not in action:
                    text = action.split("(")[-1].split(")")[0]
                else:
                    text = action.split(" \"")[-1].split("\"")[0]
                text.replace("Type ", "")
                type(text)
            elif "Home" in action:
                home(process)
            time.sleep(3)


            last_perception_infos = copy.deepcopy(perception_infos)
            last_screenshot_file = screenshot_file
            last_keyboard = keyboard
            last_action+=f", {action}"
            perception_infos, width, height, screenshot_file = get_perception_infos(process)

        thought = output_action.split("### Thought ###")[-1].split("### Action ###")[0].replace("\n", " ").replace(":",
                                                                                                                   "").replace(
            "  ", " ").strip()
        summary = output_action.split("### Operation ###")[-1].split("### Summary ###")[0].replace("\n", " ").replace(
            "  ", " ").strip()
        memory = output_action.split("### Summary ###")[-1].replace("\n", " ").replace("  ", " ").strip()
        keyboard = False
        for perception_info in perception_infos:
            if 'Keyboard' in perception_info['text'] or 'keyboard' in perception_info['text'] or '键盘' in perception_info['text']:
                keyboard = True
                chat_file.write(f"keyboard:{str(perception_info)}")
                print(f"keyboard:{str(perception_info)}")
                break


        prompt_evaluate = get_evaluate_prompt(i,last_perception_infos, perception_infos, width, height,
                                            last_keyboard, keyboard, summary, action, add_info,False)
        chat_evaluate = init_evaluate_chat()
        chat_evaluate = add_response_two_image("user", prompt_evaluate, chat_evaluate,
                                              [last_screenshot_file, screenshot_file])

        status = "#" * 50 + " Evaluation " + "#" * 50
        print(status)
        output_evaluate = inference_chat(chat_evaluate,  API_url, token)
        chat_file.write("evaluate-input: " + str(re.sub(r'\{\'type\': \'image_url\'[^}]*\}', '', str(chat_evaluate))))
        chat_file.write("evaluate-output: " + str(output_evaluate))
        chat_evaluate = add_response("assistant", output_evaluate, chat_evaluate)
        print('#' * len(status))

        if "Stop" in output_evaluate:
            stop_flag=True
        print(f"{screenshot_file} - {output_evaluate}")
        chat_file.write(f"{screenshot_file} - {output_evaluate}")

        thought_history.append(thought)
        summary_history.append(summary)
        action_history.append(action)
    i=i+1

iter = 0

stop_flag=False
while not stop_flag:

    iter += 1
    if iter == 1:
        perception_infos, width, height,screenshot_file = get_perception_infos(process)

        if os.path.exists(temp_file):
            shutil.rmtree(temp_file)

        os.makedirs(temp_file, exist_ok=True)
        for perception_info in perception_infos:
            if 'Keyboard' in perception_info['text'] or 'keyboard' in perception_info['text'] or '键盘' in perception_info['text']:
                chat_file.write(f"keyboard:{str(perception_info)}")
                print(f"keyboard:{str(perception_info)}")
                keyboard = True
                break
    elif iter == 8:
        break
    prompt_action = get_action_prompt(i,perception_infos, width, height, keyboard, summary_history,
                                      action_history, add_info, memory,False,"",True)
    chat_action = init_action_chat()
    chat_action = add_response("user", prompt_action, chat_action, screenshot_file)

    status = "
    print(status)
    output_action = inference_chat(chat_action, API_url, token)
    chat_file.write("action-input: "+str(re.sub(r'\{\'type\': \'image_url\'[^}]*\}', '', str(chat_action))))
    chat_file.write("action-output: "+str(output_action))
    action = output_action.split("### Action ###")[-1].split("### Operation ###")[0].replace("\n", " ").replace(
        "  ", " ").strip()
    print('

    if "Tap" in action:
        number = int(action.split("(")[-1].split(")")[0])
        x,y=perception_infos[number]['coordinates']
        tap(process, int(x), int(y))

    elif "Type" in action:
        if "(text)" not in action:
            text = action.split("(")[-1].split(")")[0]
        else:
            text = action.split(" \"")[-1].split("\"")[0]
        text.replace("Type ", "")
        type(text)

    elif "Home" in action:
        home(process)

    time.sleep(5)

    last_perception_infos = copy.deepcopy(perception_infos)
    last_screenshot_file = screenshot_file
    last_keyboard = keyboard
    last_action=action
    perception_infos, width, height, screenshot_file = get_perception_infos(process)
    shutil.rmtree(temp_file)
    os.mkdir(temp_file)
    count=0
    while pic_matching(last_screenshot_file[: -3] + "jpg",screenshot_file[: -3] + "jpg"):
        count+=1
        if count>3:
            stop_flag = True
            break
        error_flag = True
        perception_infos = copy.deepcopy(last_perception_infos)
        screenshot_file = last_screenshot_file
        keyboard = last_keyboard

        prompt_action = get_action_prompt(i, perception_infos, width, height, keyboard, summary_history,
                                          action_history, add_info, memory,error_flag,last_action,True)
        chat_action = init_action_chat()
        chat_action = add_response("user", prompt_action, chat_action, screenshot_file)

        status = "#" * 50 + " Decision " + "#" * 50
        print(status)
        output_action = inference_chat(chat_action, API_url, token)
        chat_file.write("action-input: " + str(re.sub(r'\{\'type\': \'image_url\'[^}]*\}', '', str(chat_action))))
        chat_file.write("action-output: " + str(output_action))
        action = output_action.split("### Action ###")[-1].split("### Operation ###")[0].replace("\n", " ").replace(
            "  ", " ").strip()
        print('#' * len(status))
        if "Tap" in action:
            number = int(action.split("(")[-1].split(")")[0])
            x, y = perception_infos[number]['coordinates']
            tap(process, int(x), int(y))
        elif "Type" in action:
            if "(text)" not in action:
                text = action.split("(")[-1].split(")")[0]
            else:
                text = action.split(" \"")[-1].split("\"")[0]
            text.replace("Type ", "")
            type(text)
        elif "Home" in action:
            home(process)
        time.sleep(3)


        last_perception_infos = copy.deepcopy(perception_infos)
        last_screenshot_file = screenshot_file
        last_keyboard = keyboard
        last_action+=f", {action}"
        perception_infos, width, height, screenshot_file = get_perception_infos(process)

    thought = output_action.split("### Thought ###")[-1].split("### Action ###")[0].replace("\n", " ").replace(":",
                                                                                                               "").replace(
        "  ", " ").strip()
    summary = output_action.split("### Operation ###")[-1].split("### Summary ###")[0].replace("\n", " ").replace(
        "  ", " ").strip()
    memory = output_action.split("### Summary ###")[-1].replace("\n", " ").replace("  ", " ").strip()
    keyboard = False
    for perception_info in perception_infos:
        if 'Keyboard' in perception_info['text'] or 'keyboard' in perception_info['text'] or '键盘' in perception_info['text']:
            keyboard = True
            chat_file.write(f"keyboard:{str(perception_info)}")
            print(f"keyboard:{str(perception_info)}")
            break


    prompt_evaluate = get_evaluate_prompt(i,last_perception_infos, perception_infos, width, height,
                                        last_keyboard, keyboard, summary, action, add_info,True)
    chat_evaluate = init_evaluate_chat()
    chat_evaluate = add_response_two_image("user", prompt_evaluate, chat_evaluate,
                                          [last_screenshot_file, screenshot_file])

    status = "
    print(status)
    output_evaluate = inference_chat(chat_evaluate,  API_url, token)
    chat_file.write("evaluate-input: " + str(re.sub(r'\{\'type\': \'image_url\'[^}]*\}', '', str(chat_evaluate))))
    chat_file.write("evaluate-output: " + str(output_evaluate))
    chat_evaluate = add_response("assistant", output_evaluate, chat_evaluate)
    print('#' * len(status))

    if "Stop" in output_evaluate:
        stop_flag=True



    print(f"{screenshot_file} - {output_evaluate}")
    chat_file.write(f"{screenshot_file} - {output_evaluate}")
    thought_history.append(thought)
    summary_history.append(summary)
    action_history.append(action)

chat_file.close()
home(process)
time.sleep(5)