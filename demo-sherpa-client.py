import argparse
import asyncio
import sys
import json
import pycorrector
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget  
from PyQt5.QtCore import QThread, pyqtSignal  

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
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget  
from PyQt5.QtCore import Qt  
from PyQt5.QtWidgets import QApplication, QWidget  
from PyQt5.QtCore import Qt, QRect  
from PyQt5.QtGui import QScreen  
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QColor, QPalette  
  
class TransparentWindow(QMainWindow):  
    def __init__(self):  
        super().__init__()  
        self.setWindowTitle('半透明窗口带文本显示')  
        self.setGeometry(100, 100, 1900, 400)  
          

        # 设置窗口置顶  
        self.setWindowFlags(Qt.WindowStaysOnTopHint)  
  
        # 获取屏幕尺寸  
        screen = QScreen.grabWindow(QApplication.primaryScreen(), QApplication.desktop().winId())  
        screen_size = screen.size()  

        # 调整窗口位置到屏幕正中最下方  
        # 注意：这里我们假设窗口的高度是固定的（如100px），然后计算顶部位置  
        # 顶部位置 = 屏幕高度 - 窗口高度  
        screen_height = screen_size.height()  
        window_height = self.height()  
        self.move(screen_size.width() // 2 - self.width() // 2, screen_height - window_height)  

        # 移除边框  
        self.setWindowFlags(Qt.FramelessWindowHint)  
        # 设置窗口背景半透明（注意：在某些平台上可能不完全有效）  
        self.setAttribute(Qt.WA_TranslucentBackground)  
          
        # 创建一个中心小部件用于布局  
        central_widget = QWidget(self)  
        self.setCentralWidget(central_widget)  
          
        # 创建一个垂直布局  
        layout = QVBoxLayout(central_widget)  
          
        # 创建一个文本标签控件  
        self.text_label = QLabel(central_widget)  
        self.text_label.setText("这里是初始文本内容。")  
        # 创建一个QFont对象并设置其属性  
        font = QFont()  
        font.setFamily("霞鹜文楷 CN Bold")  # 设置字体家族  
        font.setPointSize(30)    # 设置字体大小
        
        # 将配置好的QFont对象应用到QLabel上  
        self.text_label.setFont(font)  

        # 创建一个调色板  
        palette = self.text_label.palette()  

        # 设置文本颜色（WindowText是文本颜色的角色）  
        palette.setColor(QPalette.WindowText, QColor(250, 249, 222))  

        # 将调色板应用到标签上  
        self.text_label.setPalette(palette)  
        self.text_label.setAlignment(Qt.AlignCenter)  
          
        # 将文本标签控件添加到布局中  
        layout.addWidget(self.text_label)  
          
        self.worker = Worker()  
        self.worker.finished.connect(self.onTaskFinished) 

        self.startTask()
  
    def startTask(self):  
        self.worker.start()  
  
    def onTaskFinished(self):  
        print("任务完成！")  
  

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
            window.text_label.setText(txtrn)

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
    global window
    app = QApplication(sys.argv)  
    window = TransparentWindow()  
    window.show()

    # 在此运行了异步的main
    # try:
    #     asyncio.run(main())
    # except KeyboardInterrupt:
    #     print("\n按下 Ctrl + C 来退出")

    sys.exit(app.exec_())



