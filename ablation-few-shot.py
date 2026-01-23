import re
import os
import base64
import httpx
from openai import OpenAI
import copy


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
                seed=1234,
                stream= False,
                timeout=20
            )
            print(str(completion.choices[0].message.content))
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Network Error:{e}")
            try:
               print(str(completion))
            except:
                print("Request Failed")
def add_file(identifier, file_name):
    if identifier not in identifier_to_files:
        identifier_to_files[identifier] = []
    identifier_to_files[identifier].append(file_name)


def check_ID(id):

    prompt=''
    rule=""
    case=""
    match id:
        case 'PA-1' :
            rule="PA-1 The app must have simple flows if purchases are enabled, using shortcuts such as recent or favorite purchases. The app must not allow any of the following:Setup of payment methods, Multiple items to be selected for purchase, Commitment to recurring payments, such as subscriptions"
            case="If purchases are not found, it's ok and don't report."
        case 'NF-2' :
            rule="NF-2 The app draws only map content on the surface of the navigation templates. Text-based turn-by-turn directions, lane guidance, and estimated arrival time must be displayed on the relevant components of the navigation template. "
            case =""
        case 'NF-5' :
            rule="NF-5 The app must not provide turn-by-turn notifications, voice guidance, or cluster information when another navigation app is providing turn-by-turn instructions."
            case ="If another app isn't provided, it's ok and don't report."
        case 'VI-1' :
            rule="VI-1 If the user must go to the phone screen—for example, to act on a permission request—then the app must display a message instructing the user to only look at their phone screen when it’s safe to do so."
            case = "If there is no notification relevant to 'phone screen', it's ok and don't report.'"
        case 'AR-1':
            rule="AR-1 In activities implemented by the app, interactive UI elements must not be obstructed by system bars or display cutouts. "
            case = ""
        case 'PC-1':
            rule="PC-1 The app must not include features outside the app types intended for cars."
            case = "If the features is relevant to app-type, it's ok and don't report."
        case 'AD-1':
            rule="AD-1 The app must not display text-based advertising other than the advertiser's name or the product name."
            case = "Be careful to distinguish advertising from notifications."
        case 'NA-1':
            rule="NA-1 The app must not present advertisements through notifications."
            case = "Be careful to distinguish advertising from notifications."
        case 'IN-1':
            rule="IN-1 The app must display notifications only when relevant to the driver's needs."
            case = "Examples:Good: Notifying the user that a new message has arrived.Bad: Notifying the user about a new album release."
    prompt=f'Please review these images again and determine whether they violate the following rule:{rule}.'


    prompt += f'If you find any image that violates the rule, output the reasons. If not, output "All is complied."'

    return prompt

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

def init_evaluate_chat():
    operation_history = []
    sysetm_prompt = "You are a helpful AI mobile phone operating assistant.You can help me judge whether this app complies the rules according to the screenshots."
    operation_history.append(["system", [{"type": "text", "text": sysetm_prompt}]])
    return operation_history

identifier_to_files = {}
API_url = ""

token = ""
def process_test_folders(results_folder):
    for test_name in os.listdir(results_folder):
        test_path = os.path.join(results_folder, test_name)
        if os.path.isdir(test_path):
            chat_file_path = os.path.join(test_path, 'chat.txt')
            output_file_path = os.path.join(test_path, 'chat_no_final_case.txt')
            if os.path.exists(chat_file_path):
                with open(chat_file_path, 'r') as file:
                    content = file.read()
                print(test_name)
                print("*****************************************************")
                pattern = r'evaluate-output:(.*?)png'
                matches = re.findall(pattern, content, re.DOTALL)
                for match in matches:
                    match += 'png'
                    if 'find non-compliance' in match.lower():
                        pattern2 = r'\b[A-Za-z]+-\d+\b'
                        identifiers = re.findall(pattern2, match)
                        filenames = re.findall(r'C:[^ ]+?\.png', match)
                        for identifier in identifiers:
                            for filename in filenames:
                                file_name = filename.replace(r'test', r'test\results')
                                if identifier not in identifier_to_files:
                                    identifier_to_files[identifier] = []
                                add_file(identifier, file_name)
                output_file = open(output_file_path, "w")

                for identifier, file_names in identifier_to_files.items():
                    chat_evaluate = init_evaluate_chat()
                    prompt = check_ID(identifier)
                    chat_evaluate = add_response_images("user", prompt, chat_evaluate, file_names)
                    print(f"规则: {identifier}")
                    output_file.write(f"规则: {identifier}")
                    output_evaluate = inference_chat(chat_evaluate, API_url, token)
                    output_file.write("final-evaluate-output: " + str(output_evaluate) + '\n')
                output_file.close()
process_test_folders('./results')
