# -*- coding:utf-8 -*-
from __future__ import division
import glob
import os
import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter.filedialog import askdirectory
from PIL import Image, ImageTk
import sys
import re
import math

w0 = 1  # 图片原始宽度
h0 = 1  # 图片原始高度
x_old = 0
y_old = 0


# 将元素中的数字转换为int后再排序
def try_int(s):
    try:
        return int(s)
    except ValueError:
        return s


# 将元素中的字符串和数字分割开
def str_2_int(v_str):
    return [try_int(sub_str) for sub_str in re.split('([0-9]+)', v_str)]


# 以分割后的list为单位进行排序
def sort_humanly(v_list):
    return sorted(v_list, key=str_2_int)


def draw_circle(self, x, y, r, **kwargs):
    return self.create_oval(x - r, y - r, x + r, y + r, width=0, **kwargs)


class LabelTool:
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("Landmark Annotation Tool")
        # self.parent.geometry("1000x500")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width=TRUE, height=TRUE)

        # 图片大小
        self.img_w = 500
        self.img_h = 500

        # self.COLORS = ['red', 'blue', 'pink', 'cyan', 'green', 'black',
        #                'FireBrick', 'Salmon', 'SaddleBrown',
        #                'GreenYellow', '#6B8E23']
        self.COLORS = ['blue']
        self.new_COLORS = ['red']

        # initialize global state
        self.imageDir = ''  # 标注图片所在文件夹
        self.imageList = []
        self.af_ann_List = []  # 修正过关键点的图片

        self.outDir = ''  # 保存路径文件夹
        self.txt_kp_List = []  # 如果为修正模式,保存路径下必须有TXT
        self.new_index = []  # 当前图片，修正点的idx，用于改变颜色

        self.cur = 0
        self.total = 0
        self.imagename = ''
        self.save_file_name = ''
        self.tkimg = None

        # reference to kp
        self.pointIdList = []
        self.pointId = None
        self.pointList = []

        # ----------------- GUI 部件 ---------------------
        # dir entry & load
        self.label1 = Label(self.frame, text="*标注图片路径:", font='Helvetica', anchor=E)
        self.label1.grid(row=0, column=1, sticky=E + W)

        self.label2 = Label(self.frame, text="*保存路径:", font='Helvetica', anchor=E)
        self.label2.grid(row=1, column=1, sticky=E + W)

        self.btn1 = Button(self.frame, text="选择图片目录",
                           command=self.get_image_dir, font='Helvetica')
        self.btn1.grid(row=0, column=2, sticky=E + W)

        self.btn2 = Button(self.frame, text="选择保存目录",
                           command=self.get_save_dir, font='Helvetica')
        self.btn2.grid(row=1, column=2, sticky=E + W)

        def_w = tk.StringVar(value='600')
        def_h = tk.StringVar(value='600')
        self.lbs_w = Label(self.frame, text='宽度:', font='Helvetica', anchor=E)
        self.lbs_w.grid(row=2, column=1, sticky=E + W)

        self.entry_w = Entry(self.frame, textvariable=def_w)
        self.entry_w.grid(row=2, column=2, sticky=E + W)

        self.lbs_h = Label(self.frame, text='高度:', font='Helvetica', anchor=E)
        self.lbs_h.grid(row=3, column=1, sticky=E + W)

        self.entry_h = Entry(self.frame, textvariable=def_h)
        self.entry_h.grid(row=3, column=2, sticky=E + W)

        self.img_name_detail = StringVar()
        self.img_name_title = Label(self.frame, text='图片名称:', font='Helvetica', anchor=E)
        self.img_name = Label(self.frame, textvariable=self.img_name_detail)

        self.img_name_title.grid(row=4, column=1, sticky=E + W)
        self.img_name.grid(row=4, column=2, sticky=E + W)

        self.ldBtn = Button(self.frame, text="开始加载", font='Helvetica', command=self.load_dir)
        self.ldBtn.grid(row=5, column=1, columnspan=2, sticky=N + E + W)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, bg='lightgray')
        # 鼠标左键点击
        self.mainPanel.bind("<Button-1>", self.mouse_click)
        # 释放鼠标左键
        self.mainPanel.bind("<ButtonRelease-1>", self.mouse_release)

        self.mainPanel.grid(row=0, column=0, rowspan=9, sticky=W + N + S + E)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text='关键点坐标:', font='Helvetica')
        self.lb1.grid(row=6, column=1, columnspan=2, sticky=N + E + W)

        self.listbox = Listbox(self.frame)  # , width=30, height=15)
        self.listbox.grid(row=7, column=1, columnspan=2, sticky=N + S + E + W)

        self.btnDel = Button(self.frame, text='删除', font='Helvetica', command=self.del_point)
        self.btnDel.grid(row=8, column=1, columnspan=2, sticky=S + E + W)
        self.btnClear = Button(
            self.frame, text='清空', font='Helvetica', command=self.clear_point)
        self.btnClear.grid(row=9, column=1, columnspan=2, sticky=N + E + W)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row=10, column=0, columnspan=3, sticky=E + W + S)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev',
                              width=10, command=self.prev_image)
        self.prevBtn.pack(side=LEFT, padx=5, pady=3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>',
                              width=10, command=self.next_image)
        self.nextBtn.pack(side=LEFT, padx=5, pady=3)
        self.progLabel = Label(self.ctrPanel, text="Progress:     /    ")
        self.progLabel.pack(side=LEFT, padx=5)
        self.tmpLabel = Label(self.ctrPanel, text="Go to Image No.")
        self.tmpLabel.pack(side=LEFT, padx=5)
        self.idxEntry = Entry(self.ctrPanel, width=5)
        self.idxEntry.pack(side=LEFT)
        self.goBtn = Button(self.ctrPanel, text='Go', command=self.goto_image)
        self.goBtn.pack(side=LEFT)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side=RIGHT)

        self.frame.columnconfigure(0, weight=30)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(6, weight=1)

        # menu
        self.menubar = Menu(self.parent)
        self.model_type = ''
        self.menubar.add_command(label='标注模式', font='Helvetica', command=self.model_type1)
        self.menubar.add_command(label='修正模式', font='Helvetica', command=self.model_type2)

        self.parent.config(menu=self.menubar)

    # 标注模式
    def model_type1(self):
        self.model_type = '1'
        messagebox.showinfo(
            title='成功',
            message="标注模式已启动,请在图上进行标注")

    # 修正模式
    def model_type2(self):
        self.model_type = '2'
        messagebox.showinfo(
            title='成功',
            message="修正模式已启动,拖动关键点进行修正")

    # 获取标注图片路径
    def get_image_dir(self):
        self.imageDir = askdirectory()
        print('标注图片路径：', self.imageDir)

    # 获取保存路径
    def get_save_dir(self):
        self.outDir = askdirectory()
        print('保存路径：', self.outDir)

    # 加载选择的文件目录
    def load_dir(self):
        # 选择模式
        if self.model_type == "":
            messagebox.showwarning(
                title='警告', message="请选择操作模式,标注模式or修正模式")
            return

        # 读取并设置图片大小
        if self.entry_h.get() == "" or self.entry_w.get() == "":
            messagebox.showwarning(title="警告", message="不输入图片大小的情况下将默认设置为图片本身大小")
        else:
            self.img_h = int(self.entry_h.get())
            self.img_w = int(self.entry_w.get())
            print("image shape: (%d, %d)" % (self.img_w, self.img_h))

        # 标注图片
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.jpg'))
        self.imageList = sort_humanly(self.imageList)

        # 关键点文档
        self.txt_kp_List = glob.glob(os.path.join(self.outDir, '*.txt'))
        self.txt_kp_List = sort_humanly(self.txt_kp_List)

        # 修正过关键点的图片信息
        self.af_ann_List = [[]] * len(self.imageList)

        # 标注图片路径没有选择
        if len(self.imageList) == 0:
            messagebox.showwarning(
                title='警告', message="标注图片路径中没有jpg结尾的图片")
            return
        else:
            print("num=%d" % (len(self.imageList)))

        # 修正模式必须要有关键点文档
        if self.model_type == "2":
            if len(self.txt_kp_List) == 0:
                messagebox.showwarning(
                    title='警告', message="修正模式下,保存路径中必须要有txt结尾的关键点文档")
                return
            else:
                print("num=%d" % (len(self.txt_kp_List)))

        # 默认当前为第一张图片
        self.cur = 1
        self.total = len(self.imageList)

        # 创建保存路径
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)

        self.load_image()
        print('%d images loaded from %s' % (self.total, self.imageDir))

    # 加载图片
    def load_image(self, reload=False):
        if len(self.imageList) == 0:
            return

        # 清空画板上的点
        self.mainPanel.delete(tk.ALL)
        if not reload:
            self.new_index = []

        # load image
        global w0, h0
        image_path = self.imageList[self.cur - 1]
        pil_image = Image.open(image_path)

        self.af_ann_List[self.cur-1] = pil_image

        # 获取图像的原始大小
        w0, h0 = pil_image.size

        # 缩放到指定大小
        if self.entry_h.get() == "" or self.entry_w.get() == "":
            # 无指定大小，用图片本身大小
            self.img_w, self.img_h = w0, h0

        pil_image = pil_image.resize(
            (self.img_w, self.img_h), Image.ANTIALIAS)
        self.tkimg = ImageTk.PhotoImage(pil_image)

        self.mainPanel.config(width=self.img_w, height=self.img_h)
        self.mainPanel.create_image(
            self.img_w // 2, self.img_h // 2, image=self.tkimg, anchor=CENTER)

        self.progLabel.config(text="%04d/%04d" % (self.cur, self.total))

        # load labels
        self.clear()
        self.imagename = os.path.split(image_path)[-1].split('.')[0]
        self.img_name_detail.set(os.path.split(image_path)[-1].split('/')[0])  # 设置图片名称
        labelname = self.imagename + '.txt'
        self.save_file_name = os.path.join(self.outDir, labelname)

        # 如果保存路径中已经有保存的关键点，将它画出来
        if os.path.exists(self.save_file_name):
            with open(self.save_file_name) as f:
                for (i, line) in enumerate(f):
                    tmp = [(t.strip()) for t in line.split()]
                    # 坐标
                    x1 = float(tmp[0]) / w0 * self.img_w
                    y1 = float(tmp[1]) / h0 * self.img_h
                    # 类似鼠标事件
                    self.pointList.append((tmp[0], tmp[1]))
                    self.pointIdList.append(self.pointId)
                    self.pointId = None
                    self.listbox.insert(
                        END, '%d:(%s, %s)' % (len(self.pointIdList), tmp[0], tmp[1]))
                    if reload and i in self.new_index:
                        self.listbox.itemconfig(
                            len(self.pointIdList) - 1,
                            fg=self.new_COLORS[(len(self.pointIdList) - 1) % len(self.new_COLORS)])
                        draw_circle(self.mainPanel,
                                    x1,
                                    y1,
                                    3,
                                    fill=self.new_COLORS[(len(self.pointIdList) - 1) % len(self.new_COLORS)])
                    else:
                        self.listbox.itemconfig(
                            len(self.pointIdList) - 1,
                            fg=self.COLORS[(len(self.pointIdList) - 1) % len(self.COLORS)])
                        draw_circle(self.mainPanel,
                                    x1,
                                    y1,
                                    3,
                                    fill=self.COLORS[(len(self.pointIdList) - 1) % len(self.COLORS)])

                    tmp[0] = float(tmp[0])
                    tmp[1] = float(tmp[1])

    # 保存关键点信息到文本
    def save_image(self):

        if len(self.pointList) == 0:
            self.del_file()
        else:
            print("Save File Length: %d" % len(self.pointList))

            if self.save_file_name == '':
                print("save file name is empty")
                return

            with open(self.save_file_name, 'w') as f:
                # 关键点坐标
                for point in self.pointList:
                    f.write(' '.join(map(str, point)) + '\n')
            print('Image No. %d saved' % self.cur)

    # 鼠标点击（标注）
    def mouse_click(self, event):
        if len(self.imageList) == 0:
            messagebox.showwarning(
                title='警告', message="请选择图片目录")
            return
        x1, y1 = event.x, event.y
        # 0-1
        x1 = x1 / self.img_w
        y1 = y1 / self.img_h
        if x1 < 1 and y1 < 1:

            if self.model_type == '1':
                # 标注模式，直接将手动标注的点进行显示
                self.pointList.append((round(x1 * w0, 5), round(y1 * h0, 5)))
                self.pointIdList.append(self.pointId)
                self.pointId = None

                self.listbox.insert(END, '%d:(%.2f, %.2f)' %
                                    (len(self.pointIdList), x1, y1))

                self.listbox.itemconfig(
                    len(self.pointIdList) - 1, fg=self.COLORS[(len(self.pointIdList) - 1) % len(self.COLORS)])
                draw_circle(self.mainPanel,
                            x1 * self.img_w,
                            y1 * self.img_h,
                            3,
                            fill=self.COLORS[(len(self.pointIdList) - 1) % len(self.COLORS)])
            elif self.model_type == '2':
                # 修正模式，得到初始点坐标
                global x_old, y_old
                x_old, y_old = event.x / self.img_w * w0, event.y / self.img_h * h0

    # 鼠标释放（修正）
    def mouse_release(self, event):
        if self.model_type == '2':
            x1, y1 = event.x, event.y
            # 0-1之间
            x1 = x1 / self.img_w
            y1 = y1 / self.img_h
            if x1 < 1 and y1 < 1:

                index = self.find_closer()
                self.new_index.append(index)
                self.new_index.sort()

                self.pointList[index] = (round(x1 * w0, 5), round(y1 * h0, 5))
                self.save_image()
                self.load_image(reload=True)

    # 修正模式，查找离鼠标点击时最接近的点
    def find_closer(self):
        result = -1
        min_dis = sys.maxsize
        for i in range(len(self.pointList)):
            x = float(self.pointList[i][0])
            y = float(self.pointList[i][1])
            d_x = x - x_old
            d_y = y - y_old
            distance = math.sqrt(d_x ** 2 + d_y ** 2)
            if distance < min_dis:
                min_dis = distance
                result = i
        return result

    # 删除按钮
    def del_point(self):
        sel = self.listbox.curselection()
        if len(sel) != 1:
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.pointIdList[idx])
        self.pointIdList.pop(idx)
        self.pointList.pop(idx)
        self.listbox.delete(idx)
        if idx in self.new_index:
            self.new_index.pop(idx)

        if len(self.pointList) == 0:
            self.del_file()
        else:
            self.save_image()
        self.load_image()

    # 清空按钮
    def clear_point(self):
        for idx in range(len(self.pointIdList)):
            self.mainPanel.delete(self.pointIdList[idx])
        self.listbox.delete(0, len(self.pointList))
        self.pointIdList = []
        self.pointList = []

        self.del_file()
        self.load_image()

    # 删除保存的文件
    def del_file(self):
        if os.path.isfile(self.save_file_name):
            os.remove(self.save_file_name)

    # 清空数据
    def clear(self):
        for idx in range(len(self.pointIdList)):
            self.mainPanel.delete(self.pointIdList[idx])
        self.listbox.delete(0, len(self.pointList))
        self.pointIdList = []
        self.pointList = []

    # 加载前一张图片
    def prev_image(self):
        self.save_image()
        print("image shape: (%d, %d)" % (self.img_w, self.img_h))
        if self.cur > 1:
            self.cur -= 1
            self.load_image()

    # 加载后一张图片
    def next_image(self):
        self.save_image()
        print("image shape: (%d, %d)" % (self.img_w, self.img_h))
        if self.cur < self.total:
            self.cur += 1
            self.load_image()

        if self.cur == self.total:
            messagebox.showinfo(title="提示", message="已全部加载完")

    # 加载输入编号的图片
    def goto_image(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx <= self.total:
            self.save_image()
            self.cur = idx
            self.load_image()


if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.mainloop()
