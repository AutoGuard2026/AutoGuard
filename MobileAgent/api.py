# encode_image函数 base64-utf8编码图像
# inference_chat函数实现与ai的交互

import base64
import httpx
from openai import OpenAI


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# #deepseek
# def inference_chat(chat,api_url, token):
#
#     client = OpenAI(
#         # 中转的url地址
#         base_url='https://tbnx.plus7.plus/v1',
#         # 修改为自己生成的key
#         api_key='sk-825rDLxxbbHPFbFbwwB9Fl5NztpvzrMkP14Ae8AbQeksSI4q'
#     )
#     data = {
#                 "messages": []
#     }
#     print(chat)
#     for role, content in chat:
#         data["messages"].append({"role": role, "content": content})
#     print(data["messages"])
#
#     response = client.chat.completions.create(
#         model="deepseek-chat",
#         messages=data["messages"],
#         stream=True
#     )
#     print(response.choices[0].message.content)

# chatgpt
def inference_chat(chat,api_url, token):
    #print("begin inference_chat\n")
    client = OpenAI(
        base_url=api_url,
        api_key=token,
        http_client=httpx.Client(
            base_url=api_url,
            follow_redirects=True,
        ),
    )
    #print("begin data\n")
    data = {
        "messages": []
    }
    for role, content in chat:
        data["messages"].append({"role": role, "content": content})
    #print("end data\n")
    while True:
        try:
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=data["messages"],
                max_tokens=2048,
                temperature=0.0,
                seed=1234
            )
            #print("end completion")
            print(str(completion.choices[0].message.content))
            return completion.choices[0].message.content
        except:
            print("Network Error:")
            try:
               print(str(completion))
            except:
                print("Request Failed")
        else:
            break
    return 0
