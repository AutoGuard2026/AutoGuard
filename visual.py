# 输入state文件夹，匹配json和png文件，根据组件text信息确定截图范围
# 输出前五种主要颜色信息以及对比度【渐变色背景识别困难】
# 可调整参数：中心区域大小【在中部/左部/右部】；主要颜色数量

from PIL import Image
from collections import Counter
import os
import xml.etree.ElementTree as ET



def quantize_color(color, tolerance=10):
    # 将颜色分量四舍五入到最接近的tolerance的倍数【可调整参数信息】
    r, g, b = color
    r = round(r / tolerance) * tolerance
    g = round(g / tolerance) * tolerance
    b = round(b / tolerance) * tolerance
    return (r, g, b)


def calculate_luminance(r, g, b):  # 计算相对亮度
    RsRGB = r / 255
    GsRGB = g / 255
    BsRGB = b / 255
    # 归一化 计算对应 R、G、B 值
    R = RsRGB / 12.92 if (RsRGB <= 0.03928) else ((RsRGB + 0.055) / 1.055) ** 2.4
    G = RsRGB / 12.92 if (GsRGB <= 0.03928) else ((RsRGB + 0.055) / 1.055) ** 2.4
    B = RsRGB / 12.92 if (BsRGB <= 0.03928) else ((RsRGB + 0.055) / 1.055) ** 2.4
    return 0.2126 * R + 0.7152 * G + 0.0722 * B


def calculate_contrast(l1, l2):  # 计算对比度
    return (l1 + 0.05) / (l2 + 0.05)


def screenshot_check(screenshot, left, top, right, bottom):
    element_screenshot = screenshot.crop((left, top, right, bottom))
    # 分析元素截图的颜色信息
    # colors = element_screenshot.getcolors(maxcolors=100000)
    # 分析元素截图的颜色信息
    pixels = list(element_screenshot.convert("RGB").getdata())  # 确保处理为RGB格式
    # 模糊化处理后统计像素点数量
    quantized_pixels = [quantize_color(pixel) for pixel in pixels]
    color_counts = Counter(quantized_pixels)
    # 统计每种颜色像素点的数量
    # color_counts = Counter(pixels)
    # 提取30大主要颜色【可调整参数】
    most_common_colors = color_counts.most_common(30)

    for text_color in most_common_colors:
        for bg_color in most_common_colors:
            # if text_color[1]<most_common_colors[0][1]*0.1:
            bg_luminance = calculate_luminance(*bg_color[0])
            text_luminance = calculate_luminance(*text_color[0])
            contrast = calculate_contrast(max(text_luminance, bg_luminance), min(text_luminance, bg_luminance))
            if contrast >= 4.5:
                f.write(f"Contrast: {contrast:.2f}, Yes\n")
                return 1
            else:
                f.write(f"Contrast: {contrast:.2f}, No\n")
    # 输出主要颜色信息
    for idx, (color, count) in enumerate(most_common_colors, 1):
        f.write(f"Most common color {idx}: {color}, Count: {count}\n")
    f.write('Failed.\n')
    return 0


#def extract_bounds(xml_path, screenshot,s_width, s_height):
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
            #if isinstance(component, dict):
                # and component.get('resource_id') != None
            if component.get('text') and component['displayed'] == 'true' and component.get(
                    'class') == "android.widget.TextView":
            # 查找"text"属性不为空 且visible的 文本显示组件并提取bounds属性
            # 检查文字大小和背景对比度

                if height < 24:
                    f.write(f"UX-3 non-compilance: Component with text \"{component['text']}\" has bounds: left={left}, top={top}, right={right}, bottom={bottom}\n")
                    print('UX-3 non-compilance')
                    return 1

                # # 检测中部/左部/右部位置【可调整参数信息】
                # center = (left + right) / 2
                # if screenshot_check(screenshot, center - 200, top, center + 200, bottom) == 0:
                #     if screenshot_check(screenshot, left, top, left + 400, bottom) == 0:
                #         if screenshot_check(screenshot, right - 400, top, right, bottom) == 0:
                #             print(f"{xml_path}VD-1 non-compilance:{component['text']}")
                #             f.write(f"VD-1 non-compilance: Component with text \"{component['text']}\" has bounds: left={left}, top={top}, right={right}, bottom={bottom}\n")
                #             return 1
                #         else:
                #             f.write(f"Component with text \"{component['text']}\" has bounds: left={left}, top={top}, right={right}, bottom={bottom} text contrast compiled\n")
                #     else:
                #         f.write(f"Component with text \"{component['text']}\" has bounds: left={left}, top={top}, right={right}, bottom={bottom} text contrast compiled\n")
                # else:
                #     f.write(f"Component with text \"{component['text']}\" has bounds: left={left}, top={top}, right={right}, bottom={bottom} text contrast compiled\n")

            # 检查touch target
            if component['clickable'] == 'true' and component['displayed'] == 'true':
                if width < 64 or height < 64:
                    f.write(f"UX-1 non-compliance: Component-{i},{bounds} is not at least 64dp.\n")
                    print('UX-1 non-compilance')

                # 检查边距
                if left < 24 or top < 24 or 1024 - right < 24 or 768 - bottom < 24:
                    f.write( f"UX-2 non-compliance: Component-{i},{bounds} is not at least 24dp away from the screen edges.\n")
                    print('UX-2 non-compilance')

                # 检查组件之间的距离
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

#app=input("appname:")
parent_folder=".\\case"
for app in os.listdir(parent_folder):
    print(f"Processing {app}")
    f = open(f'{parent_folder}\\{app}\\log.txt', 'a', encoding='utf-8', errors='replace')  # 记录检测日志log
    folder_path=f'{parent_folder}\\{app}\\'
    files = os.listdir(folder_path)  # 查找文件夹中的所有文件
    # 获取所有xml和.png文件
    xml_files = [f for f in files if f.endswith('.xml')]
    # png_files = [f for f in files if f.endswith('.png')]
    # print('find files')

    # 找到后3位文件名相同的xml和.png文件对
    # file_pairs = []
    # for xml_file in xml_files:
    #     base_name_json = os.path.splitext(xml_file)[0][-3:]
    #     for png_file in png_files:
    #         base_name_png = os.path.splitext(png_file)[0][-3:]
    #         if base_name_json == base_name_png:
    #             file_pairs.append((xml_file, png_file))
    #             break
    # print(file_pairs)
    # 遍历每对文件
    #for xml_file, png_file in file_pairs:
    for xml_file in xml_files:
        xml_path = os.path.join(folder_path, xml_file)
        #png_path = os.path.join(folder_path, png_file)
        # 打开对应的.png文件
        #screenshot = Image.open(png_path)
        #width, height = screenshot.size
        f.write(f'{xml_file} width:1024 height:768\n')
        print(f'{xml_file}')
        #extract_bounds(xml_path, screenshot,width, height)
        extract_bounds(xml_path)
    f.close()


