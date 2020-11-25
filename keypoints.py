# -*- coding:utf-8 -*-
from __future__ import division
import glob
import os
import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter.filedialog import askdirectory
from PIL import Image, ImageTk
import re


w0 = 1  # 图片原始宽度
h0 = 1  # 图片原始高度


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
    return self.create_oval(x-r, y-r, x+r, y+r, width=0, **kwargs)


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

        self.COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black',
                       'Gainsboro', 'FireBrick', 'Salmon', 'SaddleBrown', 'Linen', 'Wheat',
                       'Cornsilk', 'GreenYellow', '#6B8E23']

        # initialize global state
        self.imageDir = ''  # 图片所在文件夹
        self.imageList = []

        self.outDir = ''  # 输出文件夹

        self.cur = 0
        self.total = 0
        self.imagename = ''
        self.labelfilename = ''
        self.tkimg = None

        # reference to bbox
        self.pointIdList = []
        self.pointId = None
        self.pointList = []

        # ----------------- GUI 部件 ---------------------
        # dir entry & load
        self.label1 = Label(self.frame, text="ImageDir:")
        self.label1.grid(row=0, column=1, sticky=E+W)

        self.label2 = Label(self.frame, text="SaveDir:")
        self.label2.grid(row=1, column=1, sticky=E+W)

        self.btn1 = Button(self.frame, text="选择图片目录",
                           command=self.get_image_dir, font='Helvetica')
        self.btn1.grid(row=0, column=2, sticky=E+W)

        self.btn2 = Button(self.frame, text="选择保存目录",
                           command=self.get_save_dir, font='Helvetica')
        self.btn2.grid(row=1, column=2, sticky=E+W)

        self.lbs_w = Label(self.frame, text='width:')
        self.lbs_w.grid(row=2, column=1, sticky=E+W)

        self.entry_w = Entry(self.frame)
        self.entry_w.grid(row=2, column=2, sticky=E+W)

        self.lbs_h = Label(self.frame, text='height:')
        self.lbs_h.grid(row=3, column=1, sticky=E+W)

        self.entry_h = Entry(self.frame)
        self.entry_h.grid(row=3, column=2, sticky=E+W)

        self.img_name_detail = StringVar()
        self.img_name_title = Label(self.frame, text='图片名称:', font='Helvetica')
        self.img_name = Label(self.frame, textvariable=self.img_name_detail)

        self.img_name_title.grid(row=4, column=1, sticky=E+W)
        self.img_name.grid(row=4, column=2, sticky=E+W)

        self.ldBtn = Button(self.frame, text="开始加载", font='Helvetica', command=self.load_dir)
        self.ldBtn.grid(row=5, column=1, columnspan=2, sticky=N+E+W)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, bg='lightgray')
        # 鼠标左键点击
        self.mainPanel.bind("<Button-1>", self.mouse_click)
        self.mainPanel.grid(row=0, column=0, rowspan=9, sticky=W+N+S+E)
        # 快捷键
        # self.parent.bind("s", self.save_all)
        # self.parent.bind("a", self.prev_image)  # press 'a' to go backforward
        # self.parent.bind("d", self.next_image)  # press 'd' to go forward

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text='关键点坐标:', font='Helvetica')
        self.lb1.grid(row=6, column=1, columnspan=2, sticky=N+E+W)

        self.listbox = Listbox(self.frame)  # , width=30, height=15)
        self.listbox.grid(row=7, column=1, columnspan=2, sticky=N+S+E+W)

        self.btnDel = Button(self.frame, text='删除', font='Helvetica', command=self.del_point)
        self.btnDel.grid(row=8, column=1, columnspan=2, sticky=S+E+W)
        self.btnClear = Button(
            self.frame, text='清空', font='Helvetica', command=self.clear_point)
        self.btnClear.grid(row=9, column=1, columnspan=2, sticky=N+E+W)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row=10, column=0, columnspan=3, sticky=E+W+S)
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
        self.helpmenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='帮助', font='Helvetica', menu=self.helpmenu)

        self.helpmenu.add_command(label='使用说明', font='Helvetica', command=self.usage)

        self.parent.config(menu=self.menubar)

    def usage(self):
        messagebox.showinfo(
            title='使用说明',
            message="1. 选择图片所在路径\n"
                    "2. 选择保存路径\n"
                    "3.设置保存图片大小(如果不设置就按照默认图片默认分辨率计算)\n"
                    "4. 点击开始加载")

    def get_image_dir(self):
        self.imageDir = askdirectory()
        print(self.imageDir)

    def get_save_dir(self):
        self.outDir = askdirectory()
        print(self.outDir)

    def load_dir(self):

        # 读取并设置图片大小
        if self.entry_h.get() == "" or self.entry_w.get() == "":
            messagebox.showwarning(title="警告", message="不输入图片大小的情况下将默认设置为图片本身大小")
        else:
            self.img_h = int(self.entry_h.get())
            self.img_w = int(self.entry_w.get())
            print("image shape: (%d, %d)" % (self.img_w, self.img_h))

        self.imageList = glob.glob(os.path.join(self.imageDir, '*.jpg'))
        self.imageList = sort_humanly(self.imageList)
        if len(self.imageList) == 0:
            print('No .jpg images found in the specified dir!')
            messagebox.showwarning(
                title='警告', message="对应图片文件夹中没有jpg结尾的图片")
            return
        else:
            print("num=%d" % (len(self.imageList)))

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)

        self.load_image()
        print('%d images loaded from %s' % (self.total, self.imageDir))

    def load_image(self):
        # 清空画板上的点
        self.mainPanel.delete(tk.ALL)
        # load image
        imagepath = self.imageList[self.cur - 1]
        pil_image = Image.open(imagepath)
        # get the size of the image
        # 获取图像的原始大小
        global w0, h0
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
            self.img_w//2, self.img_h//2, image=self.tkimg, anchor=CENTER)

        self.progLabel.config(text="%04d/%04d" % (self.cur, self.total))

        # load labels
        self.clear()
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        self.img_name_detail.set(os.path.split(imagepath)[-1].split('/')[0])
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)

        # 如果保存路径中已经有保存的关键点，将它画出来
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                for (i, line) in enumerate(f):
                    if i == 0:
                        # 第一行是关键点的数量
                        continue
                    tmp = [(t.strip()) for t in line.split()]
                    # 0-1之间
                    x1 = float(tmp[0])*self.img_w
                    y1 = float(tmp[1])*self.img_h
                    # 类似鼠标事件
                    self.pointList.append((tmp[0], tmp[1]))
                    self.pointIdList.append(self.pointId)
                    self.pointId = None
                    self.listbox.insert(
                        END, '%d:(%s, %s)' % (len(self.pointIdList), tmp[0], tmp[1]))
                    self.listbox.itemconfig(
                        len(self.pointIdList) - 1, fg=self.COLORS[(len(self.pointIdList) - 1) % len(self.COLORS)])
                    draw_circle(self.mainPanel, x1, y1, 2, fill=self.COLORS[(
                        len(self.pointIdList) - 1) % len(self.COLORS)])

                    tmp[0] = float(tmp[0])
                    tmp[1] = float(tmp[1])

    def save_image(self):
        print("Save File Length: %d" % len(self.pointList))

        if self.labelfilename == '':
            print("label file name is empty")
            return

        with open(self.labelfilename, 'w') as f:
            f.write('%d\n' % len(self.pointList))
            for point in self.pointList:
                f.write(' '.join(map(str, point)) + '\n')
        print('Image No. %d saved' % self.cur)

    def save_all(self):
        with open(self.labelfilename, 'w') as f:
            f.write('%d\n' % len(self.pointList))
            for point in self.pointList:
                f.write(' '.join(map(str, point)) + '\n')
        print('Image No. %d saved' % self.cur)

    def mouse_click(self, event):
        if len(self.imageList) == 0:
            messagebox.showwarning(
                title='警告', message="请选择图片目录")
            return
        x1, y1 = event.x, event.y
        # 0-1之间
        x1 = x1/self.img_w
        y1 = y1/self.img_h
        if x1 < 1 and y1 < 1:
            self.pointList.append((x1, y1))
            self.pointIdList.append(self.pointId)
            self.pointId = None

            self.listbox.insert(END, '%d:(%.2f, %.2f)' %
                                (len(self.pointIdList), x1, y1))

            print(len(self.pointList), self.COLORS[(
                len(self.pointIdList) - 1) % len(self.COLORS)])
            self.listbox.itemconfig(
                len(self.pointIdList) - 1, fg=self.COLORS[(len(self.pointIdList) - 1) % len(self.COLORS)])
            draw_circle(self.mainPanel, x1*self.img_w, y1*self.img_h, 2, fill=self.COLORS[(
                len(self.pointIdList) - 1) % len(self.COLORS)])

    def del_point(self):
        sel = self.listbox.curselection()
        if len(sel) != 1:
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.pointIdList[idx])
        self.pointIdList.pop(idx)
        self.pointList.pop(idx)
        self.listbox.delete(idx)

        self.save_image()
        self.load_image()

    def clear_point(self):
        for idx in range(len(self.pointIdList)):
            self.mainPanel.delete(self.pointIdList[idx])
        self.listbox.delete(0, len(self.pointList))
        self.pointIdList = []
        self.pointList = []

        self.save_image()
        self.load_image()
    
    def clear(self):
        for idx in range(len(self.pointIdList)):
            self.mainPanel.delete(self.pointIdList[idx])
        self.listbox.delete(0, len(self.pointList))
        self.pointIdList = []
        self.pointList = []

    def prev_image(self):
        self.save_image()
        print("image shape: (%d, %d)" % (self.img_w, self.img_h))
        if self.cur > 1:
            self.cur -= 1
            self.load_image()

    def next_image(self):
        self.save_image()
        print("image shape: (%d, %d)" % (self.img_w, self.img_h))
        if self.cur < self.total:
            self.cur += 1
            self.load_image()

        if self.cur == self.total:
            messagebox.showinfo(title="提示", message="已全部加载完")

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
