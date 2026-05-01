import copy
from openai import OpenAI
import httpx
import json
from MobileAgent.api import encode_image
def init_action_chat():
    operation_history = []
    sysetm_prompt = "You are a helpful app compliance inspector. You can help me operate the Android auto app."
    operation_history.append(["system", [{"type": "text", "text": sysetm_prompt}]])
    return operation_history

def init_evaluate_chat():
    operation_history = []
    sysetm_prompt = "You are a helpful AI mobile phone operating assistant.You can help me judge whether this app complies the rules according to the screenshots."
    operation_history.append(["system", [{"type": "text", "text": sysetm_prompt}]])
    return operation_history

def ask_gpt4(content,token):
    add_info = "This is a description of the icon and its coordinates. Please help me simplify the description and remain the most important words, within 8 words. You must not output any other information or modify the format or coordinates field.\n"
    add_info +="Your output format: \"{'coordinates': [0,0,0,0],'text': xxxx}\" and separate {} with commas. Please process the following data:\n"
    prompt = add_info +str(content)
    client = OpenAI(
        base_url="https://api.xty.app/v1",
        api_key=token,
        http_client=httpx.Client(
            base_url="https://api.xty.app/v1",
            follow_redirects=True,
        ),
    )
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": [
                {
                    "type":"text",
                    "text":prompt
                },
            ]},
        ],
        max_tokens=4096
    )

    input_str=completion.choices[0].message.content
    json_str = input_str.replace('"', '\'')
    json_str = json_str.replace('\'coordinates\'', '"coordinates"')
    json_str = json_str.replace(' \'text\': \'', ' "text": "')
    json_str = json_str.replace('\'}', '"}')
    result = []
    try:
        data = json.loads(json_str)
        for item in data:
            text = item['text']
            coordinates = item['coordinates']
            result.append({
                'text': text,
                'coordinates': coordinates
            })
    except json.JSONDecodeError as e:
        print(f"JSON解析错误：{e}")
        print(input_str)
        print(json_str)
        return content
    return result

def add_response(role, prompt, chat_history, image=None):
    new_chat_history = copy.deepcopy(chat_history)
    if image:
        base64_image = encode_image(image)
        content = [
            {
                "type": "text", 
                "text": prompt
            },
            {
                "type": "image_url", 
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            },
        ]
    else:
        content = [
            {
            "type": "text", 
            "text": prompt
            },
        ]
    new_chat_history.append([role, content])
    return new_chat_history

def add_response_two_image(role, prompt, chat_history, image):
    new_chat_history = copy.deepcopy(chat_history)

    base64_image1 = encode_image(image[0])
    base64_image2 = encode_image(image[1])
    content = [
        {
            "type": "text", 
            "text": prompt
        },
        {
            "type": "image_url", 
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image1}"
            }
        },
        {
            "type": "image_url", 
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image2}"
            }
        },
    ]
    new_chat_history.append([role, content])
    return new_chat_history
def add_response_images(role, prompt, chat_history, image):
    new_chat_history = copy.deepcopy(chat_history)
    content = [
        {
            "type": "text",
            "text": prompt
        }
    ]
    for i in image:
        base64_image1 = encode_image(i)
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image1}"}})
    new_chat_history.append([role, content])
    return new_chat_history
def print_status(chat_history):
    print("*"*100)
    for chat in chat_history:
        print("role:", chat[0])
        print(chat[1][0]["text"] + "<image>"*(len(chat[1])-1) + "\n")
    print("*"*100)