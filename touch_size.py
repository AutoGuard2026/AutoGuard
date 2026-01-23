import os
import json

# 定义规则常量
MIN_TOUCH_TARGET_SIZE = 64
MIN_SPACING_BETWEEN_COMPONENTS = 24
MIN_SPACING_FROM_EDGES = 24
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 1606

# 检查每个组件是否符合最小触控目标大小
def check_touch_target_size(components):
    for component in components:
        width = component['right'] - component['left']
        height = component['bottom'] - component['top']
        if width < MIN_TOUCH_TARGET_SIZE or height < MIN_TOUCH_TARGET_SIZE:
        #if width*height < MIN_TOUCH_TARGET_SIZE:
            return False, f"Component {component} does not meet the minimum touch target size requirement."
    return True, "All components meet the minimum touch target size requirement."

# 检查每个组件是否至少相距24dp并且距离屏幕边缘至少24dp
def check_spacing(components):
    for i, component1 in enumerate(components):
        # 检查与屏幕边缘的距离
        if component1['left'] < MIN_SPACING_FROM_EDGES or component1['top'] < MIN_SPACING_FROM_EDGES or \
           SCREEN_WIDTH - component1['right'] < MIN_SPACING_FROM_EDGES or SCREEN_HEIGHT - component1['bottom'] < MIN_SPACING_FROM_EDGES:
            return False, f"Component {component1} is not at least {MIN_SPACING_FROM_EDGES}dp away from the screen edges."

        # 检查组件之间的距离
        for j, component2 in enumerate(components):
            if i != j:
                if not (component1['right'] + MIN_SPACING_BETWEEN_COMPONENTS <= component2['left'] or
                        component2['right'] + MIN_SPACING_BETWEEN_COMPONENTS <= component1['left'] or
                        component1['bottom'] + MIN_SPACING_BETWEEN_COMPONENTS <= component2['top'] or
                        component2['bottom'] + MIN_SPACING_BETWEEN_COMPONENTS <= component1['top']):
                    return False, f"Component {component1} and Component {component2} are not at least {MIN_SPACING_BETWEEN_COMPONENTS}dp apart."
    return True, "All components are at least 24dp apart from each other and 24dp away from screen edges."

# 检查所有规则
def check_all_rules(components):
    result, message = check_touch_target_size(components)
    if not result:
        return result, message
    
    result, message = check_spacing(components)
    if not result:
        return result, message
    
    return True, "All components meet the required rules."

# 查找"clickable"属性为TRUE的组件并提取bounds属性
def extract_bounds(components):
    c_components = []
    for component in components:
        if isinstance(component, dict):
            if component['clickable']==True and component['visible']==True:
                bounds = component.get('bounds', [])
                if len(bounds) == 2:
                    left, top = bounds[0]
                    right, bottom = bounds[1]
                    if top>bottom:
                        temp=top
                        top=bottom
                        bottom=temp
                    if left>right:
                        temp=left
                        left=right
                        right=temp
                    c_components.append({'left':left,'top':top,'right':right,'bottom':bottom})
                    #print(f"Component clickable has bounds: left={left}, top={top}, right={right}, bottom={bottom}")
    return c_components

def touch_size1(folder_path):
    flag=0
    f=open('log.txt', 'a')  #记录检测日志log
    # 查找文件夹中的所有文件
    files = os.listdir(folder_path)
    # 获取所有.json和.png文件
    json_files = [f for f in files if f.endswith('.json')]

    # 遍历每个viewtree文件
    for json_file in json_files:
        json_path = os.path.join(folder_path, json_file)
        # 打开并加载json文件
        with open(json_path, 'r', encoding='utf-8') as j:
            data = json.load(j)
        f.write(json_file+'\n')
        
        if 'views' in data and isinstance(data['views'], list):
            c_components=extract_bounds(data['views'])
        # 验证组件数组
        result, message = check_all_rules(c_components)
        if result:
            f.write(message+'\n')
        else:
            flag=1
            f.write(message+'\n')
            print(message)
    f.close()
    return flag

# 使用示例:定义文件夹路径
#folder_path = "C:\\Users\\lnx\\Desktop\\car app\\test\\testviewtree\\"
#touch_size1(folder_path)