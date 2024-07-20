import argparse
import asyncio
import sys
import json
import pycorrector
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget  
from PyQt5.QtCore import QThread, pyqtSignal  
import chardet

try:
    import numpy as np
except ImportError:
    print("请先安装 numpy . 可以使用命令")
    print()
    print("  pip install numpy")
    print()
    print("安装")
    sys.exit(-1)

#import nest_asyncio#调用,此库用于解决JupyterNotebook中无法使用asyncio问题
#nest_asyncio.apply()

try:
    import sounddevice as sd
except ImportError:
    print("请先安装 sounddevice . 可以使用命令")
    print()
    print("  pip install sounddevice")
    print()
    print("安装")
    sys.exit(-1)

try:
    import websockets
except ImportError:
    print("请运行")
    print("")
    print("  pip install websockets")
    print("")
    print("在你运行脚本之前")
    print("")
    sys.exit(-1)

import sys  
# -*- coding:utf-8 -*-
import sys

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QFont, QEnterEvent, QPainter, QColor, QPen
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel,QSpacerItem, QSizePolicy, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit,QTextBrowser,QSplitter
import math
from titleBar import TitleBar

# 枚举左上右下以及四个定点
Left, Top, Right, Bottom, LeftTop, RightTop, LeftBottom, RightBottom = range(8)

class DesktopWidget(QWidget):

    # 四周边距
    Margins = 5

    def __init__(self, *args, **kwargs):
        super(DesktopWidget, self).__init__(*args, **kwargs)
        self._pressed = False
        self.Direction = None
        # 背景透明
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # 无边框
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.Tool|Qt.WindowStaysOnTopHint)  # 隐藏边框
        # 鼠标跟踪
        self.setMouseTracking(True)
        # 布局
        layout = QVBoxLayout(self, spacing=0)
        # 预留边界用于实现无边框窗口调整大小
        layout.setContentsMargins(
            self.Margins, self.Margins, self.Margins, self.Margins)
        # 标题栏
        self.titleBar = TitleBar(self)
        layout.addWidget(self.titleBar)
        # 信号槽
        self.titleBar.windowMinimumed.connect(self.showMinimized)
        self.titleBar.windowMaximumed.connect(self.showMaximized)
        self.titleBar.windowNormaled.connect(self.showNormal)
        self.titleBar.windowClosed.connect(self.close)
        self.titleBar.windowMoved.connect(self.move)
        self.windowTitleChanged.connect(self.titleBar.setTitle)
        self.windowIconChanged.connect(self.titleBar.setIcon)

        self.worker = Worker()  
        self.worker.finished.connect(self.onTaskFinished) 

        self.startTask()
  
    def startTask(self):  
        self.worker.start()  
  
    def onTaskFinished(self):  
        print("任务完成！")  

    def setTitleBarHeight(self, height=38):
        """设置标题栏高度"""
        self.titleBar.setHeight(height)

    def setIconSize(self, size):
        """设置图标的大小"""
        self.titleBar.setIconSize(size)

    def setWidget(self, widget):
        """设置自己的控件"""
        if hasattr(self, '_widget'):
            return
        self._widget = widget
        # 设置默认背景颜色,否则由于受到父窗口的影响导致透明
        self._widget.setAutoFillBackground(True)
        palette = self._widget.palette()
        palette.setColor(palette.Window, QColor(240, 240, 240))
        self._widget.setPalette(palette)
        # self._widget.installEventFilter(self)
        self.layout().addWidget(self._widget)

    def move(self, pos):
        if self.windowState() == Qt.WindowMaximized or self.windowState() == Qt.WindowFullScreen:
            # 最大化或者全屏则不允许移动
            return
        super(DesktopWidget, self).move(pos)

    def showMaximized(self):
        """最大化,要去除上下左右边界,如果不去除则边框地方会有空隙"""
        super(DesktopWidget, self).showMaximized()
        self.layout().setContentsMargins(0, 0, 0, 0)

    def showNormal(self):
        """还原,要保留上下左右边界,否则没有边框无法调整"""
        super(DesktopWidget, self).showNormal()
        self.layout().setContentsMargins(
            self.Margins, self.Margins, self.Margins, self.Margins)

    def eventFilter(self, obj, event):
        """事件过滤器,用于解决鼠标进入其它控件后还原为标准鼠标样式"""
        if isinstance(event, QEnterEvent):
            self.setCursor(Qt.ArrowCursor)
        return super(DesktopWidget, self).eventFilter(obj, event)

    def paintEvent(self, event):
        """由于是全透明背景窗口,重绘事件中绘制透明度为1的难以发现的边框,用于调整窗口大小"""
        super(DesktopWidget, self).paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 255, 255, 1), 2 * self.Margins))
        painter.drawRect(self.rect())

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        super(DesktopWidget, self).mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self._mpos = event.pos()
            self._pressed = True

    def mouseReleaseEvent(self, event):
        '''鼠标弹起事件'''
        super(DesktopWidget, self).mouseReleaseEvent(event)
        self._pressed = False
        self.Direction = None

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        super(DesktopWidget, self).mouseMoveEvent(event)
        pos = event.pos()
        xPos, yPos = pos.x(), pos.y()
        wm, hm = self.width() - self.Margins, self.height() - self.Margins
        if self.isMaximized() or self.isFullScreen():
            self.Direction = None
            self.setCursor(Qt.ArrowCursor)
            return
        if event.buttons() == Qt.LeftButton and self._pressed:
            self._resizeWidget(pos)
            return
        if xPos <= self.Margins and yPos <= self.Margins:
            # 左上角
            self.Direction = LeftTop
            self.setCursor(Qt.SizeFDiagCursor)
        elif wm <= xPos <= self.width() and hm <= yPos <= self.height():
            # 右下角
            self.Direction = RightBottom
            self.setCursor(Qt.SizeFDiagCursor)
        elif wm <= xPos and yPos <= self.Margins:
            # 右上角
            self.Direction = RightTop
            self.setCursor(Qt.SizeBDiagCursor)
        elif xPos <= self.Margins and hm <= yPos:
            # 左下角
            self.Direction = LeftBottom
            self.setCursor(Qt.SizeBDiagCursor)
        elif 0 <= xPos <= self.Margins and self.Margins <= yPos <= hm:
            # 左边
            self.Direction = Left
            self.setCursor(Qt.SizeHorCursor)
        elif wm <= xPos <= self.width() and self.Margins <= yPos <= hm:
            # 右边
            self.Direction = Right
            self.setCursor(Qt.SizeHorCursor)
        elif self.Margins <= xPos <= wm and 0 <= yPos <= self.Margins:
            # 上面
            self.Direction = Top
            self.setCursor(Qt.SizeVerCursor)
        elif self.Margins <= xPos <= wm and hm <= yPos <= self.height():
            # 下面
            self.Direction = Bottom
            self.setCursor(Qt.SizeVerCursor)

    def _resizeWidget(self, pos):
        """调整窗口大小"""
        if self.Direction == None:
            return
        mpos = pos - self._mpos
        xPos, yPos = mpos.x(), mpos.y()
        geometry = self.geometry()
        x, y, w, h = geometry.x(), geometry.y(), geometry.width(), geometry.height()
        if self.Direction == LeftTop:  # 左上角
            if w - xPos > self.minimumWidth():
                x += xPos
                w -= xPos
            if h - yPos > self.minimumHeight():
                y += yPos
                h -= yPos
        elif self.Direction == RightBottom:  # 右下角
            if w + xPos > self.minimumWidth():
                w += xPos
                self._mpos = pos
            if h + yPos > self.minimumHeight():
                h += yPos
                self._mpos = pos
        elif self.Direction == RightTop:  # 右上角
            if h - yPos > self.minimumHeight():
                y += yPos
                h -= yPos
            if w + xPos > self.minimumWidth():
                w += xPos
                self._mpos.setX(pos.x())
        elif self.Direction == LeftBottom:  # 左下角
            if w - xPos > self.minimumWidth():
                x += xPos
                w -= xPos
            if h + yPos > self.minimumHeight():
                h += yPos
                self._mpos.setY(pos.y())
        elif self.Direction == Left:  # 左边
            if w - xPos > self.minimumWidth():
                x += xPos
                w -= xPos
            else:
                return
        elif self.Direction == Right:  # 右边
            if w + xPos > self.minimumWidth():
                w += xPos
                self._mpos = pos
            else:
                return
        elif self.Direction == Top:  # 上面
            if h - yPos > self.minimumHeight():
                y += yPos
                h -= yPos
            else:
                return
        elif self.Direction == Bottom:  # 下面
            if h + yPos > self.minimumHeight():
                h += yPos
                self._mpos = pos
            else:
                return
        self.setGeometry(x, y, w, h)
    
    def setZmText(self):
        super(DesktopWidget, self).setText()


class Custom(QWidget):
    def paintEvent(self,event):
        #初始化绘图工具
        qp=QPainter()
        #开始在窗口绘制
        qp.begin(self)
        #自定义画点方法
        self.drawPoints(qp)
        #结束在窗口的绘制
        qp.end()

    def drawPoints(self,qp):
        qp.setPen(Qt.red)
        size=self.size()

        for i in range(1000):
            #绘制郑玄函数图像，它的周期是【-100,100】
            x=100*(-1+2.0*i/1000)+size.width()/2.0
            y=-50*math.sin((x-size.width()/2.0)*math.pi/50)+size.height()/2.0

            qp.drawPoint(x,y)


class DisplayWidget(QWidget):
    text_show=['777','888']

    def __init__(self, *args, **kwargs):
        super(DisplayWidget, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout(self, spacing=0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # self.left =Custom()
        # self.left.setHtml('今天天气真好')
        # self.right = QTextBrowser()
        # self.right.setText("tommadsadasdad")
        # splitter = QSplitter(Qt.Horizontal)
        # splitter.addWidget(self.left)
        # splitter.addWidget(self.right)
    def paintEvent(self,event):
        painter=QPainter()
        painter.begin(self)
        #自定义绘制方法
        # self.drawText(event,painter)
        self.myDrawText(event,painter,textLines=self.text_show)
        painter.end()

    def drawText(self,event,qp):
        # print(event.rect().x())
        f = QFont('SimSun',50)
        # f.
        qp.setFont(f)
        qp.setPen(QColor(0,0,0))
        qp.drawText(100,105,'今天风和日丽'*3)
        #设置画笔的颜色
        qp.setPen(QColor(83,180,105))
        #设置字体
        #绘制文字
        a = qp.drawText(101,106,'今天风和日丽'*2)
        print(a)
        # print(a.width)
        qp.setPen(QColor(177,177,177))
        qp.drawText(101,106,'今天风和日丽')

    def myDrawText(self,event,qp,textLines=["666"],font=QFont('霞鹜文楷 CN Regular',30),color=QColor(0,0,0)):
        qp.setFont(font)
        qp.setPen(color)
        font_size=30
        cnt=0
        for text in textLines:
            qp.drawText(100,105+cnt*font_size,text)
            cnt= cnt+1
    
    def setText(self,text):
        self.text_show= text.split('\n')

        self.update()


  

# 异步音频数据生成器，用于生成音频数据块作为NumPy数组。  
async def inputstream_generator(channels=1):  
    """  
    异步生成器，用于生成音频数据块作为NumPy数组。  
  
    参数:  
    channels (int): 声道数，默认为1。  
  
    返回:  
    异步生成音频数据块和状态信息的元组。  
    """  
    # 创建一个异步队列，用于在回调函数中存储音频数据和状态  
    q_in = asyncio.Queue()  
    # 获取当前的事件循环  
    loop = asyncio.get_event_loop()  
  
    # 定义回调函数，该函数在音频数据到达时被调用  
    def callback(indata, frame_count, time_info, status):  
        # 使用事件循环的线程安全方法将音频数据和状态放入队列  
        loop.call_soon_threadsafe(q_in.put_nowait, (indata.copy(), status))  
  
    # 查询可用的音频设备  
    devices = sd.query_devices()  
    # print(devices)  # 打印所有设备的详细信息  
    print(f"Micphone: {devices[sd.default.device[0]]}")
    print(f"Output: {devices[sd.default.device[1]]}")
    # 获取默认输入设备的索引  
    default_input_device_idx = sd.default.device[0]
    # 打印默认输入设备的名称  
    print(f'使用默认设备: {devices[default_input_device_idx]["name"]}')  
    print()  # 打印一个空行以分隔输出  
    print("已启动！请开始说话")  
  
    # 创建一个音频输入流  
    stream = sd.InputStream(  
        callback=callback,  # 使用上面定义的回调函数  !!!!!!!!!!!
        channels=channels,  # 声道数  
        dtype="float32",    # 数据类型  
        samplerate=16000,   # 采样率  
        blocksize=int(0.05 * 16000),  # 每个回调处理的块大小（0.05秒）;;;讯飞API官网:建议音频流每40ms发送1280字节
        device=default_input_device_idx)
  
    # 使用with语句确保流在离开上下文时正确关闭  
    with stream:  
        # 无限循环，等待并处理音频数据  
        while True:  
            # 从队列中异步获取音频数据和状态  
            indata, status = await q_in.get()  
            # 产出音频数据和状态  
            yield indata, status  


#异步接收来自WebSocket客户端的消息，直到接收到"Done!"为止。
async def receive_results(socket: websockets.WebSocketServerProtocol):  
    """  
    异步接收来自WebSocket客户端的消息，直到接收到"Done!"为止。  
  
    参数:  
    socket (websockets.WebSocketServerProtocol): WebSocket服务器协议对象，用于与客户端通信。  
  
    返回:  
    str: 最后一个非"Done!"的消息，如果没有消息则为""。  
    """  
    last_message = ""  # 初始化最后一条消息为空字符串  
  
    # 异步迭代WebSocket连接中的消息  
    async for message in socket:  
        # 如果消息不是"Done!"  
        if message != "Done!":  
            # 如果当前消息与上一次消息不同  
            if last_message != message:  
                # 更新最后一条消息  
                last_message = message  
  
                # 如果最后一条消息不为空，则打印它  
                if last_message:  
                    # 对结果的处理，这边可以调用函数了
                    # print(last_message)
                    await analyse_response_json(last_message)

  
        # 如果消息是"Done!"，则结束循环并返回最后一条消息  
        else:  
            return last_message  # [CHZT注] 这个返回给receive_task, 最后传到decoding_results作为最终结果

def insert_newlines(s, max_length):  
    """  
    在字符串s中插入换行符，以确保没有一行的长度超过max_length。  
    尽量在单词之间插入换行符，如果不可能，则在单词内适当位置插入。  
      
    参数:  
    s (str): 输入的字符串。  
    max_length (int): 单行允许的最大长度。  
      
    返回:  
    str: 修改后的字符串，其中包含了必要的换行符。  
    """  
    if max_length <= 0:  
        return s  # 如果最大长度无效，直接返回原字符串  
      
    result = []  
    current_line = ""  
      
    for char in s:  
        # 检查添加当前字符后是否超出最大长度  
        if len(current_line) + 1 > max_length:  
            # 如果超出，将当前行添加到结果中，并重置当前行为新字符  
            result.append(current_line)  
            current_line = char  
        else:  
            # 否则，将当前字符添加到当前行  
            current_line += char  
              
            # 检查是否在单词边界，如果是，则尝试添加换行符（如果需要）  
            if char.isspace() and len(current_line) >= max_length:  
                # 如果当前行已经是最大长度且末尾是空格，尝试向前查找单词边界  
                # 但为了简化，这里我们直接换行（假设我们不想在单词中间断开）  
                result.append(current_line[:-1])  # 移除末尾的空格  
                current_line = ""  # 重置当前行  
                  
        # 如果字符串结束，添加最后一行  
        if char == s[-1]:  
            result.append(current_line)  
      
    # 将结果列表转换回字符串，元素之间用换行符连接  
    return "\n".join(result)  

def insert_newlines1(s, max_length):  
    """  
    在字符串s中插入换行符，以确保没有一行的长度超过max_length。  
    不考虑单词边界，只根据长度来插入换行符。  
      
    参数:  
    s (str): 输入的字符串。  
    max_length (int): 单行允许的最大长度。  
      
    返回:  
    str: 修改后的字符串，其中包含了必要的换行符。  
    """  
    if max_length <= 0:  
        return s  # 如果最大长度无效，直接返回原字符串  
      
    result = []  
    current_line = ""  
      
    for char in s:  
        # 如果加上当前字符会导致当前行长度超过最大长度  
        if len(current_line) + 1 > max_length:  
            # 则在当前行末尾插入换行符，并重置当前行为新字符  
            result.append(current_line)  
            current_line = char  
        else:  
            # 否则，将当前字符添加到当前行  
            current_line += char  
      
    # 不要忘记添加最后一行  
    result.append(current_line)  
      
    # 将结果列表转换回字符串，元素之间用换行符连接  
    return "\n".join(result)  

# 生成文字
async def analyse_response_json(response_json : str):
    json_data = json.loads(response_json)
    # if json_data['is_final']==True:   # 当结束标志为真时获得该句话
    if True:
        if json_data['text']!='':
            # cor_text=m.correct(json_data['text'])
            # print(cor_text['target'])
            if json_data['is_final']==True:
                print(json_data['text'])
            txtrn=insert_newlines1(json_data['text'],30)
            mainDisplayweight.setText(txtrn)

async def run(  
    server_addr: str,  # WebSocket服务器的地址  
    server_port: int,  # WebSocket服务器的端口号  
):  
    # 使用WebSocket连接到指定的服务器地址和端口  
    async with websockets.connect(  
        f"ws://{server_addr}:{server_port}"  
    ) as websocket:  # noqa: 忽略flake8等工具的特定警告  
        # 创建一个异步任务来接收WebSocket上的结果  
        receive_task = asyncio.create_task(receive_results(websocket))  
        #                                               ^ 这个函数异步进行,负责接受结果

        print("程序开始运行啦!请开始说话:")  # 提示用户开始说话  
  
        # 异步迭代音频输入流生成器  
        async for indata, status in inputstream_generator():  # 假设这是您之前定义的异步生成器, 用于生成音频数据块作为NumPy数组。
            # 异步生成音频数据块 indata 和状态信息 status
            if status:  
                print(status)  # 打印任何非零状态信息  
            
            # 将接收到的音频数据重新塑形为一维数组  
            indata = indata.reshape(-1)  
            # 确保数组是连续的，这对于后续的内存操作可能是必要的
            # [CHZT注] 据说只是改变数组元素在内存中的位置,不会影响数组内容,,,不过也许会影响 .tobytes() ?
            indata = np.ascontiguousarray(indata)  
            # 将音频数据转换为字节串，并通过WebSocket发送  
            await websocket.send(indata.tobytes())  
  
        # 等待接收任务完成，并获取最终的解码结果  
        decoding_results = await receive_task  
        # 打印最终的解码结果  
        print(f"\最终的结果:\n{decoding_results}")


async def main():

    server_addr = "127.0.0.1"
    server_port = 6006

    # server_addr=input("请输入服务器地址(默认127.0.0.1)： ")
    if server_addr=='':
        server_addr = "127.0.0.1"

    # 在此调用了异步的run函数
    await run(
        server_addr=server_addr,
        server_port=server_port,
    )

# m = pycorrector.Corrector()

class Worker(QThread):  
    finished = pyqtSignal()  
  
    def run(self):  
        # 模拟耗时的操作  
        # 在此运行了异步的main
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n按下 Ctrl + C 来退出")
        self.finished.emit()  

if __name__ == "__main__":
    global m
    # m = pycorrector.Corrector()
    # print(m.correct_batch(['少先队员因该为老人让坐', '你找到你最喜欢的工作，我也很高心。']))
    global mainWnd
    
    QssFilePath='./Voice_assistant/main.qss'
    app = QApplication(sys.argv)
    # 检测文件编码
    with open(QssFilePath, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
    with open(QssFilePath,'r',encoding=encoding) as f:
        qss = f.read()
    
    global mainDisplayweight
    

    app.setStyleSheet(qss)
    mainWnd = DesktopWidget()
    mainWnd.setWindowTitle('测试标题栏')
    mainWnd.setWindowIcon(QIcon('Qt.ico'))
    mainWnd.resize(QSize(1250,780))
    mainDisplayweight=DisplayWidget(mainWnd)
    mainWnd.setWidget(mainDisplayweight)  # 把自己的窗口添加进来
    mainWnd.show()
    
    sys.exit(app.exec_())


