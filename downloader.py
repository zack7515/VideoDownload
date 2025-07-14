# downloader.py

import os
import subprocess # <--- 新增此行，用於手動呼叫 ffmpeg
import tempfile   # <--- 新增此行，用於管理暫存檔案
from yt_dlp import YoutubeDL

def get_available_formats(url):
    ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    formats = info.get('formats', [])
    video_title = info.get('title', 'video')
    processed_formats = []
    unique_formats = {}
    for f in formats:
        filesize_mb = (f.get('filesize') or f.get('filesize_approx') or 0) / (1024 * 1024)
        if filesize_mb < 0.1: continue
        if f.get('vcodec') == 'none' and f.get('acodec') == 'none': continue
        
        resolution = f.get('resolution', f"{f.get('height', '?')}p")
        ext = f.get('ext', 'unknown')
        
        # 使用解析度和類型作為唯一鍵，避免重複顯示
        key = f"{resolution}_{f.get('vcodec') != 'none' and f.get('acodec') != 'none'}"
        if key in unique_formats: continue
        unique_formats[key] = True

        format_info = {
            'format_id': f.get('format_id'),
            'video_format_id': f.get('format_id') if f.get('vcodec') != 'none' else None,
            'audio_format_id': 'bestaudio' if f.get('acodec') == 'none' else f.get('format_id'),
            'ext': ext,
            'filesize_mb': filesize_mb,
            'title': video_title,
            'resolution_val': f.get('height', 0)
        }
        
        is_video_only = f.get('vcodec') != 'none' and f.get('acodec') == 'none'
        is_progressive = f.get('vcodec') != 'none' and f.get('acodec') != 'none'
        
        if is_progressive:
            display_text = f"{resolution} [{ext.upper()}] ({filesize_mb:.1f}MB) - 影音合一"
            format_info.update({'display_text': display_text, 'type': 'progressive'})
            processed_formats.append(format_info)
        elif is_video_only:
            display_text = f"{resolution} [{ext.upper()}] ({filesize_mb:.1f}MB) - 僅影像 (需合併)"
            format_info.update({'display_text': display_text, 'type': 'adaptive'})
            processed_formats.append(format_info)

    processed_formats.sort(key=lambda x: x['resolution_val'], reverse=True)
    return processed_formats


def download_video(url, selected_format, save_path, progress_signal, finished_signal, failed_signal, status_signal):
    """
    核心下載函式，手動分開下載影音，再使用 ffmpeg 精準合併。
    """
    temp_dir = tempfile.gettempdir()
    video_path = None
    audio_path = None

    try:
        # --- 步驟 1: 下載影像串流 ---
        status_signal.emit("步驟 1/3: 下載影像中...")
        video_format_id = selected_format['video_format_id']
        
        # 建立暫存影像檔的路徑模板
        video_out_tmpl = os.path.join(temp_dir, f'%(id)s_video.%(ext)s')
        
        video_opts = {
            'format': video_format_id,
            'outtmpl': video_out_tmpl,
            'quiet': True, 'no_warnings': True
        }
        with YoutubeDL(video_opts) as ydl:
            meta = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(meta)
        
        progress_signal.emit(33) # 進度推進 1/3

        # --- 步驟 2: 下載音訊串流 (如果是自適應串流) ---
        if selected_format['type'] == 'adaptive':
            status_signal.emit("步驟 2/3: 下載音訊中...")
            audio_format_id = 'bestaudio' # 永遠獲取最佳音訊
            
            # 建立暫存音訊檔的路徑模板
            audio_out_tmpl = os.path.join(temp_dir, f'%(id)s_audio.%(ext)s')

            audio_opts = {
                'format': audio_format_id,
                'outtmpl': audio_out_tmpl,
                'quiet': True, 'no_warnings': True
            }
            with YoutubeDL(audio_opts) as ydl:
                meta = ydl.extract_info(url, download=True)
                audio_path = ydl.prepare_filename(meta)
        
        progress_signal.emit(66) # 進度推進 2/3

        # --- 步驟 3: 使用 ffmpeg 合併 ---
        status_signal.emit("步驟 3/3: 使用 ffmpeg 合併影音...")
        
        # 準備 ffmpeg 指令
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',  # 如果目標檔案已存在，直接覆蓋
            '-i', video_path, # 輸入影像檔
        ]
        if audio_path:
            ffmpeg_cmd.extend(['-i', audio_path]) # 輸入音訊檔 (如果存在)
        
        ffmpeg_cmd.extend([
            '-c:v', 'copy',      # 直接複製影像流，不重新編碼 (速度最快)
            '-c:a', 'aac',       # 將音訊流轉碼為 AAC (相容性最好)
            '-b:a', '192k',      # 設定音訊位元率為 192kbps
            str(save_path)       # 最終輸出檔案路徑
        ])

        # 執行 ffmpeg 指令，並隱藏其 console 視窗
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))

        progress_signal.emit(100)
        finished_signal.emit(str(save_path))

    except Exception as e:
        import traceback
        error_info = traceback.format_exc()
        # 附上 ffmpeg 的錯誤訊息 (如果有的話)
        if isinstance(e, subprocess.CalledProcessError):
            error_info += f"\n\nFFMPEG Error:\n{e.stderr.decode('utf-8', errors='ignore')}"
        failed_signal.emit(f"發生嚴重錯誤:\n{e}\n\n詳細資訊:\n{error_info}")

    finally:
        # --- 步驟 4: 清理暫存檔 ---
        try:
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
        except OSError as e:
            # 無法刪除也沒關係，只是通知一下
            print(f"Warning: Could not remove temp file: {e}")