# main.py
import sys
import os
import threading
from pathlib import Path
from PyQt6 import QtWidgets, QtCore, QtGui
from Ui_MainWindow import Ui_VideoDownload

# --- 路徑引導程式碼依然是好習慣，保留它 ---
def resource_path(relative_path):
    """ 獲取資源的絕對路徑，對開發環境和打包都有效 """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

from downloader import get_available_formats, download_video

# --- 核心修改 2：讓 MainWindow 繼承我們生成的 Ui_MainWindow ---
class MainWindow(QtWidgets.QMainWindow, Ui_VideoDownload):
    # ... signal definitions ...
    formatsLoaded = QtCore.pyqtSignal(list)
    progressUpdated = QtCore.pyqtSignal(int)
    downloadFinished = QtCore.pyqtSignal(str)
    downloadFailed = QtCore.pyqtSignal(str)
    statusUpdated = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        
        self.setupUi(self)
        
        # --- 等比例縮放 ---
        self._scalable_widgets = [
            {'widget': self.videoLabel,   'font_size': 18, 'base_geom': self.videoLabel.geometry()},
            {'widget': self.urlEdit,      'font_size': 14, 'base_geom': self.urlEdit.geometry()},
            {'widget': self.qualityLabel, 'font_size': 18, 'base_geom': self.qualityLabel.geometry()},
            {'widget': self.qualityCombo, 'font_size': 14, 'base_geom': self.qualityCombo.geometry()},
            {'widget': self.downloadButton,'font_size': 14, 'base_geom': self.downloadButton.geometry()},
            {'widget': self.progressBar,  'font_size': self.progressBar.font().pointSize(),  'base_geom': self.progressBar.geometry()},
        ]

        # 紀錄視窗的基準尺寸
        self._base_width = self.width()
        self._base_height = self.height()
        
        self.setWindowIcon(QtGui.QIcon("icon/ghibli_downloader.ico"))
        self.setWindowTitle("Video Downloader by Zack")
        # 套用風格
        self.apply_ghibli_style()
        
        self.current_valid_url = None # 用來儲存分析成功的網址
        # 存放從 downloader 取得的格式資訊
        self.available_formats = []

        # 連接訊號到對應的槽函式
        self.connect_signals()
        
        # 綁定 UI 元件的事件
        self.urlEdit.textChanged.connect(self.on_url_changed)
        self.downloadButton.clicked.connect(self.on_start_download_button_clicked)
        
        # 初始化 UI 狀態
        self.reset_ui_to_initial_state()

    def resizeEvent(self, event: QtGui.QResizeEvent):
        """
        每當視窗大小改變時，此函式會被自動呼叫。
        """
        super().resizeEvent(event)

        if self._base_width == 0 or self._base_height == 0:
            return

        # 1. 計算寬度和高度的縮放比例
        width_scale = self.width() / self._base_width
        height_scale = self.height() / self._base_height

        # 2. 更新所有可縮放元件的字體和幾何尺寸
        self._update_widget_geometry(width_scale, height_scale)

    def _update_widget_geometry(self, width_scale, height_scale):
        """
        根據縮放係數，更新所有已紀錄元件的字體大小和幾何尺寸。
        """
        for item in self._scalable_widgets:
            widget = item['widget']
            base_font_size = item['font_size']
            base_geom = item['base_geom'] # QRect(x, y, width, height)

            if not widget:
                continue

            # 1. 計算新的幾何尺寸和位置
            new_x = int(base_geom.x() * width_scale)
            new_y = int(base_geom.y() * height_scale)
            new_width = int(base_geom.width() * width_scale)
            new_height = int(base_geom.height() * height_scale)

            # 2. 直接設定新的幾何尺寸
            widget.setGeometry(new_x, new_y, new_width, new_height)

            # 3. 更新字體大小，使用更穩定的最小維度縮放
            font_scale_factor = min(width_scale, height_scale)
            if base_font_size > 0:
                new_font = widget.font()
                new_size = max(8, int(base_font_size * font_scale_factor))
                new_font.setPointSize(new_size)
                widget.setFont(new_font)
                
    def connect_signals(self):
        """將所有訊號連接到槽函式。"""
        self.formatsLoaded.connect(self.update_format_options)
        self.progressUpdated.connect(self.update_progress_bar)
        self.downloadFinished.connect(self.show_download_complete)
        self.downloadFailed.connect(self.show_download_error)
        self.statusUpdated.connect(self.update_status_label)

    def reset_ui_to_initial_state(self):
        """重置 UI 到初始狀態，並清除已儲存的網址。"""
        self.current_valid_url = None # 清除已驗證的網址
        self.qualityCombo.clear()
        self.qualityCombo.addItem("請先貼上影片網址")
        self.qualityCombo.setEnabled(False)
        self.downloadButton.setEnabled(False)
        self.progressBar.setValue(0)
        self.statusUpdated.emit("準備就緒。請貼上 YouTube 影片網址。")

    def on_url_changed(self, text):
        """當 URL 輸入框內容改變時觸發。"""
        url = text.strip()
        # 如果輸入框被清空，則重置UI
        if not url:
            self.reset_ui_to_initial_state()
            return

        # --- 修改此處邏輯 ---
        # 準備開始分析，先清除舊的有效網址
        self.current_valid_url = None
        self.downloadButton.setEnabled(False)
        self.qualityCombo.clear()
        self.qualityCombo.addItem("正在分析網址，請稍候…")
        self.qualityCombo.setEnabled(False)
        self.statusUpdated.emit(f"分析中: {url}")
        
        threading.Thread(target=self.load_formats_thread, args=(url,), daemon=True).start()

    def load_formats_thread(self, url):
        """在背景執行緒中獲取影片格式。"""
        try:
            formats = get_available_formats(url)
            # --- 新增此行：分析成功，儲存這個有效的網址 ---
            self.current_valid_url = url
            self.formatsLoaded.emit(formats)
        except Exception as e:
            # --- 新增此行：分析失敗，清除網址 ---
            self.current_valid_url = None 
            self.statusUpdated.emit(f"分析失敗，請檢查網址。")
            self.formatsLoaded.emit([])

    @QtCore.pyqtSlot(list)
    def update_format_options(self, formats):
        """當格式載入完成後，更新下拉選單。"""
        self.qualityCombo.clear()
        self.available_formats = formats
        
        if not self.available_formats:
            self.qualityCombo.addItem("無法獲取影片格式")
            self.qualityCombo.setEnabled(False)
            self.downloadButton.setEnabled(False)
            self.statusUpdated.emit("分析失敗，請檢查網址或網路。")
            return

        # 確保迭代時，將單一的格式字典 (fmt) 存入 userData
        for fmt in self.available_formats:
            self.qualityCombo.addItem(fmt['display_text'], userData=fmt)
        
        self.qualityCombo.setEnabled(True)
        self.downloadButton.setEnabled(True)
        self.statusUpdated.emit("分析完成，請選擇要下載的畫質。")

    def on_start_download_button_clicked(self):
        """當下載按鈕被點擊時觸發。"""
        url_to_download = self.current_valid_url
        selected_index = self.qualityCombo.currentIndex()
        
        if not url_to_download or selected_index < 0:
            QtWidgets.QMessageBox.warning(self, "資訊不足", "請確保已成功分析網址並已選擇畫質。")
            return

        # --- 核心修改：增加防禦性檢查 ---
        selected_format_data = self.qualityCombo.currentData()
        
        # 1. 檢查資料類型是否為字典 (dict)
        if not isinstance(selected_format_data, dict):
            QtWidgets.QMessageBox.critical(self, "內部程式錯誤", 
                f"選擇的格式資料類型不正確。\n預期類型: dict\n收到的類型: {type(selected_format_data).__name__}")
            return

        # 2. 確認是字典後，才安全地使用 .get() 方法
        video_title = selected_format_data.get('title', 'video')
        safe_filename = "".join([c for c in video_title if c.isalnum() or c in (' ', '_', '-')]).rstrip()
        
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "儲存影片", f"{safe_filename}.mp4", "MP4 影片檔案 (*.mp4)")

        if not save_path:
            self.statusUpdated.emit("使用者取消下載。")
            return
            
        self.downloadButton.setEnabled(False)
        self.qualityCombo.setEnabled(False)
        self.progressBar.setValue(0)

        threading.Thread(
            target=download_video,
            # 將已驗證為字典的 selected_format_data 傳遞下去
            args=(url_to_download, selected_format_data, save_path, self.progressUpdated, self.downloadFinished, self.downloadFailed, self.statusUpdated),
            daemon=True
        ).start()

    @QtCore.pyqtSlot(int)
    def update_progress_bar(self, percentage):
        """更新進度條。"""
        self.progressBar.setValue(percentage)

    @QtCore.pyqtSlot(str)
    def update_status_label(self, message):
        """更新狀態列文字。"""
        # 假設您的 .ui 檔案中有一個 QLabel 叫做 statusLabel
        if hasattr(self, 'statusLabel'):
            self.statusLabel.setText(message)

    @QtCore.pyqtSlot(str)
    def show_download_complete(self, final_filepath):
        """顯示下載完成訊息。"""
        self.progressBar.setValue(100)
        self.downloadButton.setEnabled(True)
        self.qualityCombo.setEnabled(True)
        self.statusUpdated.emit("下載完成！")
        QtWidgets.QMessageBox.information(self, "下載成功", f"影片已成功儲存至：\n{final_filepath}")
        self.progressBar.setValue(0)

    @QtCore.pyqtSlot(str)
    def show_download_error(self, error_message):
        """顯示下載失敗訊息。"""
        self.progressBar.setValue(0)
        self.downloadButton.setEnabled(True)
        self.qualityCombo.setEnabled(True)
        self.statusUpdated.emit("下載失敗。")
        QtWidgets.QMessageBox.critical(self, "下載錯誤", f"發生錯誤：\n{error_message}")
    def apply_ghibli_style(self):
        """套用吉卜力風格樣式"""
        ghibli_style = """
        /* 主視窗背景 - 溫暖米色 */
        QMainWindow {
            background-color: #F4F1E8;
            color: #5D4037;
            font-family: "Microsoft YaHei", "Arial", sans-serif;
        }
        
        /* 輸入框樣式 - 柔和圓角 */
        QLineEdit {
            background-color: #FFFFFF;
            border: 2px solid #D7CCC8;
            border-radius: 12px;
            padding: 8px 12px;
            font-size: 11px;
            color: #5D4037;
        }
        
        QLineEdit:focus {
            border-color: #8BC34A;
            background-color: #F8FFF8;
        }
        
        /* 下拉選單樣式 */
        QComboBox {
            background-color: #FFFFFF;
            border: 2px solid #D7CCC8;
            border-radius: 12px;
            padding: 6px 12px;
            font-size: 11px;
            color: #5D4037;
            min-width: 80px;
        }
        
        QComboBox:hover {
            border-color: #BCAAA4;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 6px solid transparent;
            border-right: 6px solid transparent;
            border-top: 6px solid #8D6E63;
        }
        
        /* 按鈕樣式 - 自然綠色調 */
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #A5D6A7, stop:1 #81C784);
            border: none;
            border-radius: 15px;
            padding: 10px 20px;
            font-size: 12px;
            font-weight: bold;
            color: #2E7D32;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #C8E6C9, stop:1 #A5D6A7);
        }
        
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #81C784, stop:1 #66BB6A);
        }
        
        QPushButton:disabled {
            background-color: #E0E0E0;
            color: #9E9E9E;
        }
        
        /* 進度條樣式 - 溫暖橙色 */
        QProgressBar {
            border: 2px solid #D7CCC8;
            border-radius: 8px;
            background-color: #FFF8E1;
            text-align: center;
            font-size: 11px;
            color: #5D4037;
            height: 20px;
        }
        
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #FFB74D, stop:1 #FF9800);
            border-radius: 6px;
        }
        
        /* 文字編輯框樣式（標題用） */
        QTextEdit {
            background-color: #FFF8E1;
            border: 1px solid #E8D5B7;
            border-radius: 8px;
            padding: 8px;
            color: #5D4037;
            font-weight: bold;
        }
        
        QTextEdit[readOnly="true"] {
            background-color: #F5F5DC;
            color: #8D6E63;
        }
        
        /* 狀態列樣式 */
        QStatusBar {
            background-color: #E8D5B7;
            color: #5D4037;
            border-top: 1px solid #D7CCC8;
        }
        """
        self.setStyleSheet(ghibli_style)

# ---- 程式啟動入口 ----
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    # 設定應用程式ID，以便在 Windows 工作列顯示正確圖示
    try:
        from ctypes import windll
        myappid = 'zack.ghibli.videodownloader.1.1'
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except ImportError:
        pass
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())