# VideoDownload
一個基於 [Python] 的工具，用於從多個公開影片平台下載影片串流。

A tool based on [Python] for downloading video streams from various public video platforms.
-----------------------------------------------------------------------------------------------------------------------------

✨ 功能特性 / Features
支援多平台下載
可自訂選擇影片解析度與格式

⚠️ 免責聲明 / Disclaimer
本工具僅供教育、研究與個人使用。

使用者在使用本工具時，應自行承擔全部責任，確保其行為符合所有適用的法律法規，以及任何影音平台的服務條款。下載、使用、或分發受版權保護的內容，而未獲得版權持有人的明確授權，可能屬於違法行為。

本專案的開發者對於任何使用者因使用或濫用本軟體而導致的任何形式的法律後果、損害或損失，概不負責。開發者不提供任何明示或暗示的擔保，並且不支持任何形式的侵權行為。

本專案是一個開源專案，其目的在於技術交流與學習。所有程式碼均按「原樣」提供。使用者在下載和使用本專案時，即表示已閱讀、理解並同意本免責聲明的所有條款。

-----------------------------------------------------------------------------------------------------------------------------

This tool is intended for educational, research, and personal use only.

Users are solely responsible for ensuring that their use of this tool complies with all applicable laws and the terms of service of any platform they use it with. Downloading, using, or distributing copyrighted content without the explicit permission of the copyright holder may be illegal.

The developers of this project assume no liability for any legal consequences, damages, or losses arising from the use or misuse of this software. The developers provide no warranties, express or implied, and do not endorse any form of copyright infringement.

This is an open-source project for the purpose of technical exchange and learning. All code is provided "as is". By downloading or using this project, you acknowledge that you have read, understood, and agreed to all terms in this disclaimer.

-----------------------------------------------------------------------------------------------------------------------------

🚀 安裝說明 / Installation
前置需求:

請確保您已安裝 [Python 3.9]。

(若有) 請確保您已安裝 ffmpeg 並將其加入系統路徑。

### 打包為 Windows 執行檔 (.exe)

如果你想從原始碼自行建置執行檔，你需要安裝 Python 和 `pyinstaller`。此專案也依賴 `yt-dlp` 和 `ffmpeg`。

1.  **安裝必要套件：**
    ```bash
    pip install pyinstaller pyqt6 yt-dlp
    ```

2.  **放置 `ffmpeg.exe`：**
    請至 `ffmpeg` 官網下載，並將 `ffmpeg.exe` 檔案放在專案的根目錄下（與 `main.py` 同一層）。

3.  **產生 `.spec` 規格檔案：**
    這個檔案會告訴 PyInstaller 如何打包你的應用程式。在終端機中執行以下指令：
    ```bash
    pyi-makespec --windowed --onefile main.py
    pyinstaller main.spec
    ```
    * `--windowed`：產生沒有命令提示字元 (黑視窗) 的圖形介面程式。
    * `--onefile`：將所有東西打包成一個單獨的 `.exe` 檔案。


Prerequisites:

Make sure you have [Python 3.9] installed.

(If applicable) Ensure ffmpeg is installed and added to your system's PATH.

### Packaging for Windows (.exe)

If you want to build the executable file from the source code, you will need to have Python and `pyinstaller` installed. This project also relies on `yt-dlp` and `ffmpeg`.

1.  **Install necessary libraries:**
    ```bash
    pip install pyinstaller pyqt6 yt-dlp
    ```

2.  **Place `ffmpeg.exe`:**
    Download `ffmpeg` from its official website and place `ffmpeg.exe` in the root directory of the project, next to `main.py`.

3.  **Generate and Modify the `.spec` file:**
    This file tells PyInstaller how to bundle your application. Run the following command in the terminal:
    ```bash
    pyi-makespec --windowed --onefile main.py
    pyinstaller main.spec
    ```



    After the process is complete, you will find the standalone executable file in the `dist` folder.
-----------------------------------------------------------------------------------------------------------------------------

📄 授權協議 / License
本專案採用 MIT 授權協議。詳情請見(LICENSE) 檔案。

This project is licensed under the MIT License - see the(LICENSE) file for details.
