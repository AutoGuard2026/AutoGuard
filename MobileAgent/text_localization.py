# 定义OCR处理函数，输入参数：图像路径、OCR的检测与识别函数；返回值：识别结果和对应的坐标保存的列表
# longest_common_substring_length函数，用于计算两个字符串的最长公共子串的长度【暂未找到引用】

import cv2  # 导入OpenCV库，用于图像处理
import numpy as np  # 导入NumPy库，用于处理数组
from MobileAgent.crop import crop_image  # 从MobileAgent模块中导入crop_image函数，用于切割图像


# order_point函数，用于排序四个坐标点，使其按顺序形成矩形的四个角
def order_point(coor):
    # 将输入的坐标数组reshape为4行2列的形状，每行代表一个坐标点
    arr = np.array(coor).reshape([4, 2])

    # 计算这四个点的质心（即坐标的平均值）
    sum_ = np.sum(arr, 0)
    centroid = sum_ / arr.shape[0]

    # 计算每个点到质心的夹角（使用arctan2函数计算角度，得到的theta是一个数组）
    theta = np.arctan2(arr[:, 1] - centroid[1], arr[:, 0] - centroid[0])

    # 根据角度对点进行排序
    sort_points = arr[np.argsort(theta)]

    # 对排序后的点进行调整，如果最左边的点在质心的右边，则将点顺序调整
    sort_points = sort_points.reshape([4, -1])
    if sort_points[0][0] > centroid[0]:
        sort_points = np.concatenate([sort_points[3:], sort_points[:3]])

    # 最终的坐标点被转换为float32类型返回
    sort_points = sort_points.reshape([4, 2]).astype('float32')
    return sort_points


# longest_common_substring_length函数，用于计算两个字符串的最长公共子串的长度
def longest_common_substring_length(str1, str2):
    m = len(str1)  # 获取第一个字符串的长度
    n = len(str2)  # 获取第二个字符串的长度
    # 创建一个二维动态规划数组，用于存储中间结果
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    # 填充动态规划表格
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            # 如果字符相同，则延续之前的最长公共子串
            if str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            # 否则取最大值
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    # 返回最长公共子串的长度，即动态规划表格右下角的值
    return dp[m][n]


# 定义OCR处理函数，输入参数：图像路径、OCR的检测与识别函数
def ocr(image_path, ocr_detection, ocr_recognition):
    text_data = []  # 用于存储识别出的文本内容
    coordinate = []  # 用于存储对应文本位置的坐标

    # 读取输入的图像
    image_full = cv2.imread(image_path)
    # 使用OCR检测模型检测图像中的文本区域
    det_result = ocr_detection(image_full)
    # 从检测结果中提取文本区域的四个角的坐标（polygons表示检测到的四个点的坐标）
    det_result = det_result['polygons']

    # 遍历所有检测到的文本区域
    for i in range(det_result.shape[0]):
        # 引用之前定义的函数，对每个文本区域的四个角点进行排序，确保坐标的顺序
        pts = order_point(det_result[i])
        # 使用裁剪函数对文本区域进行裁剪
        image_crop = crop_image(image_full, pts)

        try:
            # 对裁剪后的图像进行OCR识别，获取文本结果
            result = ocr_recognition(image_crop)['text'][0]
        except:
            # 如果OCR识别失败（可能是空白区域或其他错误），则跳过当前区域
            continue

        # 获取裁剪区域的坐标，转换为整数并重新组织成框格式
        box = [int(e) for e in list(pts.reshape(-1))]
        box = [box[0], box[1], box[4], box[5]]  # 只取左上和右下两个角的坐标
        # 将识别结果和对应的坐标保存到列表中，并返回
        text_data.append(result)
        coordinate.append(box)
    return text_data, coordinate