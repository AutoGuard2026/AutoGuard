from collections import Counter
import os
import xml.etree.ElementTree as ET



def quantize_color(color, tolerance=10):
    r, g, b = color
    r = round(r / tolerance) * tolerance
    g = round(g / tolerance) * tolerance
    b = round(b / tolerance) * tolerance
    return (r, g, b)


def calculate_luminance(r, g, b):
    RsRGB = r / 255
    GsRGB = g / 255
    BsRGB = b / 255

    R = RsRGB / 12.92 if (RsRGB <= 0.03928) else ((RsRGB + 0.055) / 1.055) ** 2.4
    G = RsRGB / 12.92 if (GsRGB <= 0.03928) else ((RsRGB + 0.055) / 1.055) ** 2.4
    B = RsRGB / 12.92 if (BsRGB <= 0.03928) else ((RsRGB + 0.055) / 1.055) ** 2.4
    return 0.2126 * R + 0.7152 * G + 0.0722 * B


def calculate_contrast(l1, l2):
    return (l1 + 0.05) / (l2 + 0.05)


def screenshot_check(screenshot, left, top, right, bottom):
    element_screenshot = screenshot.crop((left, top, right, bottom))
    pixels = list(element_screenshot.convert("RGB").getdata())
    quantized_pixels = [quantize_color(pixel) for pixel in pixels]
    color_counts = Counter(quantized_pixels)
    most_common_colors = color_counts.most_common(30)

    for text_color in most_common_colors:
        for bg_color in most_common_colors:
            bg_luminance = calculate_luminance(*bg_color[0])
            text_luminance = calculate_luminance(*text_color[0])
            contrast = calculate_contrast(max(text_luminance, bg_luminance), min(text_luminance, bg_luminance))
            if contrast >= 4.5:
                f.write(f"Contrast: {contrast:.2f}, Yes\n")
                return 1
            else:
                f.write(f"Contrast: {contrast:.2f}, No\n")
    for idx, (color, count) in enumerate(most_common_colors, 1):
        f.write(f"Most common color {idx}: {color}, Count: {count}\n")
    f.write('Failed.\n')
    return 0

def extract_bounds(xml_path):
    i=0
    for event, elem in ET.iterparse(xml_path, ['start', 'end']):
        i+=1
        component=elem.attrib
        if component.get('bounds'):
            bounds = component['bounds'][1:-1].split("][")
            left, top = map(int, bounds[0].split(","))
            right, bottom = map(int, bounds[1].split(","))
            if top > bottom:
                temp = top
                top = bottom
                bottom = temp
            if left > right:
                temp = left
                left = right
                right = temp
            height = bottom - top
            width = right - left

            if component.get('text') and component['displayed'] == 'true' and component.get(
                    'class') == "android.widget.TextView":

                if height < 24:
                    f.write(f"UX-3 non-compilance: Component with text \"{component['text']}\" has bounds: left={left}, top={top}, right={right}, bottom={bottom}\n")
                    print('UX-3 non-compilance')
                    return 1

            if component['clickable'] == 'true' and component['displayed'] == 'true':
                if width < 64 or height < 64:
                    f.write(f"UX-1 non-compliance: Component-{i},{bounds} is not at least 64dp.\n")
                    print('UX-1 non-compilance')

                if left < 24 or top < 24 or 1024 - right < 24 or 768 - bottom < 24:
                    f.write( f"UX-2 non-compliance: Component-{i},{bounds} is not at least 24dp away from the screen edges.\n")
                    print('UX-2 non-compilance')

                j=0
                for event2, elem2 in ET.iterparse(xml_path, ['start', 'end']):
                    j+=1
                    if i != j:
                        component2 = elem2.attrib
                        if component2.get('bounds') and component2['clickable'] == 'true' and component2['displayed'] == 'true':
                            bounds2 = component2['bounds'][1:-1].split("][")
                            left2, top2 = map(int, bounds2[0].split(","))
                            right2, bottom2 = map(int, bounds2[1].split(","))
                            if top2 > bottom2:
                                temp2 = top2
                                top2 = bottom2
                                bottom2 = temp2
                            if left2 > right2:
                                temp2 = left2
                                left2 = right2
                                right2 = temp2
                            if not(right + 24 <= left2 or right2+ 24 <= left or bottom2 + 24 <= top or bottom + 24 <= top2):
                                f.write(
                                    f"UX-2 non-compliance: Component-{i},{bounds} and Component-{j},{bounds2} is not at least 24dp away from each other.\n")
                                print('UX-2 non-compilance')

    return 0

parent_folder=".\\case"
for app in os.listdir(parent_folder):
    print(f"Processing {app}")
    f = open(f'{parent_folder}\\{app}\\log.txt', 'a', encoding='utf-8', errors='replace')
    folder_path=f'{parent_folder}\\{app}\\'
    files = os.listdir(folder_path)
    xml_files = [f for f in files if f.endswith('.xml')]
    for xml_file in xml_files:
        xml_path = os.path.join(folder_path, xml_file)
        f.write(f'{xml_file} width:1024 height:768\n')
        print(f'{xml_file}')
        extract_bounds(xml_path)
    f.close()


