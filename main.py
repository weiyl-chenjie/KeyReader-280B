# python自带库
import os
import sys
from time import sleep
import sqlite3
# 第三方库
import cv2 as cv
import numpy as np
from PySide2.QtWidgets import QMainWindow, QApplication, QMessageBox
from PySide2.QtGui import Qt, QImage, QPixmap
from PySide2.QtCore import QThread, Signal
import keyboard
import pyautogui as pag
from PIL import ImageGrab
# 自己的包
from UI2PY.MainWindow import Ui_MainWindow
from set_calibration_line import SetCalibrationLine
from config import Config
from HslCommunication import SiemensPLCS, SiemensS7Net
from sato import ComThread


class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.Ui_MainWindow = Ui_MainWindow()
        self.Ui_MainWindow.setupUi(self)

        self.set_calibration_line_pane = SetCalibrationLine()
        self.set_calibration_line_pane.setWindowModality(Qt.ApplicationModal)  # 设置为模态窗口

        self._thread = VideoThread()
        self._thread.signal.connect(self.show_video)
        self._thread.start()

        self.com = ComThread()
        self.conf = Config()

        # 获取厂家名
        self.plant = self.conf.read_config('config', 'product', 'plant')
        # 获取产品名
        self.product = self.conf.read_config('config', 'product', 'product')
        # 获取弹子数
        self.marble_number = int(self.conf.read_config('config', 'product', 'marble_number'))
        # 单排齿还是多排齿
        self.row_number = int(self.conf.read_config('config', 'product', 'row_number'))
        # 是否有钥匙到位传感器
        self.has_key_sensor = self.conf.read_config('config', 'product', 'has_key_sensor').upper() == 'YES'
        # 钥匙到位传感器上一次的状态
        self.key_last_status = False
        # # 阈值
        # self.min_threshold = int(self.conf.read_config('canny', 'min_threshold'))
        # self.max_threshold = int(self.conf.read_config('canny', 'max_threshold'))
        # 获取PLC的ip
        self.ip_plc = self.conf.read_config(product=self.product, section='plc', name='ip')
        # 创建PLC实例
        self.siemens = SiemensS7Net(siemens=SiemensPLCS.S1200, ipAddress=self.ip_plc)
        # 钥匙到位传感器上一次的状态
        self.key_sensor_last_status = False
        self.Ui_MainWindow.comboBox_change_product.addItem('')
        # 读取所有产品
        with sqlite3.connect('keyid.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT plant, product, marble_number, rows FROM products")
            rows = cur.fetchall()
            for row in rows:
                plant = row[0]
                product = row[1]
                item = plant + ":" + product
                self.Ui_MainWindow.comboBox_change_product.addItem(item)

        self.Ui_MainWindow.label_status.setText("自动读钥匙号，请点击'开始'按钮")

        self.setup()

    def setup(self):
        # 设置控件值
        # 工厂
        self.Ui_MainWindow.lineEdit_plant.setText(self.plant)
        # 产品
        self.Ui_MainWindow.lineEdit_product.setText(self.product)
        # 弹子数
        self.Ui_MainWindow.lineEdit_marble_number.setText(str(self.marble_number))
        if self.row_number == 1:
            self.Ui_MainWindow.radioButton_single_row.setCheckable(True)
            self.Ui_MainWindow.radioButton_single_row.setChecked(True)
            self.Ui_MainWindow.radioButton_double_row.setCheckable(False)
        elif self.row_number == 2:
            self.Ui_MainWindow.radioButton_double_row.setCheckable(True)
            self.Ui_MainWindow.radioButton_double_row.setChecked(True)
            self.Ui_MainWindow.radioButton_single_row.setCheckable(False)
        # 是否有钥匙到位传感器
        self.Ui_MainWindow.checkBox_key_sensor.setChecked(self.has_key_sensor)
        # PLC的ip
        self.Ui_MainWindow.lineEdit_IP_PLC.setText(self.ip_plc)

        if self.com.check_com():  # 如果有串口，则打开指定的串口
            if self.com.open_com():  # 如果串口打开成功
                if self.siemens.ConnectServer().IsSuccess:  # 若连接成功
                    self._thread.working = True
                    self.Ui_MainWindow.label_status.setText('PLC连接成功')
                    # if not self._thread.cap.isOpened():
                    #     self._thread.cap.open(0)
                    # self._thread.working = True
                    # self._thread.start()
                    self.Ui_MainWindow.label_status.setText('等待钥匙插入')
                    self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 255, 127);')
                else:
                    self.Ui_MainWindow.label_status.setText('PLC连接失败')
                    self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 0, 0);')
            else:  # 如果串口打开失败
                QMessageBox.critical(self, '错误！', '串口打开失败！')
                self.Ui_MainWindow.label_status.setText('串口打开失败！')
                self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 0, 0);')
        else:
            QMessageBox.critical(self, '错误！', '未发现串口！')
            self.Ui_MainWindow.label_status.setText('未发现串口！')
            self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 0, 0);')

    # 槽函数
    def start(self):
        self.Ui_MainWindow.label_status.setText('连接PLC...')
        self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 255, 127);')
        QApplication.processEvents()
        if self.siemens.ConnectServer().IsSuccess:  # 若连接成功
            self._thread.working = True
            self.Ui_MainWindow.label_status.setText('PLC连接成功')
            # if not self._thread.cap.isOpened():
            #     self._thread.cap.open(0)
            # self._thread.working = True
            # self._thread.start()
            self.Ui_MainWindow.label_status.setText('等待钥匙插入')
            self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 255, 127);')
        else:
            self.Ui_MainWindow.label_status.setText('PLC连接失败')
            self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 0, 0);')

    def change_product(self, item):
        self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 255, 127);')
        if item:  # 若果选择了非空项目
            product = item.split(":")[1]
            print(product)
            with sqlite3.connect('keyid.db') as conn:
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT plant, product, marble_number, rows FROM products WHERE product ='%s'" % product)
                    rows = cur.fetchall()
                    row = rows[0]  # 应该只有一条数据
                except Exception as e:
                    self.Ui_MainWindow.label_status.setText('change_product:%s' % str(e))
                    self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 0, 0);')
                # 修改变量值
                self.plant = row[0]
                self.product = row[1]
                self.marble_number = row[2]
                self.row_number = row[3]

            self.setup()

            # 修改对应的.ini文件
            self.conf.update_config(product='config', section='product', name='plant', value=self.plant)
            self.conf.update_config(product='config', section='product', name='product', value=self.product)
            self.conf.update_config(product='config', section='product', name='marble_number', value=str(self.marble_number))
            self.conf.update_config(product='config', section='product', name='row_number', value=str(self.row_number))

    def manual_adjustment_parameters(self):
        os.startfile(self.product+'.ini')

    def self_calibration(self):
        # 暂停读取摄像头进程，并释放摄像头
        # self._thread.working = False
        step = 1
        while step < 5:
            self.Ui_MainWindow.label_status.setText('自动校准：请插入%s号钥匙' % step)
            if self.key_is_ready():  # 如果感应到钥匙插入
                self.get_key_capture()

                keyid = self.edge_detect(self_calibration=True)
                if step == 1:
                    one = keyid
                    self.conf.update_config(product=self.product, section='key', name='one', value=str(keyid))
                elif step == 2:
                    two = keyid
                    self.conf.update_config(product=self.product, section='key', name='two', value=str(keyid))
                if step == 3:
                    three = keyid
                    self.conf.update_config(product=self.product, section='key', name='three', value=str(keyid))
                if step == 4:
                    four = keyid
                    self.conf.update_config(product=self.product, section='key', name='four', value=str(keyid))
                step += 1
        if self.row_number == 1:
            tolerance = abs(int((one - four)/6))
        elif self.row_number == 2:
            tolerance = tuple((int(abs(i - j)/6) for i, j in zip(one, four)))
        self.conf.update_config(product=self.product, section='key', name='tolerance', value=str(tolerance))

        self.Ui_MainWindow.label_status.setText('校准结束，点击开始进行工作')

    def set_calibration_line(self):
        # 暂停读取摄像头进程，并释放摄像头，然后调用设置校准线的窗口
        # self._thread.__del__()
        self.set_calibration_line_pane.setup()
        self.set_calibration_line_pane.show()

    def show_video(self):
        if self.key_is_ready():  # 如果有钥匙进入
            # 捕获图像并判断钥匙号
            _, keycode = self.capture()
            self.barcode_print(product=self.product, keycode=keycode)
        else:
            # img = QImage(self._thread.img, self._thread.img.shape[1], self._thread.img.shape[0], QImage.Format_RGB888)
            # self.Ui_MainWindow.label_show_image.setPixmap(QPixmap.fromImage(img))
            pass
        # print("发送信号了")

    def manual_capture(self):
        print('manual_capture')
        # self.Ui_MainWindow.label_status.setText('手动读号')
        # self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(0, 255, 0);')
        keyid, canny = self.edge_detect(is_capture=True)
        keycode = self.get_keycode(keyid)
        self.Ui_MainWindow.lineEdit_key_code.setText(keycode)
        self.Ui_MainWindow.lineEdit_key_id.setText(keyid)
        cv.imshow('Canny', canny)
        cv.waitKey()
        cv.destroyAllWindows()

    @staticmethod
    def has_key_sensor_changed(evt):
        conf = Config()
        if evt:  # 如果选择了钥匙到位传感器
            conf.update_config(product='config', section='product', name='has_key_sensor', value='YES')
        else:  # 如果取消了钥匙到位传感器
            conf.update_config(product='config', section='product', name='has_key_sensor', value='NO')

    def change_ip_plc(self):
        ip = self.Ui_MainWindow.lineEdit_IP_PLC.text()
        self.conf.update_config(product=self.product, section='plc', name='ip', value=ip)

    def plc_connect_test(self):
        self.Ui_MainWindow.label_status.setText('正在连接PLC...请稍后')
        QApplication.processEvents()
        if self.siemens.ConnectServer().IsSuccess:  # 若连接成功
            self.Ui_MainWindow.label_status.setText('成功连接PLC')
            self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(0, 255, 0);')
        else:
            self.Ui_MainWindow.label_status.setText('PLC连接失败！')
            self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 0, 0);')

    # 选择图片的识别区域
    def select_capture_region(self):
        # self._thread.__del__()
        if keyboard.wait(hotkey='ctrl+alt') == None:
            x1, y1 = pag.position()
            print(pag.position())
            if keyboard.wait(hotkey='ctrl+alt') == None:
                x2, y2 = pag.position()
                print(pag.position())
        pos_new = str((x1, y1, x2, y2))
        self.conf.update_config(product='config', section='capture_region', name='position', value=pos_new)

    # 自定义函数
    # 边缘检测
    def edge_detect(self, self_calibration=False, check_key_is_ready=False, is_capture=False):
        print('edge_detect')
        # if self._thread.working:  # 如果线程正在工作
        #     original_img = self._thread.img
        # else:
        #     _, original_img = self._thread.cap.read()
        original_img = self.get_key_capture()
        # original_img = cv.flip(original_img, 1)  # 水平翻转
        # original_img = cv.imread("key.jpg")
        # 阈值
        min_threshold = int(self.conf.read_config(product=self.product, section='canny', name='min_threshold'))
        max_threshold = int(self.conf.read_config(product=self.product, section='canny', name='max_threshold'))
        # Canny(): 边缘检测
        # 得到原始图片的边缘
        img1 = cv.GaussianBlur(original_img, (3, 3), 0)
        canny_original_img = cv.Canny(img1, min_threshold, max_threshold)
        # 画线的粗细和类型
        thickness = int(self.conf.read_config(product=self.product, section='line', name='thickness'))
        lineType = int(self.conf.read_config(product=self.product, section='line', name='lineType'))
        # 底线起点和终点的坐标(双排齿的右边竖线)
        ptStart_bottom = eval(self.conf.read_config(product=self.product, section='line', name='ptStart_bottom'))
        ptEnd_bottom = eval(self.conf.read_config(product=self.product, section='line', name='ptEnd_bottom'))
        point_color_bottom = eval(self.conf.read_config(product=self.product, section='line', name='point_color_bottom'))  # BGR
        cv.line(original_img, ptStart_bottom, ptEnd_bottom, point_color_bottom, thickness, lineType)

        # 顶线起点和终点的坐标(双排齿的左边竖线)
        ptStart_top = eval(self.conf.read_config(product=self.product, section='line', name='ptStart_top'))
        ptEnd_top = eval(self.conf.read_config(product=self.product, section='line', name='ptEnd_top'))
        point_color_top = eval(self.conf.read_config(product=self.product, section='line', name='point_color_top'))  # BGR
        cv.line(original_img, ptStart_top, ptEnd_top, point_color_top, thickness, lineType)

        # 竖线,对准弹子(双排齿为横线)
        if self.row_number == 1:  # 如果为单排齿
            pts_vertical = eval(self.conf.read_config(product=self.product, section='line', name='pts_vertical'))
            pts_vertical_interval = int(self.conf.read_config(product=self.product, section='line', name='pts_vertical_interval'))
            for i in range(self.marble_number):
                if i < 1:
                    continue
                pts_vertical.append(
                    [(pts_vertical[0][0][0] + pts_vertical_interval * i, pts_vertical[0][0][1]),
                     (pts_vertical[0][1][0] + pts_vertical_interval * i, pts_vertical[0][1][1])])
            point_color_vertical = (255, 0, 0)  # BGR
            for pt in pts_vertical:
                cv.line(original_img, pt[0], pt[1], point_color_vertical, thickness, lineType)

            if self_calibration:  # 如果是自动校准
                keyid = 0
                for pt in pts_vertical:
                    for i in range(ptStart_top[1] + 2, ptStart_bottom[1]):
                        if canny_original_img[i][pt[0][0]] == 255:
                            keyid += ptStart_bottom[1] - i
                            break
                keyid = int(keyid / self.marble_number)
                cv.line(original_img, (ptStart_top[0], keyid), (ptEnd_top[0], keyid), point_color_top, thickness,
                        lineType)
                img = QImage(original_img, original_img.shape[1], original_img.shape[0], QImage.Format_RGB888)
            elif check_key_is_ready:  # 如果要判断钥匙是否已到位
                keyid = 0
                for i in range(ptStart_top[1] + 2, ptStart_bottom[1]):
                    if canny_original_img[i][pts_vertical[0][0][0]] == 255:
                        keyid = i
                        break
            elif is_capture:  # 检测keyid
                one = int(self.conf.read_config(product=self.product, section='key', name='one'))
                two = int(self.conf.read_config(product=self.product, section='key', name='two'))
                three = int(self.conf.read_config(product=self.product, section='key', name='three'))
                four = int(self.conf.read_config(product=self.product, section='key', name='four'))
                # 画4条标准线(双排齿画8条)
                cv.line(original_img, (ptStart_top[0], one), (ptEnd_top[0], one), point_color_top, thickness, lineType)
                cv.line(original_img, (ptStart_top[0], two), (ptEnd_top[0], two), point_color_top, thickness, lineType)
                cv.line(original_img, (ptStart_top[0], three), (ptEnd_top[0], three), point_color_top, thickness,
                        lineType)
                cv.line(original_img, (ptStart_top[0], four), (ptEnd_top[0], four), point_color_top, thickness,
                        lineType)
                img = QImage(original_img, original_img.shape[1], original_img.shape[0], QImage.Format_RGB888)

                keyid = ''
                for pt in pts_vertical:
                    for i in range(ptStart_top[1] + 2, ptStart_bottom[1]):
                        if canny_original_img[i][pt[0][0]] == 255:
                            keyid += self.get_keyid((ptStart_bottom[1] - i))
                            break
                        elif i >= ptStart_bottom[1] - 1:
                            keyid += 'X'
        elif self.row_number == 2:  # 如果为双排齿
            # 获取pts_vertical格式为：[[[(x1, y1), (x2, y2)]], [[(x3, y3), (x4, y4)]]]
            pts_vertical = eval(self.conf.read_config(product=self.product, section='line', name='pts_vertical'))
            # 双排齿，弹子线分左边和右边
            pts_vertical_left, pts_vertical_right = pts_vertical
            # 获取弹子间隔,分为左右两部分。pts_vertical_interval的格式为：(number1, number2)
            pts_vertical_left_interval, pts_vertical_right_interval = eval(
                self.conf.read_config(product=self.product, section='line', name='pts_vertical_interval'))
            for i in range(int(self.marble_number/2)):
                if i < 1:
                    continue
                # 获得左边4条线（横坐标一样，纵坐标固定间隔）
                pts_vertical_left.append(
                    [(pts_vertical_left[0][0][0], pts_vertical_left[0][0][1] + pts_vertical_left_interval * i),
                     (pts_vertical_left[0][1][0], pts_vertical_left[0][1][1] + pts_vertical_left_interval * i)])
                # 获得右边4条线（横坐标一样，纵坐标固定间隔）
                pts_vertical_right.append(
                    [(pts_vertical_right[0][0][0], pts_vertical_right[0][0][1] + pts_vertical_right_interval * i),
                     (pts_vertical_right[0][1][0], pts_vertical_right[0][1][1] + pts_vertical_right_interval * i)])
            point_color_vertical = (255, 0, 0)  # BGR
            for pt in pts_vertical_left:
                cv.line(original_img, pt[0], pt[1], point_color_vertical, thickness, lineType)
            for pt in pts_vertical_right:
                cv.line(original_img, pt[0], pt[1], point_color_vertical, thickness, lineType)

            if self_calibration:  # 如果是自动校准
                keyid_left = 0
                keyid_right = 0
                # 左边
                for pt in pts_vertical_left:
                    for i in range(2, ptStart_top[0]):
                        if canny_original_img[pt[0][1]][i] == 255:
                            keyid_left += ptStart_top[0] - i
                            break
                keyid_left = int(keyid_left / self.marble_number)
                cv.line(original_img, (keyid_left, ptStart_top[1]), (keyid_left, ptEnd_top[1]), point_color_top, thickness,
                        lineType)

                # 右边
                for pt in pts_vertical_right:
                    for i in range(ptStart_bottom[0]+2, len(canny_original_img[0])):
                        if canny_original_img[pt[0][1]][i] == 255:
                            keyid_right += i - ptStart_bottom[0]
                            break
                keyid_right = int(keyid_right / self.marble_number)
                cv.line(original_img, (keyid_right, ptStart_bottom[1]), (keyid_right, ptEnd_bottom[1]), point_color_top, thickness,
                        lineType)
                img = QImage(original_img, original_img.shape[1], original_img.shape[0], QImage.Format_RGB888)
                keyid = (keyid_left, keyid_right)
            elif check_key_is_ready:  # 如果要判断钥匙是否已到位
                keyid = 0
                for i in range(2, ptStart_top[0]):
                    if canny_original_img[pts_vertical[0][0][1]][i] == 255:
                        keyid = i
                        break

            elif is_capture:  # 检测keyid
                one = eval(self.conf.read_config(product=self.product, section='key', name='one'))
                two = eval(self.conf.read_config(product=self.product, section='key', name='two'))
                three = eval(self.conf.read_config(product=self.product, section='key', name='three'))
                four = eval(self.conf.read_config(product=self.product, section='key', name='four'))
                # 画4条标准线(双排齿画8条)
                # 左边4条线
                cv.line(original_img, (abs(ptStart_top[0] - one[0]), ptStart_top[1]),
                        (abs(ptEnd_top[0] - one[0]), ptEnd_top[1]), point_color_top, thickness, lineType)
                cv.line(original_img, (abs(ptStart_top[0] - two[0]), ptStart_top[1]),
                        (abs(ptEnd_top[0] - two[0]), ptEnd_top[1]), point_color_top, thickness, lineType)
                cv.line(original_img, (abs(ptStart_top[0] - three[0]), ptStart_top[1]),
                        (abs(ptEnd_top[0] - three[0]), ptEnd_top[1]), point_color_top, thickness, lineType)
                cv.line(original_img, (abs(ptStart_top[0] - four[0]), ptStart_top[1]),
                        (abs(ptEnd_top[0] - four[0]), ptEnd_top[1]), point_color_top, thickness, lineType)
                # 右边4条线
                cv.line(original_img, (one[1] + ptStart_bottom[0], ptStart_bottom[1]),
                        (one[1] + ptEnd_bottom[0], ptEnd_bottom[1]), point_color_top, thickness, lineType)
                cv.line(original_img, (two[1] + ptStart_bottom[0], ptStart_bottom[1]),
                        (two[1] + ptEnd_bottom[0], ptEnd_bottom[1]), point_color_top, thickness, lineType)
                cv.line(original_img, (three[1] + ptStart_bottom[0], ptStart_bottom[1]),
                        (three[1] + ptEnd_bottom[0], ptEnd_bottom[1]), point_color_top, thickness, lineType)
                cv.line(original_img, (four[1] + ptStart_bottom[0], ptStart_bottom[1]),
                        (four[1] + ptEnd_bottom[0], ptEnd_bottom[1]), point_color_top, thickness, lineType)

                keyid_left = ''
                keyid_right = ''
                key_left = []
                key_right = []
                for pt in pts_vertical_left:
                    # x轴的起始坐标
                    # print(ptStart_bottom)
                    for i in range(2, ptStart_top[0]):
                        if canny_original_img[pt[0][1]][i] == 255:
                            keyid_left += self.get_keyid(abs(pt[1][0] - i), left=True)
                            key_left.append(pt[1][0] - i)
                            break
                        elif i >= pt[1][0] - 1:
                            keyid_left += 'X'
                            key_left.append(i)
                            break
                for pt in pts_vertical_right:
                    # x轴的起始坐标
                    # print(pt[0][0], pt[1][0])
                    for i in range(ptStart_bottom[0] + 2, len(canny_original_img[0])):
                        if canny_original_img[pt[0][1]][i] == 255:
                            keyid_right += self.get_keyid(abs(i - ptStart_bottom[0]), right=True)
                            key_right.append(i - ptStart_bottom[0])
                            break
                        elif i >= pt[1][0] - 1:
                            keyid_right += 'X'
                            key_right.append(i)
                            break
                res = [''] * len(keyid_left) * 2
                print(key_right, key_left)
                print(keyid_right, keyid_left)
                res[::2] = keyid_right
                res[1::2] = keyid_left
                print(res)
                keyid = ''.join(res)
        # 形态学：边缘检测
        # _, Thr_img = cv.threshold(original_img, 210, 255, cv.THRESH_BINARY)  # 设定红色通道阈值210（阈值影响梯度运算效果）
        # kernel = cv.getStructuringElement(cv.MORPH_RECT, (5, 5))  # 定义矩形结构元素
        # gradient = cv.morphologyEx(Thr_img, cv.MORPH_GRADIENT, kernel)  # 梯度
        # cv.imshow("original_img", original_img)
        # cv.imshow("gradient", gradient)
        # cv.imshow('Canny', canny)

        # Canny(): 边缘检测
        img1 = cv.GaussianBlur(original_img, (3, 3), 0)
        canny_to_show = cv.Canny(img1, min_threshold, max_threshold)
        return keyid, canny_to_show

    # 获取keyid
    def get_keyid(self, key, left=False, right=False):
        if left:
            one = eval(self.conf.read_config(product=self.product, section='key', name='one'))[0]
            two = eval(self.conf.read_config(product=self.product, section='key', name='two'))[0]
            three = eval(self.conf.read_config(product=self.product, section='key', name='three'))[0]
            four = eval(self.conf.read_config(product=self.product, section='key', name='four'))[0]
            tolerance = eval(self.conf.read_config(product=self.product, section='key', name='tolerance'))[0]
        elif right:
            one = eval(self.conf.read_config(product=self.product, section='key', name='one'))[1]
            two = eval(self.conf.read_config(product=self.product, section='key', name='two'))[1]
            three = eval(self.conf.read_config(product=self.product, section='key', name='three'))[1]
            four = eval(self.conf.read_config(product=self.product, section='key', name='four'))[1]
            tolerance = eval(self.conf.read_config(product=self.product, section='key', name='tolerance'))[1]
        else:
            one = int(self.conf.read_config(product=self.product, section='key', name='one'))
            two = int(self.conf.read_config(product=self.product, section='key', name='two'))
            three = int(self.conf.read_config(product=self.product, section='key', name='three'))
            four = int(self.conf.read_config(product=self.product, section='key', name='four'))
            tolerance = int(self.conf.read_config(product=self.product, section='key', name='tolerance'))
        if one - tolerance < key < one + tolerance:
            return '1'
        elif two - tolerance < key < two + tolerance:
            return '2'
        elif three - tolerance < key < three + tolerance:
            return '3'
        elif four - tolerance < key < four + tolerance:
            return '4'
        else:
            return 'X'

    # 获取keycode
    def get_keycode(self, keyid):
        if self.product == '0开头':  # 如果是0开头的，奇数位需要反转(1变4、2变3、3变2、4变1)
            keyid_odd = keyid[0::2]  # 奇数位
            keyid_even = keyid[1::2]  # 偶数位
            keyid_odd_changed = ''
            for i in keyid_odd:
                if i == '1':
                    i = '4'
                elif i == '2':
                    i = '3'
                elif i == '3':
                    i = '2'
                elif i == '4':
                    i = '1'
                keyid_odd_changed += i
            res = [''] * len(keyid_odd) * 2
            res[::2] = keyid_odd_changed
            res[1::2] = keyid_even
            keyid = ''.join(res)
        try:
            with sqlite3.connect('keyid.db') as conn:
                c = conn.cursor()
                rows = c.execute("SELECT keycode FROM '%s' WHERE keyid='%s'" % (self.product, keyid)).fetchall()
                keycode = rows[0][0]
                self.Ui_MainWindow.label_status.setText('成功读取钥匙号')
                self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(0, 255, 0);')
                return keycode
        except Exception as e:
            self.Ui_MainWindow.label_status.setText('get_keycode:%s' % str(e))
            self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 0, 0);')
            return '----'

    # 截取钥匙图片
    def get_key_capture(self):
        pos = eval(self.conf.read_config(product='config', section="capture_region", name="position"))
        img = ImageGrab.grab(pos)
        img.save('key.jpg')
        self.Ui_MainWindow.label_show_image.setPixmap(QPixmap('key.jpg'))
        return cv.imread("key.jpg")

    # 捕获，测量
    def capture(self):
        print('capture')
        sleep(2)
        keyid, canny = self.edge_detect(is_capture=True)
        print(keyid)
        keycode = self.get_keycode(keyid)
        print(keycode)
        self.Ui_MainWindow.lineEdit_key_code.setText(keycode)
        self.Ui_MainWindow.lineEdit_key_id.setText(keyid)
        return keyid, keycode

    # 钥匙是否插到位
    def key_is_ready(self):
        if self.has_key_sensor:  # 如果有钥匙到位传感器
            key_is_ready = self.siemens.ReadBool('I4.5').Content
            if key_is_ready:  # 如果钥匙到位(I4.5)
                if self.key_last_status:  # 如果之前钥匙已经到位，不做任何处理
                    pass
                else:  # 如果之前钥匙未到位，则将标志位置为True
                    # self.key_is_ready = True
                    # 将本次的钥匙是否到位传感器的状态作为下一次状态的上一状态
                    self.key_last_status = True
                    return True
            else:  # 如果钥匙未到位，则将标志位置为False
                # 将本次的钥匙是否到位传感器的状态作为下一次状态的上一状态
                self.key_last_status = False
                return False
        else:
            # 最底线的纵坐标(双排齿为左侧竖线横坐标)
            if self.row_number == 1:
                base_line = eval(self.conf.read_config('line', 'ptstart_bottom'))[1]
            elif self.row_number == 2:
                base_line = eval(self.conf.read_config('line', 'ptstart_top'))[0]
            keyid = self.edge_detect(check_key_is_ready=True)
            # 如果边缘超过基准线，则表明有钥匙进入
            if keyid < base_line:
                return True
            else:
                return False

    # 条码打印
    def barcode_print(self, product, keycode):
        if product == '280B' or product == '281B' or product == '0开头':
            barcode_bytes = keycode.encode("utf-8")  # 转换为字节格式
            send_data = b'\x1bA\x1bN\x1bR\x1bR\x1bH070\x1bV01282\x1bL0202\x1bS\x1bB103080*' + barcode_bytes + b'*\x1bH0200\x1bV01369\x1bL0202\x1bS' + barcode_bytes + b'\x1bQ1\x1bZ'
        self.com.send_data(send_data)
        self.Ui_MainWindow.label_status.setText('等待读取钥匙号')
        self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 255, 127);')


class VideoThread(QThread):
    signal = Signal()

    def __init__(self):
        super(VideoThread, self).__init__()
        self.working = True  # 工作状态
        # self.cap = cv.VideoCapture(0)
        #
        # if not self.cap.isOpened():
        #     print('无法打开摄像机')
        #     exit()
        #
        # self.img = np.array([])

    def __del__(self):
        self.working = False  # 工作状态
        # When everything done, release the capture
        #  self.cap.release()
        # cv.destroyAllWindows()
        self.wait()

    def run(self):
        # 进行线程任务
        while self.working:
            sleep(0.5)
            # # Capture frame-by-frame
            # ret, frame = self.cap.read()
            # frame = cv.flip(frame, 1)  # 水平翻转
            # # if frame is read correctly ret is True
            # if not ret:
            #     print("Can't receive frame (stream end?). Exiting ...")
            #     break
            #
            # # RGB转BGR
            # frame_bgr = cv.cvtColor(frame, cv.COLOR_RGB2BGR)
            # # Our operations on the frame come here
            # gray = cv.cvtColor(frame, cv.COLOR_RGB2GRAY)
            # self.img = frame_bgr
            # # Display the resulting frame
            # # cv.imshow('frame', gray)
            # # if cv.waitKey(1) == ord('q'):
            # #     break
            self.signal.emit()  # 发射信号


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()
    # window.showMaximized()
    window.show()
    sys.exit(app.exec_())


