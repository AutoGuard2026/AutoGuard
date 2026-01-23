app_type=
test_name=""
def get_instruction(i,j):
    rules1 = [0]
    rules2 = [0]
    process = [0]
    match app_type:
        case 1:
            app_type_s="media"
            rules1[0] = 1
            rules1.append("MA-1 The app must not autoplay on startup or without user initiated action to select the app or app media.")
            process.append("open the app and check whether it's playing automatically.")
            process.append("try to discover more different page in this app and don't open other app")

            rules2[0]=6
            rules2.append("VI-1 Android Auto only: If the user must go to the phone screen—for example, to act on a permission request—then the app must display a message instructing the user to only look at their phone screen when it’s safe to do so.")
            rules2.append("AR-1 In activities implemented by the app, interactive UI elements must not be obstructed by system bars or display cutouts. ")
            rules2.append("PC-1 The app must not include features outside the app types intended for cars.")
            rules2.append("AD-1 The app must not display text-based advertising other than the advertiser's name or the product name.")
            rules2.append("NA-1 The app must not present advertisements through notifications.")
            rules2.append("IN-1 The app must display notifications only when relevant to the driver's needs.Examples:Good: Notifying the user that a new message has arrived.Bad: Notifying the user about a new album release.")

        case 2:
            app_type_s = "messaging"
            rules1[0] = 5
            rules1.append("MF-1 The app must receive incoming messages.")
            process.append("open the app, check if there is a message to reply")
            rules1.append("MF-2 Messages must be properly grouped and displayed in the correct order.")
            process.append("in the app, check if messages are in order")
            rules1.append("MF-3 The user can reply to a message.")
            process.append("open the app, check if a message has a 'reply' button")
            rules1.append("MF-4 The app must use short-form messaging app design patterns. Traditional long-form messaging apps, such as apps for email, are not permitted.")
            process.append("make sure there is no way to send files in the app")
            rules1.append("MF-5 The app must implement a peer-to-peer messaging service and not notification services, such as those for weather, stocks, and sport scores.")
            process.append("open the app, check if there is a message not peer-to-peer,such as those for weather, stocks, and sport scores.")
            process.append("try to discover more different page in this app and don't open other app")

            rules2[0] = 4
            rules2.append("PC-1 The app must not include features outside the app types intended for cars.")
            rules2.append(
                "AD-1 The app must not display text-based advertising other than the advertiser's name or the product name.")
            rules2.append("NA-1 The app must not present advertisements through notifications.")
            rules2.append(
                "IN-1 The app must display notifications only when relevant to the driver's needs.Examples:Good: Notifying the user that a new message has arrived.Bad: Notifying the user about a new album release.")

        case 3:
            app_type_s="navigation"
            rules1[0] = 3
            rules1.append("PA-1 The app must have simple flows if purchases are enabled, using shortcuts such as recent or favorite purchases. The app must not allow any of the following:Setup of payment methods, Multiple items to be selected for purchase, Commitment to recurring payments, such as subscriptions")
            process.append("search restaurant, check if there are recent/favorite purchases, and pay attention to payment methods, Multiple items to be selected, subscriptions")
            rules1.append("NF-2 The app draws only map content on the surface of the navigation templates. Text-based turn-by-turn directions, lane guidance, and estimated arrival time must be displayed on the relevant components of the navigation template. ")
            process.append("navigate to supermarket and check the navigation page")
            rules1.append("NF-5 The app must not provide turn-by-turn notifications, voice guidance, or cluster information when another navigation app is providing turn-by-turn instructions.")
            process.append("navigate to supermarket in test-app, home, launch another navigation app, home, click test-app icon and check if it is still navigation")
            process.append("try to discover more different page in this app and don't open other app")

            rules2[0] = 6
            rules2.append(
                "VI-1 If the user must go to the phone screen—for example, to act on a permission request—then the app must display a message instructing the user to only look at their phone screen when it’s safe to do so.")
            rules2.append(
                "AR-1 In activities implemented by the app, interactive UI elements must not be obstructed by system bars or display cutouts. ")
            rules2.append("PC-1 The app must not include features outside the app types intended for cars.")
            rules2.append(
                "AD-1 The app must not display text-based advertising other than the advertiser's name or the product name.")
            rules2.append("NA-1 The app must not present advertisements through notifications.")
            rules2.append(
                "IN-1 The app must display notifications only when relevant to the driver's needs.Examples:Good: Notifying the user that a new message has arrived.Bad: Notifying the user about a new album release.")

        case 4 :
            app_type_s="POI(point of interest)"
            rules1[0] = 1
            rules1.append("PA-1 If purchases are enabled, using shortcuts such as recent or favorite purchases. The app must not allow any of the following: Setup of payment methods, Multiple items to be selected for purchase, Commitment to recurring payments, such as subscriptions.")
            process.append("search station, check if there are recent/favorite purchases, and pay attention to payment methods, Multiple items to be selected, subscriptions")
            process.append("try to discover more different page in this app and don't open other app")

            rules2[0] = 7
            rules2.append(
                "VI-1 Android Auto only: If the user must go to the phone screen—for example, to act on a permission request—then the app must display a message instructing the user to only look at their phone screen when it’s safe to do so.")
            rules2.append(
                "AR-1 In activities implemented by the app, interactive UI elements must not be obstructed by system bars or display cutouts. ")
            rules2.append("PC-1 The app must not include features outside the app types intended for cars.")
            rules2.append(
                "AD-1 The app must not display text-based advertising other than the advertiser's name or the product name.")
            rules2.append("NA-1 The app must not present advertisements through notifications.")
            rules2.append(
                "IN-1 The app must display notifications only when relevant to the driver's needs.Examples:Good: Notifying the user that a new message has arrived.Bad: Notifying the user about a new album release.")
            rules2.append("PF-1 The app must provide meaningful functionality relevant to driving.")

        case 5:
            app_type_s="IOT(internet of things)"
            rules1[0] = 1
            rules1.append(
                "PA-1 The app must have simple flows if purchases are enabled, using shortcuts such as recent or favorite purchases. The app must not allow any of the following:Setup of payment methods, Multiple items to be selected for purchase, Commitment to recurring payments, such as subscriptions")
            process.append(
                "search shop, check if there are recent/favorite purchases, and pay attention to payment methods, Multiple items to be selected, subscriptions")
            process.append("try to discover more different page in this app and don't open other app")
            rules2[0] = 6
            rules2.append(
                "VI-1 Android Auto only: If the user must go to the phone screen—for example, to act on a permission request—then the app must display a message instructing the user to only look at their phone screen when it’s safe to do so.")
            rules2.append(
                "AR-1 In activities implemented by the app, interactive UI elements must not be obstructed by system bars or display cutouts. ")
            rules2.append("PC-1 The app must not include features outside the app types intended for cars.")
            rules2.append(
                "AD-1 The app must not display text-based advertising other than the advertiser's name or the product name.")
            rules2.append("NA-1 The app must not present advertisements through notifications.")
            rules2.append(
                "IN-1 The app must display notifications only when relevant to the driver's needs.Examples:Good: Notifying the user that a new message has arrived.Bad: Notifying the user about a new album release.")

        case 6:
            app_type_s ="weather"
            rules1[0] = 3
            rules1.append("WE-3 Forecast information must include easily readable icons and symbols.")
            process.append("Find the weather forecast and check if the forecast information contains readable icons and symbols.")
            rules1.append("WE-4 Customization of forecast intervals must not be made possible using templates.")
            process.append("templates including list, message, search-box, sign-in and other UI elements, find the view about forecast intervals and judge whether this view contains templates elements.")
            rules1.append(
                "PA-1 The app must have simple flows if purchases are enabled, using shortcuts such as recent or favorite purchases. The app must not allow any of the following:Setup of payment methods, Multiple items to be selected for purchase, Commitment to recurring payments, such as subscriptions")
            process.append(
                "search order/subscribe, check if there are recent/favorite purchases, and pay attention to payment methods, Multiple items to be selected, subscriptions")

            process.append("try to discover more different page in this app and don't open other app")
            rules2[0] = 9
            rules2.append(
                "VI-1 Android Auto only: If the user must go to the phone screen—for example, to act on a permission request—then the app must display a message instructing the user to only look at their phone screen when it’s safe to do so.")
            rules2.append(
                "AR-1 In activities implemented by the app, interactive UI elements must not be obstructed by system bars or display cutouts. ")
            rules2.append("PC-1 The app must not include features outside the app types intended for cars.")
            rules2.append(
                "AD-1 The app must not display text-based advertising other than the advertiser's name or the product name.")
            rules2.append("NA-1 The app must not present advertisements through notifications.")
            rules2.append(
                "IN-1 The app must display notifications only when relevant to the driver's needs.Examples:Good: Notifying the user that a new message has arrived.Bad: Notifying the user about a new album release.")
            rules2.append("WE-1 App must include weather related content, which must be relevant to the user's current location or a user specified location.")
            rules2.append("WE-2 Weather information on map tiles must be readable and may not include complex legends. Apps may include a maximum of three legends. Apps with multiple legends may have a maximum of three colors, whereas single legend apps may have more than three colors.")
            rules2.append("WE-5 Weather apps must not show more than five unique weather map annotations in a given view (for example: Temperature markers, wind speed markers, humidity, radar overlay, lightning indicators, road conditions all in the same view).")
    if j==1:
        instruction = f"We want to test the {test_name} App，a {app_type_s} app.The rule to be tested is: {rules1[i]}"
        return instruction
    elif j==2:
        add_info=f"The click-chain to check the rule may be {process[i]}."
        return add_info
    elif j==3:
        whole=""
        for rule in rules2[1:]:
            whole += rule
            whole += "\n"
        return whole

def get_action_prompt(i,clickable_infos, width, height,keyboard, summary_history, action_history,add_info, memory,error_flag=False, last_action="",free_flag=False):
    print(f"free_flag is: {free_flag}")
    if bool(free_flag)==True:
        instruction = get_instruction(i, 2)
    else:
        instruction=get_instruction(i,1)
    prompt = "### Background ###\n"
    prompt += f"This image is a DHU(desktop head unit) screenshot. Its width is {width} pixels and its height is {height} pixels. The car is driving. The task is: {instruction}\n\n"

    prompt += "### Screenshot information ###\n"
    prompt += "In order to help you better perceive the content in this screenshot, we extract some information on the current screenshot through system files. "
    prompt += "This information consists of two parts: \"number: content\". "
    prompt += "The number corresponds to the part circled by the red rectangle in the image. The content is a text or an icon description respectively. "
    prompt += "The information is as follow:\n"
    for num in range(len(clickable_infos)):
        prompt += f"{num}: {clickable_infos[num]['text']}\n"
    
    prompt += "Please note that this information is not necessarily accurate. You need to combine the screenshot to understand."
    prompt += "\n\n"

    prompt += "### Keyboard status ###\n"
    prompt += "We extract the keyboard status of the current screenshot and it is whether the keyboard of the current screenshot is activated.\n"
    prompt += "The keyboard status is as follow:\n"
    if keyboard:
        prompt += "The keyboard has been activated and you can type."
    else:
        prompt += "The keyboard has not been activated and you can\'t type."
    prompt += "\n\n"
    if add_info != "":
        prompt += "### Hint ###\n"
        prompt += "There are hints to help you complete the user\'s instructions. The hints are as follow:\n"
        prompt += add_info+"If you want to open the app from the home page, click the icon with nine dots which means more apps."
        prompt +="If you want to back to the last page , click the '<' icon in the upper left corner."
        if not free_flag:
            prompt += get_instruction(i,2)
        prompt += "\n\n"
    
    if len(action_history) > 0:
        prompt += "### History operations ###\n"
        prompt += "Before reaching this page, some operations have been completed. You need to refer to the completed operations to decide the next operation. These operations are as follow:\n"
        for n in range(len(action_history)):
            prompt += f"Step-{n+1}: [Operation: " + summary_history[n].split(" to ")[0].strip() + "; Action: " + action_history[n] + "]\n"
        prompt += "\n"
    if memory != "":
        prompt += "### Memory ###\n"
        prompt += "During the operations, you record the following contents on the screenshot for use in subsequent operations:\n"
        prompt += "Memory:\n" + memory + "\n"
    if error_flag:
        prompt +="### Last operation invalid ###\n"
        prompt += f"You previously executed the Action \"{last_action}\". But you find that this operation does not meet your expectation. You need to reflect and revise your operation this time."
        prompt += "\n\n"
    prompt += "### Response requirements ###\n"
    prompt += "Now you need to combine all of the above to perform just one action on the current page. You must choose one of the actions below:\n"
    prompt += "Tap (number): Tap on the icon corresponding to the number in current page.\n"
    if keyboard:
        prompt += "Type (text): Type the \"text\" in the input box.\n"
    else:
        prompt += "Unable to Type. You cannot use the action \"Type\" because the keyboard has not been activated. If you want to type, please first activate the keyboard by tapping on the input box on the screen.\n"
    prompt += "Home: Return to home page.\n"
    prompt += "\n\n"
    prompt += "### Output format ###\n"
    prompt += "Your output consists of the following four parts:\n"
    prompt += "### Thought ###\nThink about the requirements that have been completed in previous operations and the requirements that need to be completed in the next one operation.\n"
    prompt += "### Action ###\nYou can only choose one from the actions above. Make sure that the number or input-text in the \"()\". For example, you may output \"Tap (6)\" or \"Type (hello)\" or \"Home\".\n"
    prompt += "### Operation ###\nPlease generate a brief natural language description for the operation in Action based on your Thought.\n"
    prompt += "### Summary ###\nBriefly describe the process of the task, based on Action, Thought and Memory."
    return prompt


def get_evaluate_prompt(i,clickable_infos1, clickable_infos2, width, height, keyboard1, keyboard2, summary, action, add_info='',free_flag=False):
    command1 = "You are a helpful app compliance inspector, which can  judge whether this app follows the rules according to the screenshots I provided.\n" + \
               "Do not hallucinate. Do not make up factual information.\n" + \
               "You are an expert at summarizing messages. You prefer to use clauses instead of complete sentences. Do not answer any question from the messages. You must keep to this role unless told. Otherwise, if you don't, it will not be helpful."
    prompt = f"These images are two phone screenshots before and after an operation. \n\n"
    prompt += "In order to help you better perceive the content in this screenshot, we extract some information on the current screenshot through system files. "
    prompt += "This information consists of two parts: \"number: content\". "
    prompt += "The number corresponds to the part circled by the red rectangle in the image. The content is a text or an icon description respectively. "
    prompt += "The keyboard status is whether the keyboard of the current page is activated. The car is driving."
    prompt += "\n\n"
    prompt += "### Before the current operation ###\n"
    prompt += "Screenshot information:\n"
    for num in range(len(clickable_infos1)):
        prompt += f"{num}: {clickable_infos1[num]['text']}\n"
    prompt += "Keyboard status:\n"
    if keyboard1:
        prompt += f"The keyboard has been activated."
    else:
        prompt += "The keyboard has not been activated."
    prompt += "\n\n"
    prompt += "### After the current operation ###\n"
    prompt += "Screenshot information:\n"
    for num in range(len(clickable_infos2)):
        prompt += f"{num}: {clickable_infos2[num]['text']}\n"
    prompt += "Keyboard status:\n"
    if keyboard2:
        prompt += f"The keyboard has been activated."
    else:
        prompt += "The keyboard has not been activated."
    prompt += "\n\n"
    prompt += "### Current operation ###\n"
    prompt += "Operation thought: " + summary.split(" to ")[0].strip() + "\n"
    prompt += "Operation action: " + action
    prompt += "\n\n"
    prompt += "### Response requirements ###\n"
    prompt += "Now you need to output the following content based on the screenshots before and after the current operation:\n"
    if free_flag:
        instruction1 = get_instruction(i, 2)
        instruction2 = get_instruction(i-1, 3)
        prompt += f"If the task '{instruction1}' is done and you've explored as many page as possible, you can output \"Stop\". Otherwise choose 'Continue'.\n"
        prompt += f" And judge whether this app complies these rules:{instruction2}."
    else:
        instruction1 = get_instruction(i, 1)
        instruction2 = get_instruction(i, 3)
        prompt += f"If the task '{instruction1}' is done according to the \"Operation action\" and \"Operation thought\", and you can output \"Stop\" and judge whether this app complies this rule. Otherwise choose 'Continue'.\n"
        prompt +=f"If the task isn't done and you choose to Continue, you can only judge whether this app complies these rule:{instruction2}."
    prompt += "\n\n"
    prompt += "### Output format ###\n"
    prompt += "Your output format is:\n"
    prompt += "'Stop' or 'Continue'\n 'All is complied' or 'Find non-compliance:<rule number>+thoughts chain+<rule number>+thoughts chain'. Do not output any other information.\n" + \
               "For example, you may output:\"Stop.\nFind non-compliance:\n" + \
               "AB-2  the notification is from a game app.\n" + \
               "CD-1  purchase flow is not simple.\"\n"
    return command1+prompt


def get_evaluate_prompt2(i, clickable_infos1, clickable_infos2, width, height, keyboard1, keyboard2, summary, action,
                        add_info='', stop_flag=False):
    command1 = "You are a helpful app compliance inspector, which can  judge whether this app follows the rules according to the screenshots I provided.\n" + \
               "Do not hallucinate. Do not make up factual information.\n" + \
               "You are an expert at summarizing messages. You prefer to use clauses instead of complete sentences. Do not answer any question from the messages. You must keep to this role unless told. Otherwise, if you don't, it will not be helpful."
    prompt = f"These images are two phone screenshots before and after an operation. \n\n"
    prompt += "In order to help you better perceive the content in this screenshot, we extract some information on the current screenshot through system files. "
    prompt += "This information consists of two parts: \"number: content\". "
    prompt += "The number corresponds to the part circled by the red rectangle in the image. The content is a text or an icon description respectively. "
    prompt += "The keyboard status is whether the keyboard of the current page is activated. The car is driving."
    prompt += "\n\n"
    prompt += "### Before the current operation ###\n"
    prompt += "Screenshot information:\n"
    for num in range(len(clickable_infos1)):
        prompt += f"{num}: {clickable_infos1[num]['text']}\n"
    prompt += "Keyboard status:\n"
    if keyboard1:
        prompt += f"The keyboard has been activated."
    else:
        prompt += "The keyboard has not been activated."
    prompt += "\n\n"
    prompt += "### After the current operation ###\n"
    prompt += "Screenshot information:\n"
    for num in range(len(clickable_infos2)):
        prompt += f"{num}: {clickable_infos2[num]['text']}\n"
    prompt += "Keyboard status:\n"
    if keyboard2:
        prompt += f"The keyboard has been activated."
    else:
        prompt += "The keyboard has not been activated."
    prompt += "\n\n"
    prompt += "### Current operation ###\n"
    prompt += "Operation thought: " + summary.split(" to ")[0].strip() + "\n"
    prompt += "Operation action: " + action
    prompt += "\n\n"
    prompt += "### Response requirements ###\n"
    prompt += "Now you need to output the following content based on the screenshots before and after the current operation:\n"
    if stop_flag:
        instruction1 = get_instruction(i, 1)
        instruction2 = get_instruction(i, 3)
        prompt += f"Judge whether this app complies these rules:{instruction1}\n{instruction2}."
    prompt += "\n\n"
    prompt += "### Output format ###\n"
    prompt += "Your output format is:\n"
    prompt += "'All is complied' or 'Find non-compliance:<rule number>+thoughts chain+<rule number>+thoughts chain'. Do not output any other information.\n" + \
              "For example, you may output:\"Find non-compliance:\n" + \
              "AB-2  the notification is from a game app.\n" + \
              "CD-1  purchase flow is not simple.\"\n" + \
        "Or you may just output:\"All is complied\"\n"
    return command1 + prompt