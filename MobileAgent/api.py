import base64
import httpx
from openai import OpenAI


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
def inference_chat(chat,api_url, token):
    client = OpenAI(
        base_url=api_url,
        api_key=token,
        http_client=httpx.Client(
            base_url=api_url,
            follow_redirects=True,
        ),
    )
    data = {
        "messages": []
    }
    for role, content in chat:
        data["messages"].append({"role": role, "content": content})
    while True:
        try:
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=data["messages"],
                max_tokens=2048,
                temperature=0.0,
                seed=1234
            )
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
