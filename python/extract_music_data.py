import os
import sys
from bs4 import BeautifulSoup
import pandas as pd
import re

def get_external_file_path(relative_path, subdirectory=None):
    """
    exeファイルと同じディレクトリ、またはそのサブディレクトリにある外部ファイルのパスを取得する。
    """
    if hasattr(sys, 'frozen'): # PyInstallerでフリーズされている場合
        base_dir = os.path.dirname(sys.executable)
    else: # 通常のPythonスクリプトとして実行されている場合
        base_dir = os.path.abspath(os.path.dirname(sys.argv[0])) # os.path.dirname(os.path.abspath(__file__)) も可

    if subdirectory:
        full_path = os.path.join(base_dir, subdirectory, relative_path)
    else:
        full_path = os.path.join(base_dir, relative_path)
    return full_path

# extract_music_data 関数内のファイルパス指定はそのまま
# html_file_path = get_external_file_path('html.txt')
# csv_file_path = 'extracted_music_data.csv'



def extract_music_data():
    """
    HTMLファイルから楽曲データを抽出し、CSVファイルに保存します。
    """
    # HTMLファイルを読み込みます
    # 'html.txt'ファイルがこのPythonスクリプトと同じディレクトリにあることを確認してください
    html_file_path = get_external_file_path('html.txt') # <-- 追加/変更
    with open(html_file_path, 'r', encoding='utf-8') as f: # <-- 変更
        html_content = f.read()

    # HTMLコンテンツをパース（解析）します
    soup = BeautifulSoup(html_content, 'html.parser')

    # 抽出したデータを格納するリスト
    extracted_data = []

    # 楽曲ブロックのクラス名が 'music_master_score_back' または 'music_expert_score_back' など複数あるため、
    # 'music_' で始まり '_score_back' で終わるクラス名を持つdiv要素を検索します。
    song_blocks = soup.find_all('div', class_=re.compile(r'music_.*_score_back'))

    for block in song_blocks:
        song_name = None
        difficulty = None
        dx_or_std = None
        score = None # スコアを初期化

        # 曲名を抽出
        name_block = block.find('div', class_='music_name_block')
        if name_block:
            song_name = name_block.get_text(strip=True)

        # 難易度を抽出
        diff_img = block.find('img', class_='h_20 f_l')
        if diff_img:
            if 'diff_master.png' in diff_img['src']:
                difficulty = 'MAS'
            elif 'diff_remaster.png' in diff_img['src']:
                difficulty = 'ReMAS'
            elif 'diff_expert.png' in diff_img['src']:
                difficulty = 'EXP'
            elif 'diff_advanced.png' in diff_img['src']:
                difficulty = 'ADVANCED'
            elif 'diff_basic.png' in diff_img['src']:
                difficulty = 'BASIC'

        # DX or STDを抽出
        dx_img = block.find('img', src=re.compile(r'music_dx\.png'))
        std_img = block.find('img', src=re.compile(r'music_standard\.png'))
        if dx_img:
            dx_or_std = 'DX'
        elif std_img:
            dx_or_std = 'STD'

        # スコアを抽出
         # スコアを抽出
        # 全てのスコアラベルを持つ<td>要素を見つけます
        score_labels = block.find_all('td', class_=re.compile(r'.*_score_label'))
        score = None
        # スコアが2つ以上存在する場合、2番目のスコアを選択します (インデックスは1)
        if len(score_labels) > 1:
            score_text = score_labels[1].get_text(strip=True) # 2番目のスコアを選択
            # スコアが '― %' の場合は、このエントリをスキップします
            if '― %' in score_text:
                continue
            try:
                # '%'記号を削除し、float型に変換してから10000を掛けます
                score = float(score_text.replace('%', '')) * 10000
                score = int(score)  # 整数に変換します
            except ValueError:
                score = None
        elif len(score_labels) == 1: # スコアが1つしかない場合は、そのスコアを選択
            score_text = score_labels[0].get_text(strip=True)
            if '― %' in score_text:
                continue
            try:
                score = float(score_text.replace('%', '')) * 10000
                score = int(score)
            except ValueError:
                score = None

        # すべての必要な情報が揃っている場合のみ、データに追加します
        if song_name and difficulty and dx_or_std and score is not None:
            extracted_data.append({
                '曲名': song_name,
                '難易度': difficulty,
                'STDORDX': dx_or_std,
                'スコア': score
            })

    # 抽出したデータからDataFrameを作成します
    df = pd.DataFrame(extracted_data)

    # CSVファイルとして出力します
    csv_file_path = 'extracted_music_data.csv'
    df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')

    print(f"データが正常に抽出され、{csv_file_path} に保存されました。")
    
extract_music_data()