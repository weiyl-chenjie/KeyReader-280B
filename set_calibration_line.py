# python自带库
import sys
# 第三方库
import cv2 as cv
from PySide2.QtWidgets import QWidget, QApplication
# 自己的包
from UI2PY.set_calibration_line import Ui_Form
from config import Config


class SetCalibrationLine(QWidget, Ui_Form):
    def __init__(self):
        super(SetCalibrationLine, self).__init__()
        self.setupUi(self)
        self.conf = Config()
        self.plant = self.conf.read_config(product='config', section='product', name='plant')
        self.product = self.conf.read_config(product='config', section='product', name='product')
        self.marble_number = int(self.conf.read_config(product='config', section='product', name='marble_number'))
        self.row_number = int(self.conf.read_config(product='config', section='product', name='row_number'))
        self.setup()

    def setup(self):
        self.product = self.conf.read_config(product='config', section='product', name='product')
        ptStart_bottom_x, ptStart_bottom_y = eval(
            self.conf.read_config(product=self.product, section='line', name='ptStart_bottom'))
        ptEnd_bottom_x, ptEnd_bottom_y = eval(
            self.conf.read_config(product=self.product, section='line', name='ptEnd_bottom'))
        ptStart_top_x, ptStart_top_y = eval(
            self.conf.read_config(product=self.product, section='line', name='ptStart_top'))
        ptEnd_top_x, ptEnd_top_y = eval(self.conf.read_config(product=self.product, section='line', name='ptEnd_top'))

        min_threshold = int(self.conf.read_config(product=self.product, section='canny', name='min_threshold'))
        max_threshold = int(self.conf.read_config(product=self.product, section='canny', name='max_threshold'))

        if self.row_number == 1:  # 如果是单排齿
            pts_vertical = eval(self.conf.read_config(product=self.product, section='line', name='pts_vertical'))
            pts_vertical_start, pts_vertical_end = pts_vertical[0]
            pts_vertical_start_x, pts_vertical_start_y = pts_vertical_start
            pts_vertical_end_x, pts_vertical_end_y = pts_vertical_end
            # 获取弹子间隔
            pts_vertical_interval = int(self.conf.read_config(product=self.product, section='line', name='pts_vertical_interval'))

            self.label_marble_line_start_right.setEnabled(False)
            self.label_marble_line_end_right.setEnabled(False)
            self.spinBox_pts_vertical_start_x_right.setEnabled(False)
            self.spinBox_pts_vertical_start_y_right.setEnabled(False)
            self.spinBox_pts_vertical_end_x_right.setEnabled(False)
            self.spinBox_pts_vertical_end_y_right.setEnabled(False)
            self.label_marble_interval_right.setEnabled(False)
            self.spinBox_pts_vertical_interval_right.setEnabled(False)
        elif self.row_number == 2:  # 如果是双排齿
            # 获取pts_vertical格式为：[[[(x1, y1), (x2, y2)]], [[(x3, y3), (x4, y4)]]]
            pts_vertical = eval(self.conf.read_config(product=self.product, section='line', name='pts_vertical'))
            # 双排齿，弹子线分左边和右边,格式为:[[(x1, y1), (x2, y2)]]
            pts_vertical_left, pts_vertical_right = pts_vertical
            # 左侧线
            pts_vertical_start_x, pts_vertical_start_y = pts_vertical_left[0][0]
            pts_vertical_end_x, pts_vertical_end_y = pts_vertical_left[0][1]
            # 右侧线
            pts_vertical_start_x_right, pts_vertical_start_y_right = pts_vertical_right[0][0]
            pts_vertical_end_x_right, pts_vertical_end_y_right = pts_vertical_right[0][1]
            # 获取弹子间隔,分为左右两部分。pts_vertical_interval的格式为：(number1, number2)
            pts_vertical_interval, pts_vertical_interval_right = eval(
                self.conf.read_config(product=self.product, section='line', name='pts_vertical_interval'))

            self.spinBox_pts_vertical_start_x_right.setValue(pts_vertical_start_x_right)
            self.spinBox_pts_vertical_start_y_right.setValue(pts_vertical_start_y_right)
            self.spinBox_pts_vertical_end_x_right.setValue(pts_vertical_end_x_right)
            self.spinBox_pts_vertical_end_y_right.setValue(pts_vertical_end_y_right)
            self.spinBox_pts_vertical_interval_right.setValue(pts_vertical_interval_right)

        self.spinBox_ptStart_bottom_x.setValue(ptStart_bottom_x)
        self.spinBox_ptStart_bottom_y.setValue(ptStart_bottom_y)
        self.spinBox_ptEnd_bottom_x.setValue(ptEnd_bottom_x)
        self.spinBox_ptEnd_bottom_y.setValue(ptEnd_bottom_y)

        self.spinBox_ptStart_top_x.setValue(ptStart_top_x)
        self.spinBox_ptStart_top_y.setValue(ptStart_top_y)
        self.spinBox_ptEnd_top_x.setValue(ptEnd_top_x)
        self.spinBox_ptEnd_top_y.setValue(ptEnd_top_y)

        self.spinBox_pts_vertical_start_x.setValue(pts_vertical_start_x)
        self.spinBox_pts_vertical_start_y.setValue(pts_vertical_start_y)
        self.spinBox_pts_vertical_end_x.setValue(pts_vertical_end_x)
        self.spinBox_pts_vertical_end_y.setValue(pts_vertical_end_y)
        self.spinBox_pts_vertical_interval.setValue(pts_vertical_interval)

        self.spinBox_min_threshold.setValue(min_threshold)
        self.spinBox_max_threshold.setValue(max_threshold)

    def check(self):
        print('点击了查看')
        # cap = cv.VideoCapture(0)
        # res, original_img = cap.read()
        # original_img = cv.flip(original_img, 1)  # 水平翻转
        original_img = cv.imread("key.jpg")
        # 画线的粗细和类型
        thickness = int(self.conf.read_config(product=self.product, section='line', name='thickness'))
        lineType = int(self.conf.read_config(product=self.product, section='line', name='lineType'))
        # 底线起点和终点的坐标
        ptStart_bottom = (self.spinBox_ptStart_bottom_x.value(), self.spinBox_ptStart_bottom_y.value())
        ptEnd_bottom = (self.spinBox_ptEnd_bottom_x.value(), self.spinBox_ptEnd_bottom_y.value())
        point_color_bottom = eval(self.conf.read_config(product=self.product, section='line', name='point_color_bottom'))  # BGR
        cv.line(original_img, ptStart_bottom, ptEnd_bottom, point_color_bottom, thickness, lineType)

        # 顶线起点和终点的坐标
        ptStart_top = (self.spinBox_ptStart_top_x.value(), self.spinBox_ptStart_top_y.value())
        ptEnd_top = (self.spinBox_ptEnd_top_x.value(), self.spinBox_ptEnd_top_y.value())
        point_color_top = eval(self.conf.read_config(product=self.product, section='line', name='point_color_top'))  # BGR
        cv.line(original_img, ptStart_top, ptEnd_top, point_color_top, thickness, lineType)

        # 弹子线（对准弹子）
        if self.row_number == 1:  # 如果是单排齿
            pts_vertical = [[(self.spinBox_pts_vertical_start_x.value(), self.spinBox_pts_vertical_start_y.value()),
                            (self.spinBox_pts_vertical_end_x.value(), self.spinBox_pts_vertical_end_y.value())]]
            pts_vertical_interval = self.spinBox_pts_vertical_interval.value()
            for i in range(self.marble_number):
                if i < 1:
                    continue
                pts_vertical.append(
                    [(pts_vertical[0][0][0] + pts_vertical_interval * i, pts_vertical[0][0][1]),
                     (pts_vertical[0][1][0] + pts_vertical_interval * i, pts_vertical[0][1][1])])
            point_color_vertical = (255, 0, 0)  # BGR
            for pt in pts_vertical:
                cv.line(original_img, pt[0], pt[1], point_color_vertical, thickness, lineType)
        elif self.row_number == 2:  # 如果是双排齿
            # 获取pts_vertical格式为：[[[(x1, y1), (x2, y2)]], [[(x3, y3), (x4, y4)]]]
            pts_vertical = [[[(self.spinBox_pts_vertical_start_x.value(), self.spinBox_pts_vertical_start_y.value()),
                            (self.spinBox_pts_vertical_end_x.value(), self.spinBox_pts_vertical_end_y.value())]],
                            [[(self.spinBox_pts_vertical_start_x_right.value(), self.spinBox_pts_vertical_start_y_right.value()),
                              (self.spinBox_pts_vertical_end_x_right.value(), self.spinBox_pts_vertical_end_y_right.value())]]]
            # 双排齿，弹子线分左边和右边
            pts_vertical_left, pts_vertical_right = pts_vertical
            # 获取弹子间隔,分为左右两部分。pts_vertical_interval的格式为：(number1, number2)
            pts_vertical_left_interval, pts_vertical_right_interval = (self.spinBox_pts_vertical_interval.value(),
                                                                           self.spinBox_pts_vertical_interval_right.value())
            for i in range(int(self.marble_number / 2)):
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

        # canny(): 边缘检测
        img1 = cv.GaussianBlur(original_img, (3, 3), 0)
        canny = cv.Canny(img1, self.spinBox_min_threshold.value(), self.spinBox_max_threshold.value())
        # cap.release()
        cv.imshow('Canny', canny)
        cv.imshow('orignal', original_img)
        cv.waitKey(0)
        cv.destroyAllWindows()

    def submit(self):
        ptStart_bottom = (self.spinBox_ptStart_bottom_x.value(), self.spinBox_ptStart_bottom_y.value())
        ptEnd_bottom = (self.spinBox_ptEnd_bottom_x.value(), self.spinBox_ptEnd_bottom_y.value())
        ptStart_top = (self.spinBox_ptStart_top_x.value(), self.spinBox_ptStart_top_y.value())
        ptEnd_top = (self.spinBox_ptEnd_top_x.value(), self.spinBox_ptEnd_top_y.value())
        min_threshold = self.spinBox_min_threshold.value()
        max_threshold = self.spinBox_max_threshold.value()
        if self.row_number == 1:  # 如果是单排齿
            pts_vertical = [[(self.spinBox_pts_vertical_start_x.value(), self.spinBox_pts_vertical_start_y.value()),
                            (self.spinBox_pts_vertical_end_x.value(), self.spinBox_pts_vertical_end_y.value())]]
            pts_vertical_interval = self.spinBox_pts_vertical_interval.value()
        elif self.row_number == 2:  # 如果是双排齿
            pts_vertical = [[[(self.spinBox_pts_vertical_start_x.value(), self.spinBox_pts_vertical_start_y.value()),
                             (self.spinBox_pts_vertical_end_x.value(), self.spinBox_pts_vertical_end_y.value())]],
                            [[(self.spinBox_pts_vertical_start_x_right.value(), self.spinBox_pts_vertical_start_y_right.value()),
                             (self.spinBox_pts_vertical_end_x_right.value(), self.spinBox_pts_vertical_end_y_right.value())]]]
            pts_vertical_interval = (self.spinBox_pts_vertical_interval.value(), self.spinBox_pts_vertical_interval_right.value())
        self.product = self.conf.read_config(product='config', section='product', name='product')
        self.conf.update_config(product=self.product, section='line', name='ptStart_bottom', value=str(ptStart_bottom))
        self.conf.update_config(product=self.product, section='line', name='ptEnd_bottom', value=str(ptEnd_bottom))
        self.conf.update_config(product=self.product, section='line', name='ptStart_top', value=str(ptStart_top))
        self.conf.update_config(product=self.product, section='line', name='ptEnd_top', value=str(ptEnd_top))
        self.conf.update_config(product=self.product, section='line', name='pts_vertical', value=str(pts_vertical))
        self.conf.update_config(product=self.product, section='line', name='pts_vertical_interval', value=str(pts_vertical_interval))
        self.conf.update_config(product=self.product, section='canny', name='min_threshold', value=str(min_threshold))
        self.conf.update_config(product=self.product, section='canny', name='max_threshold', value=str(max_threshold))
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = SetCalibrationLine()
    demo.show()
    sys.exit(app.exec_())
