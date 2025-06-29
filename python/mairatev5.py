import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageEnhance
import os
import sys
from bs4 import BeautifulSoup
import pandas as pd
import re
import tkinter.font as tkfont
# --- 定数 ---
print("mairatev5.pyを実行中...しばらくお待ちください")

def get_resource_path(relative_path):
    """
    リソースファイルの絶対パスを取得する。
    PyInstallerでバンドルされていても、されていなくても、
    常に実行ファイル/スクリプトと同じディレクトリを基準にする。
    """
    # 実行ファイルのパス (またはスクリプトのパス) を取得
    if hasattr(sys, 'frozen'): # PyInstallerでフリーズされている場合
        base_path = os.path.dirname(sys.executable)
    else: # 通常のPythonスクリプトとして実行されている場合
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    return os.path.join(base_path, relative_path)

# 定数の定義はそのまま


APP_TITLE = "mairate_bynomaji_AI(@nomaji1030)"
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
TABLE_COLS = 5 # 横方向のセル数は共通

# 新曲用設定
NEW_SONG_MASTER_CSV_PATH = get_resource_path("new_song_master.csv")
NEW_SONGS_TABLE_ROWS = 3
MAX_NEW_SONGS_DISPLAY = NEW_SONGS_TABLE_ROWS * TABLE_COLS # 15

# 旧曲用設定
OLD_SONG_MASTER_CSV_PATH = get_resource_path("old_song_master.csv")
OLD_SONGS_TABLE_ROWS = 7
MAX_OLD_SONGS_DISPLAY = OLD_SONGS_TABLE_ROWS * TABLE_COLS # 35

# セルとフォント設定 (共通)
CELL_WIDTH = 190
CELL_HEIGHT = 120
HEADING_FONT_SIZE = 18 # 小見出し用フォントサイズ
HEADING_AREA_HEIGHT = 40 # 小見出しエリアの高さ
CELL_PADDING = 5 # セル内テキストのパディング

RATE_PASSING =  12# レート値の下に空白を入れるためのスペース

FONT_NAME = "Yu Gothic UI"
FONT_SIZE_RATE = 23
FONT_SIZE_TITLE = 15
FONT_SIZE_DETAIL = 12

# --- 修正箇所: 新たなフォントサイズ定数を追加 ---
FONT_SIZE_TOTAL_RATE = 40 # 総合計レートのフォントサイズ
# --- 修正箇所ここまで ---


BACKGROUND_IMAGE_PATH = get_resource_path("background.png")
EXPLANATION_IMAGE_PATH = get_resource_path("explanation.png")

IMAGES_DIR =get_resource_path("ジャケット") 

from calculate import calculate_rate
from extract_music_data import extract_music_data

class RatingApp:
    """ レーティング表作成アプリ """

    def __init__(self, master):
        self.master = master
        master.title(APP_TITLE)
        master.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

        self.song_data_list = [] # 全ての入力楽曲データ
        self.new_song_master_data = {}
        self.old_song_master_data = {}
        self.load_all_master_data() # 両方のマスタデータを読み込む

        self.image_cache = {}

        try:
            self.bg_image = Image.open(BACKGROUND_IMAGE_PATH)
            self.bg_photo_image = ImageTk.PhotoImage(self.bg_image.resize((WINDOW_WIDTH, WINDOW_HEIGHT)))
            self.bg_label = tk.Label(master, image=self.bg_photo_image)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except FileNotFoundError:
            print(f"背景画像 {BACKGROUND_IMAGE_PATH} が見つかりません。")
        except Exception as e:
            print(f"背景画像の読み込みエラー: {e}")

        

        # --- GUI要素 ---
        input_frame = ttk.Frame(master, padding="10")
        input_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(input_frame, text="曲名:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.song_name_entry = ttk.Entry(input_frame, width=30)
        self.song_name_entry.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(input_frame, text="難易度:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.difficulty_entry = ttk.Entry(input_frame, width=10)
        self.difficulty_entry.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(input_frame, text="STD/DX:").grid(row=0, column=4, padx=5, pady=2, sticky="w")
        self.std_or_dx_entry = ttk.Entry(input_frame, width=5)
        self.std_or_dx_entry.grid(row=0, column=4, padx=5, pady=2)

        ttk.Label(input_frame, text="スコア:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.score_entry = ttk.Entry(input_frame, width=10)
        self.score_entry.grid(row=1, column=1, padx=5, pady=2)

        self.add_button = ttk.Button(input_frame, text="追加", command=self.add_song_data)
        self.add_button.grid(row=1, column=2, padx=5, pady=2)
        
        bigfont = tkfont.Font(size=18, weight="bold")  # お好みでサイズや太さを調整

        style = ttk.Style()
        style.configure("Big.TButton", font=bigfont)

# ボタン作成時に style="Big.TButton" を指定
        self.add_button = ttk.Button(input_frame, text="全自動処理", command=self.fully_automatic_processing, style="Big.TButton")
        self.add_button.grid(row=1, column=4, padx=5, pady=2)

        self.import_csv_button = ttk.Button(input_frame, text="スコアCSVインポート", command=self.import_scores_from_csv)
        self.import_csv_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        self.calculate_button = ttk.Button(input_frame, text="レート計算＆表示", command=self.calculate_and_display_ratings)
        self.calculate_button.grid(row=2, column=2, columnspan=2, padx=5, pady=5)

        self.export_button = ttk.Button(input_frame, text="画像エクスポート", command=self.export_table_as_image, state=tk.DISABLED)
        self.export_button.grid(row=2, column=4, columnspan=2, padx=5, pady=5)

        try:
            self.bg_explanation = Image.open(EXPLANATION_IMAGE_PATH)
            self.bg_photo_explanation = ImageTk.PhotoImage(self.bg_explanation.resize((300,100)))
            self.bg_label = tk.Label(input_frame, image=self.bg_photo_explanation)
            self.bg_label.place( x=WINDOW_WIDTH/1.5, y=0,  relwidth=0.5, relheight=1    )
        except FileNotFoundError:
            print(f"背景画像 {EXPLANATION_IMAGE_PATH} が見つかりません。")
        except Exception as e:
            print(f"背景画像の読み込みエラー: {e}")

        # --- Canvas設定 ---
        self.canvas_frame = ttk.Frame(master)
        self.canvas_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Canvasのスクロール領域を計算 (総合計エリア + 新曲ヘッダ + 新曲セル + 旧曲ヘッダ + 旧曲セル)
        # --- 修正箇所: 総合計表示用の高さ HEADING_AREA_HEIGHT を追加 ---
        total_canvas_height = (HEADING_AREA_HEIGHT + # 総合計表示エリア
                               HEADING_AREA_HEIGHT + NEW_SONGS_TABLE_ROWS * CELL_HEIGHT +
                               HEADING_AREA_HEIGHT + OLD_SONGS_TABLE_ROWS * CELL_HEIGHT)
        # --- 修正箇所ここまで ---
        total_canvas_width = CELL_WIDTH * TABLE_COLS

        self.canvas = tk.Canvas(self.canvas_frame, bg="white", scrollregion=(0,0, total_canvas_width, total_canvas_height))
        self.canvas.pack(side="left", fill="both", expand=True)

        v_scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        v_scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=v_scrollbar.set)

        h_scrollbar = ttk.Scrollbar(master, orient="horizontal", command=self.canvas.xview)
        h_scrollbar.pack(fill="x", padx=10, pady=(0,10))
        self.canvas.configure(xscrollcommand=h_scrollbar.set)

    def _load_master_csv(self, csv_filepath):
        master_data = {}
        try:
            with open(csv_filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                if 'STDORDX' not in reader.fieldnames: # 共通チェック
                    messagebox.showerror("マスタCSVエラー", f"{csv_filepath} に 'STDORDX' 列がありません。")
                    return {}
                for row in reader:
                    key = (row['曲名'], row['難易度'], row['STDORDX'])
                    master_data[key] = {
                        '譜面定数': float(row['譜面定数']),
                        'レベル': row['レベル'],
                        'STDORDX_val': row['STDORDX'],
                        '画像ファイル名': row.get('画像ファイル名', '')
                    }
            print(f"{csv_filepath} を読み込みました。")
        except FileNotFoundError:
            print(f"エラー: {csv_filepath} が見つかりません。")
            messagebox.showwarning("マスタファイルエラー", f"{csv_filepath} が見つかりません。処理は続行されますが、該当曲の情報は取得できません。")
        except Exception as e:
            print(f"{csv_filepath} の読み込みエラー: {e}")
        return master_data

    def load_all_master_data(self):
        self.new_song_master_data = self._load_master_csv(NEW_SONG_MASTER_CSV_PATH)
        self.old_song_master_data = self._load_master_csv(OLD_SONG_MASTER_CSV_PATH)

        if not self.new_song_master_data and not self.old_song_master_data:
            messagebox.showerror("マスタデータ重大エラー", "新旧どちらの楽曲マスタCSVも読み込めませんでした。アプリを正しく使用できません。")
        elif not self.new_song_master_data:
            print(f"警告: {NEW_SONG_MASTER_CSV_PATH} は空か読み込めませんでした。")
        elif not self.old_song_master_data:
            print(f"警告: {OLD_SONG_MASTER_CSV_PATH} は空か読み込めませんでした。")


    def add_song_data(self):
        song_name = self.song_name_entry.get()
        difficulty = self.difficulty_entry.get()
        std_or_dx = self.std_or_dx_entry.get().upper()
        score_str = self.score_entry.get()

        if not all([song_name, difficulty, std_or_dx, score_str]):
            messagebox.showerror("入力エラー", "曲名、難易度、STD/DX、スコアをすべて入力してください。")
            return
        if std_or_dx not in ["STD", "DX"]:
            messagebox.showerror("入力エラー", "STD/DXは 'STD' または 'DX' で入力してください。")
            return
        try: score = int(score_str)
        except ValueError:
            messagebox.showerror("入力エラー", "スコアは数値で入力してください。")
            return

        self._add_song_to_list(song_name, difficulty, std_or_dx, score)
        self.song_name_entry.delete(0, tk.END)
        self.difficulty_entry.delete(0, tk.END)
        self.std_or_dx_entry.delete(0, tk.END)
        self.score_entry.delete(0, tk.END)
        # print(f"追加: {song_name} ({difficulty} / {std_or_dx}) - スコア: {score}")

    def _add_song_to_list(self, song_name, difficulty, std_or_dx, score):
        master_key = (song_name, difficulty, std_or_dx)
        song_type = 'unknown'
        chart_info = None
  
        if master_key in self.new_song_master_data:
            chart_info = self.new_song_master_data[master_key]
            song_type = 'new'
        elif master_key in self.old_song_master_data:
            chart_info = self.old_song_master_data[master_key]
            song_type = 'old'
        else:
            messagebox.showwarning("マスタ参照エラー", f"楽曲「{song_name} ({difficulty} / {std_or_dx})」が新旧どちらのマスタにも見つかりません。")
            chart_info = {'譜面定数': 0.0, 'レベル': 'N/A', 'STDORDX_val': std_or_dx, '画像ファイル名': ''}
            # song_type remains 'unknown'

        song_entry = {
            '曲名': song_name,
            '難易度': difficulty,
            'STDORDX': std_or_dx,
            'スコア': score,
            '譜面定数': chart_info['譜面定数'],
            'レベル': chart_info['レベル'],
            '画像パス': os.path.join(IMAGES_DIR, chart_info['画像ファイル名']) if chart_info.get('画像ファイル名') else '',
            'レート値': 0.0,
            'song_type': song_type # 曲のタイプ (new/old/unknown) を格納
        }
        self.song_data_list.append(song_entry)
        print(f"追加 ({song_type}): {song_name} ({difficulty} / {std_or_dx}) - スコア: {score}")


    def import_scores_from_csv(self):
        # (_add_song_to_list が song_type を設定する)
        filepath = filedialog.askopenfilename(title="スコアCSVファイルを選択", filetypes=[("CSVファイル", "*.csv")])
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                required_headers = ['曲名', '難易度', 'STDORDX', 'スコア']
                if not all(header in reader.fieldnames for header in required_headers):
                    messagebox.showerror("CSVフォーマットエラー", f"CSVファイルには '{', '.join(required_headers)}' のヘッダーが必要です。")
                    return
                imported_count = 0
                for row in reader:
                    try:
                        song_name = row['曲名']
                        difficulty = row['難易度']
                        std_or_dx = row['STDORDX'].upper()
                        score = int(row['スコア'])
                        if std_or_dx not in ["STD", "DX"]:
                            print(f"警告: STDORDXの値が不正な行 (STD/DX以外): {row}")
                            continue
                        self._add_song_to_list(song_name, difficulty, std_or_dx, score)
                        imported_count += 1
                    except ValueError: print(f"警告: スコア形式不正: {row}")
                    except KeyError as e: print(f"警告: CSV必須列不足 ({e}): {row}")
            messagebox.showinfo("インポート完了", f"{imported_count} 件の楽曲データを処理しました。")
        except FileNotFoundError: messagebox.showerror("エラー", "ファイルが見つかりません。")
        except Exception as e: messagebox.showerror("インポートエラー", f"CSV処理エラー: {e}")

    def automotive_csv(self):
        # (全自動処理のCSVインポート)
        filepath = "extracted_music_data.csv"
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                required_headers = ['曲名', '難易度', 'STDORDX', 'スコア']
                if not all(header in reader.fieldnames for header in required_headers):
                    messagebox.showerror("CSVフォーマットエラー", f"CSVファイルには '{', '.join(required_headers)}' のヘッダーが必要です。")
                    return
                imported_count = 0
                for row in reader:
                    try:
                        song_name = row['曲名']
                        difficulty = row['難易度']
                        std_or_dx = row['STDORDX'].upper()
                        score = int(row['スコア'])
                        if std_or_dx not in ["STD", "DX"]:
                            print(f"警告: STDORDXの値が不正な行 (STD/DX以外): {row}")
                            continue
                        self._add_song_to_list(song_name, difficulty, std_or_dx, score)
                        imported_count += 1
                    except ValueError: print(f"警告: スコア形式不正: {row}")
                    except KeyError as e: print(f"警告: CSV必須列不足 ({e}): {row}")
            messagebox.showinfo("インポート完了", f"{imported_count} 件の楽曲データを処理しました。")
        except FileNotFoundError: messagebox.showerror("エラー", "ファイルが見つかりません。")
        except Exception as e: messagebox.showerror("インポートエラー", f"CSV処理エラー: {e}")


    def calculate_and_display_ratings(self):
        if not self.song_data_list:
            messagebox.showinfo("情報", "表示する楽曲データがありません。")
            return

        for song in self.song_data_list:
            try:
                level = float(song['譜面定数'])
                achievement_rate = float(song['スコア'])
                song['レート値'] = calculate_rate(level, achievement_rate)
            except (ValueError, TypeError): # 譜面定数が0.0の場合なども考慮
                song['レート値'] = 0.0
            except Exception as e:
                song['レート値'] = 0.0
                print(f"レート計算中に予期せぬエラー: {song['曲名']} - {e}")

        # 新曲と旧曲に分類
        new_songs_processed = [s for s in self.song_data_list if s['song_type'] == 'new']
        old_songs_processed = [s for s in self.song_data_list if s['song_type'] == 'old']

        # それぞれソートして上位曲を取得
        self.top_new_songs = sorted(new_songs_processed, key=lambda s: s['レート値'], reverse=True)[:MAX_NEW_SONGS_DISPLAY]
        self.top_old_songs = sorted(old_songs_processed, key=lambda s: s['レート値'], reverse=True)[:MAX_OLD_SONGS_DISPLAY]

        # --- 修正箇所: 小計と合計を計算 ---
        self.new_songs_subtotal_rate = sum(s['レート値'] for s in self.top_new_songs)
        self.old_songs_subtotal_rate = sum(s['レート値'] for s in self.top_old_songs)
        self.total_rate = self.new_songs_subtotal_rate + self.old_songs_subtotal_rate
        # --- 修正箇所ここまで ---

        self.display_rating_tables() # 複数形に変更
        self.export_button.config(state=tk.NORMAL)

    def _draw_song_cell_on_canvas(self, song, base_x, base_y):
        """ Canvasに1つの楽曲セルを描画するヘルパー """
        x1, y1 = base_x, base_y
        x2, y2 = x1 + CELL_WIDTH, y1 + CELL_HEIGHT

        img_path = song.get('画像パス', '')
        if img_path and os.path.exists(img_path):
            if img_path not in self.image_cache:
                try:
                    img = Image.open(img_path).resize((CELL_WIDTH, CELL_HEIGHT), Image.LANCZOS)
                    # 明るさを調整する処理を追加
                    brightness_factor = 0.5 # 0.0 (黒) から 1.0 (元の明るさ) の範囲で調整
                    enhancer = ImageEnhance.Brightness(img)
                    img_brightness_adjusted = enhancer.enhance(brightness_factor)

                    self.image_cache[img_path] = ImageTk.PhotoImage(img_brightness_adjusted)
                    
                except Exception as e:
                    print(f"画像読み込みエラー ({img_path}): {e}")
                    self.image_cache[img_path] = None
            if self.image_cache[img_path]:
                self.canvas.create_image(x1, y1, anchor="nw", image=self.image_cache[img_path])
            else: self.canvas.create_rectangle(x1, y1, x2, y2, fill="darkgrey", outline="black")
        else:
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="darkgrey", outline="black")
            if img_path: print(f"画像ファイルが見つかりません: {img_path}")

        text_x = x1 + CELL_PADDING
        rate_y = y1  # CELL_PADDINGを0に
        self.canvas.create_text(text_x, rate_y, anchor="nw", text=f"{song['レート値']:.0f}", font=(FONT_NAME, FONT_SIZE_RATE, "bold"), fill="yellow")

        # 空行を追加 (Canvas表示ではこの空行は特に意味を持たないが、レイアウトの一貫性のため残す)
        # blank_y = rate_y + FONT_SIZE_RATE + CELL_PADDING // 2
        # self.canvas.create_text(text_x, blank_y, anchor="nw", text="", font=(FONT_NAME, FONT_SIZE_RATE))
        
        # タイトル、難易度、定数、スコアの描画位置を調整
        # レート値の下に直接タイトルを配置する
        title_y = rate_y + FONT_SIZE_RATE + CELL_PADDING   +RATE_PASSING    # レート値の下に少しスペースを空ける,レート値の下はさらに空白
    

        song_name_display = song['曲名']
        # フォントサイズとCELL_WIDTHに基づいて最大文字数を計算
        # ImageFont.getsizeで正確なピクセル幅を取得する代わりに、おおよその比率で計算
        max_title_len = int(CELL_WIDTH / (FONT_SIZE_TITLE * 0.65)) # 0.65は経験的な値

        if len(song_name_display) > max_title_len:
            song_name_display = song_name_display[:max_title_len-1] + "…"
        self.canvas.create_text(text_x, title_y, anchor="nw", text=song_name_display, font=(FONT_NAME, FONT_SIZE_TITLE), fill="white")
        
        difficulty_y = title_y + FONT_SIZE_TITLE + 1.5*CELL_PADDING
        self.canvas.create_text(text_x, difficulty_y, anchor="nw", text=f"{song['難易度']} [{song['レベル']}]", font=(FONT_NAME, FONT_SIZE_DETAIL), fill="white")
        
        const_y = difficulty_y + FONT_SIZE_DETAIL + CELL_PADDING
        self.canvas.create_text(text_x, const_y, anchor="nw", text=f"定数:{song['譜面定数']:.1f} ({song['STDORDX']})", font=(FONT_NAME, FONT_SIZE_DETAIL), fill="white")
        
        achivescore_y = const_y + FONT_SIZE_DETAIL + CELL_PADDING
        self.canvas.create_text(text_x, achivescore_y, anchor="nw",
                                    text=f"スコア:{song['スコア']/10000:.4f} % ",
                                    font=(FONT_NAME, FONT_SIZE_DETAIL), fill="white")


    def display_rating_tables(self):
        self.canvas.delete("all")
        current_y_offset = 0

        # --- 修正箇所: 総合計レートの表示を追加 ---
        if hasattr(self, 'total_rate'):
            total_rate_text = f"総合計レート: {self.total_rate:.0f}"
            self.canvas.create_text(WINDOW_WIDTH / 2, current_y_offset + HEADING_AREA_HEIGHT / 2, anchor="center",
                                    text=total_rate_text, font=(FONT_NAME, FONT_SIZE_TOTAL_RATE, "bold"), fill="red")
        current_y_offset += HEADING_AREA_HEIGHT # 総合計表示エリアの高さ
        # --- 修正箇所ここまで ---


        # 1. 新曲テーブル描画
        # --- 修正箇所: 新曲小計表示を追加 ---
        new_heading_text = f"新曲 (Top {MAX_NEW_SONGS_DISPLAY})　小計: {self.new_songs_subtotal_rate:.0f}" if hasattr(self, 'new_songs_subtotal_rate') else f"新曲 (Top {MAX_NEW_SONGS_DISPLAY})"
        self.canvas.create_text(10, current_y_offset + HEADING_AREA_HEIGHT / 2, anchor="w",
                                text=new_heading_text,
                                font=(FONT_NAME, HEADING_FONT_SIZE, "bold"), fill="black")
        # --- 修正箇所ここまで ---
        current_y_offset += HEADING_AREA_HEIGHT

        if hasattr(self, 'top_new_songs'):
            for i, song in enumerate(self.top_new_songs):
                row = i // TABLE_COLS
                col = i % TABLE_COLS
                cell_base_x = col * CELL_WIDTH
                cell_base_y = current_y_offset + row * CELL_HEIGHT
                self._draw_song_cell_on_canvas(song, cell_base_x, cell_base_y)
        current_y_offset += NEW_SONGS_TABLE_ROWS * CELL_HEIGHT # 新曲テーブル分の高さを加算

        # 2. 旧曲テーブル描画
        # --- 修正箇所: 旧曲小計表示を追加 ---
        old_heading_text = f"旧曲 (Top {MAX_OLD_SONGS_DISPLAY})　小計: {self.old_songs_subtotal_rate:.0f}" if hasattr(self, 'old_songs_subtotal_rate') else f"旧曲 (Top {MAX_OLD_SONGS_DISPLAY})"
        self.canvas.create_text(10, current_y_offset + HEADING_AREA_HEIGHT / 2, anchor="w",
                                text=old_heading_text,
                                font=(FONT_NAME, HEADING_FONT_SIZE, "bold"), fill="black")
        # --- 修正箇所ここまで ---
        current_y_offset += HEADING_AREA_HEIGHT

        if hasattr(self, 'top_old_songs'):
            for i, song in enumerate(self.top_old_songs):
                row = i // TABLE_COLS
                col = i % TABLE_COLS
                cell_base_x = col * CELL_WIDTH
                cell_base_y = current_y_offset + row * CELL_HEIGHT
                self._draw_song_cell_on_canvas(song, cell_base_x, cell_base_y)
        
        # Canvasのスクロール範囲を明示的に設定 (bbox("all")は時々不正確になることがあるため)
        # --- 修正箇所: 総合計表示エリアの高さを含むように最終高さを調整 ---
        final_height = (HEADING_AREA_HEIGHT + # 総合計表示エリア
                        HEADING_AREA_HEIGHT + NEW_SONGS_TABLE_ROWS * CELL_HEIGHT +
                        HEADING_AREA_HEIGHT + OLD_SONGS_TABLE_ROWS * CELL_HEIGHT)
        # --- 修正箇所ここまで ---
        self.canvas.config(scrollregion=(0, 0, TABLE_COLS * CELL_WIDTH, final_height))


    def _draw_song_cell_on_image(self, draw, song, base_x, base_y, fonts):
        """ Pillow Imageに1つの楽曲セルを描画するヘルパー """
        x1, y1 = base_x, base_y
        
        # 画像の描画は呼び出し元で行うため、ここではテキスト描画のみ
        text_x = x1 + CELL_PADDING
        rate_y = y1  # CELL_PADDINGを0に
        draw.text((text_x, rate_y), f"{song['レート値']:.0f}", font=fonts['rate'], fill="yellow")
        
        title_y = rate_y + FONT_SIZE_RATE + CELL_PADDING + RATE_PASSING # RATE_PASSINGをここでも適用
        song_name_display = song['曲名']
        max_title_len = int(CELL_WIDTH / (FONT_SIZE_TITLE * 0.65))
        if len(song_name_display) > max_title_len:
            song_name_display = song_name_display[:max_title_len-1] + "…"
        draw.text((text_x, title_y), song_name_display, font=fonts['title'], fill="white")
        
        difficulty_y = title_y + FONT_SIZE_TITLE + 1.5*CELL_PADDING # 1.5*CELL_PADDINGをここでも適用
        draw.text((text_x, difficulty_y), f"{song['難易度']} [{song['レベル']}]", font=fonts['detail'], fill="white")
        
        const_y = difficulty_y + FONT_SIZE_DETAIL + CELL_PADDING
        draw.text((text_x, const_y), f"定数:{song['譜面定数']:.1f} ({song['STDORDX']})", font=fonts['detail'], fill="white")

        achivescore_y = const_y + FONT_SIZE_DETAIL + CELL_PADDING
        draw.text((text_x, achivescore_y),
                  text=f"スコア:{song['スコア']/10000:.4f} % ", # スコアキーを修正
                  font=fonts['detail'], fill="white")


    def export_table_as_image(self):
        if not ((hasattr(self, 'top_new_songs') and self.top_new_songs) or \
                (hasattr(self, 'top_old_songs') and self.top_old_songs)):
            messagebox.showinfo("情報", "エクスポートするデータがありません。")
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNGファイル", "*.png"), ("JPEGファイル", "*.jpg")], title="画像を保存")
        if not filepath: return

        try:
            img_width = TABLE_COLS * CELL_WIDTH
            # --- 修正箇所: 画像の高さに総合計表示エリアの分を追加 ---
            img_height = (HEADING_AREA_HEIGHT + # 総合計表示エリア
                          HEADING_AREA_HEIGHT + NEW_SONGS_TABLE_ROWS * CELL_HEIGHT +
                          HEADING_AREA_HEIGHT + OLD_SONGS_TABLE_ROWS * CELL_HEIGHT)
            # --- 修正箇所ここまで ---

            image = Image.new("RGB", (img_width, img_height), "white") # 背景色
            draw = ImageDraw.Draw(image)
            
            fonts = {}
            # フォントファイルパスの調整
            # get_resource_path を使用して、バンドルされたフォントファイルを見つける
            font_path_base = get_resource_path("") # リソースのルートパスを取得
            
            try:
                # Windows標準の日本語フォントを明示的に指定
                jp_font_path = "C:/Windows/Fonts/meiryo.ttc"
                fonts['heading'] = ImageFont.truetype(jp_font_path, HEADING_FONT_SIZE)
                fonts['rate'] = ImageFont.truetype(jp_font_path, FONT_SIZE_RATE)
                fonts['title'] = ImageFont.truetype(jp_font_path, FONT_SIZE_TITLE)
                fonts['detail'] = ImageFont.truetype(jp_font_path, FONT_SIZE_DETAIL)
                # --- 修正箇所: 総合計レート用フォントを追加 ---
                fonts['total_rate'] = ImageFont.truetype(jp_font_path, FONT_SIZE_TOTAL_RATE)
                # --- 修正箇所ここまで ---
            except IOError:
                print(f"警告: 指定フォント({jp_font_path})が見つかりません。代替フォントを使用。")
                print(f"警告: 指定フォント({FONT_NAME})が見つかりません。代替フォントを使用。")
                # OS依存の代替案
                if os.name == 'nt': # Windows
                    default_font_name = "arial.ttf"
                    default_bold_font_name = "arialbd.ttf"
                else: # macOS/Linux (一般的なフォント)
                    default_font_name = "DejaVuSans.ttf"
                    default_bold_font_name = "DejaVuSans-Bold.ttf"

                try:
                    fonts['heading'] = ImageFont.truetype(default_bold_font_name, HEADING_FONT_SIZE)
                    fonts['rate'] = ImageFont.truetype(default_bold_font_name, FONT_SIZE_RATE)
                    fonts['title'] = ImageFont.truetype(default_font_name, FONT_SIZE_TITLE)
                    fonts['detail'] = ImageFont.truetype(default_font_name, FONT_SIZE_DETAIL)
                    # --- 修正箇所: 総合計レート用代替フォントを追加 ---
                    fonts['total_rate'] = ImageFont.truetype(default_bold_font_name, FONT_SIZE_TOTAL_RATE)
                    # --- 修正箇所ここまで ---
                except IOError as e_default_font:
                    print(f"エラー: 代替フォントも読み込めません。システムデフォルトフォントで続行します。詳細: {e_default_font}")
                    fonts['heading'] = ImageFont.load_default()
                    fonts['rate'] = ImageFont.load_default()
                    fonts['title'] = ImageFont.load_default()
                    fonts['detail'] = ImageFont.load_default()
                    # --- 修正箇所: 総合計レート用システムデフォルトフォントを追加 ---
                    fonts['total_rate'] = ImageFont.load_default()
                    # --- 修正箇所ここまで ---


            current_y_offset = 0

            # --- 修正箇所: 画像への総合計レートの描画を追加 ---
            if hasattr(self, 'total_rate'):
                total_rate_text = f"総合計レート: {self.total_rate:.0f}"
                # テキストを中央揃えにするための計算
                text_bbox = draw.textbbox((0, 0), total_rate_text, font=fonts['total_rate'])
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                text_x = (img_width - text_width) / 2
                text_y = current_y_offset + (HEADING_AREA_HEIGHT - text_height) / 2
                draw.text((text_x, text_y), total_rate_text, font=fonts['total_rate'], fill="red")
            current_y_offset += HEADING_AREA_HEIGHT # 総合計表示エリアの高さ
            # --- 修正箇所ここまで ---


            # 新曲描画
            # --- 修正箇所: 画像への新曲小計表示を追加 ---
            new_heading_text = f"新曲 (Top {MAX_NEW_SONGS_DISPLAY})　小計: {self.new_songs_subtotal_rate:.0f}" if hasattr(self, 'new_songs_subtotal_rate') else f"新曲 (Top {MAX_NEW_SONGS_DISPLAY})"
            draw.text((10, current_y_offset + HEADING_AREA_HEIGHT / 2 - fonts['heading'].getbbox("A")[3] / 2),
                      new_heading_text, font=fonts['heading'], fill="black")
            # --- 修正箇所ここまで ---
            current_y_offset += HEADING_AREA_HEIGHT
            
            if hasattr(self, 'top_new_songs'):
                for i, song in enumerate(self.top_new_songs):
                    row = i // TABLE_COLS
                    col = i % TABLE_COLS
                    x1 = col * CELL_WIDTH
                    y1_cell = current_y_offset + row * CELL_HEIGHT
                    
                    # 画像の描画と明るさ調整
                    img_path_s = song.get('画像パス', '')
                    if img_path_s and os.path.exists(img_path_s):
                        try:
                            s_img = Image.open(img_path_s).resize((CELL_WIDTH, CELL_HEIGHT), Image.LANCZOS)
                            # 明るさ調整をエクスポート時にも適用
                            brightness_factor = 0.5
                            enhancer = ImageEnhance.Brightness(s_img)
                            s_img_brightness_adjusted = enhancer.enhance(brightness_factor)
                            image.paste(s_img_brightness_adjusted, (x1, y1_cell))
                        except Exception as e_img:
                            print(f"エクスポート時画像エラー {img_path_s}: {e_img}")
                            draw.rectangle([x1, y1_cell, x1 + CELL_WIDTH, y1_cell + CELL_HEIGHT], fill="darkgrey", outline="black")
                    else:
                        draw.rectangle([x1, y1_cell, x1 + CELL_WIDTH, y1_cell + CELL_HEIGHT], fill="darkgrey", outline="black")
                    
                    # テキスト描画 (ヘルパー関数呼び出し)
                    self._draw_song_cell_on_image(draw, song, x1, y1_cell, fonts)

            current_y_offset += NEW_SONGS_TABLE_ROWS * CELL_HEIGHT

            # 旧曲描画
            # --- 修正箇所: 画像への旧曲小計表示を追加 ---
            old_heading_text = f"旧曲 (Top {MAX_OLD_SONGS_DISPLAY})　小計: {self.old_songs_subtotal_rate:.0f}" if hasattr(self, 'old_songs_subtotal_rate') else f"旧曲 (Top {MAX_OLD_SONGS_DISPLAY})"
            draw.text((10, current_y_offset + HEADING_AREA_HEIGHT / 2 - fonts['heading'].getbbox("A")[3] / 2),
                      old_heading_text, font=fonts['heading'], fill="black")
            # --- 修正箇所ここまで ---
            current_y_offset += HEADING_AREA_HEIGHT
            
            if hasattr(self, 'top_old_songs'):
                for i, song in enumerate(self.top_old_songs):
                    row = i // TABLE_COLS
                    col = i % TABLE_COLS
                    x1 = col * CELL_WIDTH
                    y1_cell = current_y_offset + row * CELL_HEIGHT
                    
                    # 画像の描画と明るさ調整
                    img_path_s = song.get('画像パス', '')
                    if img_path_s and os.path.exists(img_path_s):
                        try:
                            s_img = Image.open(img_path_s).resize((CELL_WIDTH, CELL_HEIGHT), Image.LANCZOS)
                            # 明るさ調整をエクスポート時にも適用
                            brightness_factor = 0.5
                            enhancer = ImageEnhance.Brightness(s_img)
                            s_img_brightness_adjusted = enhancer.enhance(brightness_factor)
                            image.paste(s_img_brightness_adjusted, (x1, y1_cell))
                        except Exception as e_img:
                            print(f"エクスポート時画像エラー {img_path_s}: {e_img}")
                            draw.rectangle([x1, y1_cell, x1 + CELL_WIDTH, y1_cell + CELL_HEIGHT], fill="darkgrey", outline="black")
                    else:
                        draw.rectangle([x1, y1_cell, x1 + CELL_WIDTH, y1_cell + CELL_HEIGHT], fill="darkgrey", outline="black")
                    
                    # テキスト描画
                    self._draw_song_cell_on_image(draw, song, x1, y1_cell, fonts)

            image.save(filepath)
            messagebox.showinfo("エクスポート完了", f"画像を {filepath} に保存しました。")
        except Exception as e:
            messagebox.showerror("エクスポートエラー", f"画像の保存中にエラーが発生しました: {e}")
            print(f"エクスポートエラー詳細: {e}")



    
    
    def fully_automatic_processing(self):
        print("全自動処理を開始します。")
        extract_music_data()  # CSVファイルを生成する関数を呼び出す
        self.automotive_csv()
        self.calculate_and_display_ratings()
    
    
    
   



if __name__ == '__main__':
    root = tk.Tk()
    app = RatingApp(root)
    root.mainloop()
    
  