# remove_boxes，用于去除一些不符合条件的框（过小或者交并比过大）
# 目标检测函数 det，借助groundingdino_model用于从图像中检测出相关物体并返回框坐标

from MobileAgent.crop import calculate_size,calculate_iou  # 导入calculate_size 用于计算框的面积，calculate_iou 用于计算两个框的交并比(IOU)
from PIL import Image  # 导入PIL库，用于图像处理
import torch  # 导入PyTorch库，用于张量操作及模型推理

# 定义函数 remove_boxes，用于去除一些不符合条件的框（过小或者交并比过大）
def remove_boxes(boxes_filt, size, iou_threshold=0.5):
    boxes_to_remove = set()  # 用一个集合存储需要被去除的框的索引
    # 遍历所有的框
    for i in range(len(boxes_filt)):
        # 计算每个框的面积，并与图像总面积的5%进行比较，若框的面积小于5%，则将该框加入移除列表
        if calculate_size(boxes_filt[i]) > 0.05 * size[0] * size[1]:
            boxes_to_remove.add(i)

        # 与其他框j进行交并比计算
        for j in range(len(boxes_filt)):
            # 如果其他框j的面积也小于5%，则将该框也加入移除列表
            if calculate_size(boxes_filt[j]) > 0.05 * size[0] * size[1]:
                boxes_to_remove.add(j)
            if i == j:  # 如果是同一个框，跳过
                continue
            if i in boxes_to_remove or j in boxes_to_remove:  # 如果框已经被标记为移除，则跳过
                continue
            # 计算两个框之间的交并比(IOU)
            iou = calculate_iou(boxes_filt[i], boxes_filt[j])
            if iou >= iou_threshold:  # 如果交并比大于或等于阈值默认0.5，则移除其中一个框
                boxes_to_remove.add(j)

    # 根据 boxes_to_remove 中的索引过滤框，保留不需要移除的框
    boxes_filt = [box for idx, box in enumerate(boxes_filt) if idx not in boxes_to_remove]
    return boxes_filt  # 返回经过筛选后的框

# 定义目标检测函数 det，用于从图像中检测出相关物体并返回框坐标
def det(input_image_path, caption, groundingdino_model, box_threshold=0.05, text_threshold=0.5):
    # 打开输入的图像文件，并获取图像的大小
    image = Image.open(input_image_path)
    size = image.size  # size 是一个元组 (宽度, 高度)
    # 处理输入的文本描述（将其转换为小写并去除多余空格，确保文本以句号结尾）
    caption = caption.lower()
    caption = caption.strip()
    if not caption.endswith('.'):
        caption = caption + '.'
    # 准备输入数据，包括图像路径、文本提示、框的阈值和文本阈值
    inputs = {
        'IMAGE_PATH': input_image_path,
        'TEXT_PROMPT': caption,
        'BOX_TRESHOLD': box_threshold,
        'TEXT_TRESHOLD': text_threshold
    }
    # 使用GroundingDINO模型进行推理，得到框的结果
    result = groundingdino_model(inputs)
    boxes_filt = result['boxes']  # 获取模型输出中的框（可能包含多个框）
    # 获取图像的宽度和高度，并对框的坐标进行缩放到图像的尺寸
    H, W = size[1], size[0]  # PIL 中的 size 是 (宽, 高)，需要调整顺序为 (高, 宽)
    # 对每个框进行坐标变换，框的坐标从 [0, 1] 范围缩放到图像的实际像素范围
    for i in range(boxes_filt.size(0)):
        boxes_filt[i] = boxes_filt[i] * torch.Tensor([W, H, W, H])  # 缩放框的坐标
        boxes_filt[i][:2] -= boxes_filt[i][2:] / 2  # 调整框的左上角坐标
        boxes_filt[i][2:] += boxes_filt[i][:2]  # 调整框的右下角坐标
    # 将框坐标转换为整数，并将其转换为列表
    boxes_filt = boxes_filt.cpu().int().tolist()
    # 调用 remove_boxes 函数根据大小和 IOU 筛选框
    filtered_boxes = remove_boxes(boxes_filt, size)  # 这里可以加限制，如 [:9] 保留前9个框
    # 提取并返回筛选后框的坐标
    coordinates = []
    for box in filtered_boxes:
        coordinates.append([box[0], box[1], box[2], box[3]])
    return coordinates
