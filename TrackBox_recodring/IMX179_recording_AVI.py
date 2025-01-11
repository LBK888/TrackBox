'''
IMX179 recording program - 2025.01.11 - version 1.0
 for TrackBox v2.0, https://github.com/LBK888/TrackBox
camera: IMX179 DFRobot FIT0729 (8 Megapixels USB Camera)

Max Effective Resolution: 3264(H) X 2448(V)  8 Megapixel
Image Output Format: JPEG 
Supported Resolution and Frame Rate: 
                 3264X2448 @ 15fps  / 2592X1944@ 15fps
                 1920x1080 @ 30fps  / 1600X1200@ 30fps
                 1280X720 @ 30fps  / 960X540@ 30fps
                 800X600 @ 30fps   / 640X480@ 30fps

To-Do:
    1. button control from MCU
    2. config file
'''
import cv2
import time
import os
import serial   #this is pyserial, not serial
from serial.tools import list_ports
from datetime import datetime
from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
import matplotlib.pyplot as plt
import csv
import threading
from queue import Queue
       

### USER Settings ###
# 設定時間間隔（10 分鐘）
RecDuration_min = 10
# 設定錄影解析度
width, height = 2592, 1944
# 設定曝光值 (可選)
auto_exposure=False  #是否自動曝光，若亮度不足導致曝光值>-4，可能會使fps不足
exposure_value = -7  # 曝光值通常在 -7 到 7 之間
# 相機號碼，預設=0，如像是筆電已有內建相機，請自行修改
camera_id=0
# 重要: 第一次錄影完，查看real FPS是多少，再來修改這裡
# 說明: 真實fps除了與硬體有關外，也與python+cv2版本有關，最佳組合可以達到2592*1944@19fps
fps=20.0
# 設定相機啟動後所需的自動對焦/曝光時間 (秒)
cam_pause=2.5

#folder
out_filename='video_' #prefix, 會檢查檔案不被複寫
#root path, 與本py檔同一資料夾，請放置於SSD硬碟
rootdir=os.path.dirname(os.path.realpath(__file__))+'/'
#folder
folder=rootdir
#folder='D:/Webcam_recodring/'  #請使用SSD硬碟

### Not Settings ###
RecDuration = RecDuration_min * 60

class VideoRecorder:
    def __init__(self):
        # 新增序列埠設定
        self.SERIAL_PORT = find_serial_port()
        self.BAUD_RATE = 115200
        self.ser = None
        self.temp_humid_data = []
        self.TH_read_intv=5 #溫溼度讀取間格，sec
        self.last_temp_read_time = 0  # 新增：追蹤上次讀取時間

        self.fn_code="1"

        # recording optimization
        self.frame_queue = Queue(maxsize=128)  # 新增 frame 佇列
        self.is_recording = True
        #self.buffer_size = 10  # 設定緩衝區大小        
        
        self.cleanup_handlers = []
        
    def setup_serial(self):
        """設置序列埠連接"""
        try:
            self.ser = serial.Serial(self.SERIAL_PORT, self.BAUD_RATE, timeout=1)
            time.sleep(2)  # 等待設備初始化
            self.ser.write(b"START\n")
            print("序列埠連接成功")
            return True
        except Exception as e:
            print(f"序列埠連接失敗: {e}")
            return False

    def read_temp_humid(self):
        """讀取溫溼度數據，每TH_read_intv秒執行一次"""
        current_time_TH = time.time()
        # 如果距離上次讀取還不到TH_read_intv秒，則跳過
        if current_time_TH - self.last_temp_read_time < self.TH_read_intv:
            return None, None
                
        if self.ser:
            try:
                # 清空緩衝區
                self.ser.reset_input_buffer()
                
                # 嘗試不同的編碼方式
                try:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                except UnicodeDecodeError:
                    try:
                        line = self.ser.readline().decode('big5', errors='ignore').strip()
                    except UnicodeDecodeError:
                        line = self.ser.readline().decode('ascii', errors='ignore').strip()
                
                # 確保數據格式正確
                #print(line)
                if ":" in line and "," in line:
                    parts = line.split(", ")
                    if len(parts) >= 2:
                        # 使用更安全的方式提取數值
                        temp_str = parts[0].split(": ")[-1].split(" ")[0]
                        humid_str = parts[1].split(": ")[-1].split(" ")[0]
                        
                        # 確保能轉換為浮點數
                        if temp_str and humid_str:
                            temperature = float(temp_str)
                            humidity = float(humid_str)
                            
                            current_time_str = datetime.now().strftime("%H:%M:%S")
                            self.temp_humid_data.append([current_time_str, temperature, humidity])
                            self.last_temp_read_time = current_time_TH
                            return temperature, humidity
                            
            except Exception as e:
                print(f"讀取溫溼度數據錯誤: {e}")
                print(f"原始數據: {self.ser.readline()}")  # 用於調試
        return None, None


    def capture_frames(self, cap):
        """專門負責擷取影像的執行緒"""
        while self.is_recording:
            ret, frame = cap.read()
            if not ret:
                break
            if not self.frame_queue.full():
                self.frame_queue.put(frame)


    
    def record(self):
        try:
            # 選擇 webcam
            cap = cv2.VideoCapture(camera_id)
            #cap.set(cv2.CAP_PROP_FPS, 10)
            actual_width, actual_height = set_resolution(cap, width, height)

            if auto_exposure:
                set_exposure(cap, set_auto_exposure(cap))
            else:
                set_exposure(cap, exposure_value)
                time.sleep(cam_pause)   #等待自動對焦與自動曝光
            
            # 啟動擷取影像的執行緒
            capture_thread = threading.Thread(target=self.capture_frames, args=(cap,))
            capture_thread.start()
            

            # start rec time, 定時器開始        
            startT = time.time()
            frame_wrote = 0
            
            # 設置序列埠
            self.setup_serial()

            # Set Window size to 50％
            window_width = int(width * 0.5)
            window_height = int(height * 0.5)
            cv2.namedWindow('Webcam Recording', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Webcam Recording', window_width, window_height)

            self.fn_code=datetime.now().strftime('%Y%m%d_%H%M')
            filename = get_next_filename(folder+out_filename+self.fn_code+".avi")
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(filename, fourcc, fps, (int(actual_width), int(actual_height)))

            while self.is_recording:
                #frame = None
                if not self.frame_queue.empty():    #opt..
                    frame = self.frame_queue.get()  #opt..
                    out.write(frame)
                    frame_wrote += 1
                    
                    if frame_wrote % 2 == 0:
                        cv2.imshow('Webcam Recording', frame)


                # 當前時間
                current_time = time.time() - startT

                # 如果是在攝影時間內則錄影
                if current_time >= RecDuration:
                    self.is_recording = False
                    break  # 達到指定錄製時間才結束


                #time.sleep(interval*0.1)

                # 按下 'q' 鍵結束錄影
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                # 讀取溫溼度
                temp, humid = self.read_temp_humid()
                if temp is not None and humid is not None:
                    print(f"溫度: {temp}°C, 濕度: {humid}%")

            # 釋放資源
            self.is_recording = False
            capture_thread.join()
            cap.release()
            out.release()
            cv2.destroyAllWindows()

            print(f'Vedio record and saved as {filename}')
            print(f'=> Total frame: {frame_wrote}')
            print(f'=> Total Duration: {current_time:.2f} sec')
            print(f'=> real FPS: {frame_wrote/current_time:.2f} fps')
        except Exception as e:
            print(f"錄影過程發生錯誤：{e}")
        finally:
            self.cleanup()

    def stop(self):
        # 儲存溫溼度數據
        if self.temp_humid_data:
            fn=f"temp_humid_{self.fn_code}"
            self.save_temp_humid_data(filename=fn+".xlsx")
            self.save_plot_data(filename=fn+".png")
        
        # 關閉序列埠
        if self.ser:
            self.ser.write(b"STOP\n")
            self.ser.close()


    def save_temp_humid_csv(self):
        """儲存溫溼度數據到 CSV 檔案"""
        filename = folder + f"temp_humid_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Time', 'Temperature (°C)', 'Humidity (%)'])
            writer.writerows(self.temp_humid_data)
        print(f"溫溼度數據已儲存至 {filename}")

    def save_temp_humid_data(self, filename="temp_humid.xlsx"):
        """將數據保存到 Excel 並繪製圖表"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Temperature & Humidity"

        # 標題
        ws.append(["Time", "Temperature (°C)", "Humidity (%)"])

        # 插入數據
        for record in self.temp_humid_data:
            ws.append(record)

        # 繪製圖表
        chart = LineChart()
        chart.title = "Temperature & Humidity Over Time"
        chart.style = 12
        
        # 修改 y 軸設定
        chart.y_axis.title = "Value"
        #chart.y_axis.majorGridlines = True  # 修改：啟用網格線
        chart.y_axis.delete = False  # 修改：確保顯示 y 軸
        
        # 修改 x 軸設定
        chart.x_axis.title = "Time"
        chart.x_axis.tickLblPos = "low"
        chart.x_axis.tickLblSkip = 2
        #chart.x_axis.majorGridlines = True  # 修改：啟用網格線
        chart.x_axis.delete = False  # 修改：確保顯示 x 軸

        # 參考範圍（時間不包括在內）
        data_length = len(self.temp_humid_data)
        data_range = Reference(ws, min_col=2, max_col=3, min_row=1, max_row=data_length + 1)
        chart.add_data(data_range, titles_from_data=True)

        # 時間軸
        time_range = Reference(ws, min_col=1, min_row=2, max_row=data_length + 1)
        chart.set_categories(time_range)
        
        # 設定線條顏色
        s1 = chart.series[0]  # 溫度線
        s2 = chart.series[1]  # 濕度線
        s1.graphicalProperties.line.solidFill = "8B0000"  # 深紅色
        s2.graphicalProperties.line.solidFill = "87CEEB"  # 水藍色

        ws.add_chart(chart, "E5")
        wb.save(folder+filename)
        print(f"數據已保存為: {filename}")


    def save_plot_data(self, filename="temp_humid.png"):
        """用 matplotlib 繪製圖表"""
        if not self.temp_humid_data:  # 檢查是否有數據
            print("沒有可用的溫溼度數據")
            return
            
        times = [record[0] for record in self.temp_humid_data]
        temperatures = [record[1] for record in self.temp_humid_data]
        humidities = [record[2] for record in self.temp_humid_data]

        plt.figure(figsize=(12, 6))  # 修改：增加圖表大小
        plt.plot(times, temperatures, color='darkred', marker='o', label="Temperature (°C)", linewidth=2, markersize=6)
        plt.plot(times, humidities, color='skyblue', marker='o', label="Humidity (%)", linewidth=2, markersize=6)
        
        plt.xlabel("Time", fontsize=12)
        plt.ylabel("Value", fontsize=12)
        plt.title("Temperature & Humidity Over Time", fontsize=14)
        plt.legend(fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # 修改：調整x軸標籤
        plt.xticks(rotation=45, ha='right')
        
        # 修改：調整圖表邊距
        plt.tight_layout(pad=2.0)
        
        # 保存圖表
        plt.savefig(folder+filename, dpi=480, bbox_inches='tight')
        plt.close()  # 修改：關閉圖表，避免顯示
        print(f"圖表已保存為: {filename}")

    def cleanup(self):
        # 清理所有資源
        self.frame_queue.queue.clear()
        self.temp_humid_data = []
        self.is_recording = False
        
        self.ser.write(b"STOP\n")
        self.ser.close()

def set_resolution(cap, width, height):
    # 確保設定有被正確套用
    ret1 = cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    ret2 = cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    # 檢查實際設定的解析度
    actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    
    print(f"目標解析度: {width}x{height}")
    print(f"實際解析度: {actual_width}x{actual_height}")
    
    if actual_width != width or actual_height != height:
        print("警告：無法設定到指定的解析度！")
    
    return actual_width, actual_height



def set_exposure(cap, exposure_value):
    cap.set(cv2.CAP_PROP_EXPOSURE, exposure_value)

def set_auto_exposure(cap,center_ratio=0.7):
    """自動調整曝光值直到找到最佳設定"""
    # 初始設定
    exposure = 0
    cap.set(cv2.CAP_PROP_EXPOSURE, exposure)
    time.sleep(0.5)  # 等待曝光調整生效
    
    # 讀取一張影像
    ret, frame = cap.read()
    if not ret:
        print("無法讀取影像")
        return -7  # 返回預設值
    
    # 計算中央70%區域
    h, w = frame.shape[:2]
    center_h = int(h * center_ratio)
    center_w = int(w * center_ratio)
    start_h = (h - center_h) // 2
    start_w = (w - center_w) // 2
    
    # 取得中央區域
    center_region = frame[start_h:start_h+center_h, start_w:start_w+center_w]
    
    # 轉換為灰階以計算亮度直方圖
    gray = cv2.cvtColor(center_region, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    
    # 計算平均亮度和過曝/欠曝的像素比例
    total_pixels = center_h * center_w
    dark_pixels = sum(hist[:64]) / total_pixels  # 暗部像素比例
    bright_pixels = sum(hist[192:]) / total_pixels  # 亮部像素比例
    mean_brightness = cv2.mean(gray)[0]
    
    # 調整曝光值的最大嘗試次數
    max_attempts = 10
    attempt = 0
    
    while attempt < max_attempts:
        print(f"目前曝光值: {exposure}, 平均亮度: {mean_brightness:.1f}")
        
        # 判斷是否需要調整
        if bright_pixels > 0.2:  # 過曝
            exposure = max(exposure - 1, -10)
        elif dark_pixels > 0.3:  # 欠曝
            exposure = min(exposure + 1, 10)
        else:
            # 如果平均亮度在理想範圍內(90-150)就停止調整
            if 90 <= mean_brightness <= 150:
                break
            elif mean_brightness < 90:
                exposure = min(exposure + 1, 10)
            else:
                exposure = max(exposure - 1, -10)
        
        # 設定新的曝光值
        cap.set(cv2.CAP_PROP_EXPOSURE, exposure)
        time.sleep(0.5)  # 等待曝光調整生效
        
        # 重新讀取影像並計算
        ret, frame = cap.read()
        if not ret:
            break
            
        center_region = frame[start_h:start_h+center_h, start_w:start_w+center_w]
        gray = cv2.cvtColor(center_region, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        dark_pixels = sum(hist[:64]) / total_pixels
        bright_pixels = sum(hist[192:]) / total_pixels
        mean_brightness = cv2.mean(gray)[0]
        
        attempt += 1
    
    print(f"最終曝光值設定為: {exposure}")
    return exposure


def get_next_filename(filename):
    name, ext = os.path.splitext(filename)
    count = 1
    while os.path.exists(filename):
        filename = f"{name}_{count}{ext}"
        count += 1
    return filename

def find_serial_port():
    """
    自動尋找可用的序列埠，如有需要加入以下code改為手動設定
    # d1 mini 的USB序列埠，請每次檢查。如不記錄溫濕度則忽略
    SERIAL_PORT  = "COM4"
    """
    ports = list(list_ports.comports())
    if not ports:
        raise Exception("未找到任何可用的序列埠，請檢查設備連接！")

    for port in ports:
        print(f"找到序列埠: {port.device} - {port.description}")
        # 根據需要，匹配特定的設備名稱或描述
        if "USB-SERIAL" in port.description or "CH340" in port.description:
            print(f"自動選擇序列埠: {port.device}")
            return port.device

    # 如果無法自動匹配，使用第一個序列埠
    print("未找到特定設備，使用第一個可用序列埠")
    return ports[0].device

def main():
    recorder = VideoRecorder()
    recorder.record()
    recorder.stop()

if __name__ == "__main__":
    main()
