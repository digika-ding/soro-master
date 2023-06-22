from PIL import Image, ImageDraw, ImageFont
import boto3, requests, os, time, sys
from math import ceil
from glob import glob

def calc_drill(IMG_DIR='./question/',OUT_DIR='./answer/',MARGIN=20):
    textract = boto3.client('textract',region_name='us-east-1')
    os.makedirs(OUT_DIR, exist_ok=True)
    
    print(IMG_DIR,OUT_DIR,MARGIN)
    
    # 画像の枚数分ループ
    for img_file in glob(IMG_DIR+'*.png'):
        with open(img_file,'rb') as f:
            img_bytes = f.read()
        # Textract の API を実行
        response = textract.detect_document_text(Document={'Bytes': img_bytes})
        
        # PIL で画像を開く
        img = Image.open(img_file)
        # 画像サイズを格納
        w,h = img.size
        # 問題を格納する list
        questions = []
        # 演算子とその位置を取得
        for block in response['Blocks']:
            if block['BlockType'] == 'WORD':
                if block['Text'] in ['-','+']: # - か + を取得
                    left = int(w*block['Geometry']['BoundingBox']['Left'])
                    top = int(h*block['Geometry']['BoundingBox']['Top'])
                    right = ceil(w*block['Geometry']['BoundingBox']['Left'] + w*block['Geometry']['BoundingBox']['Width'])
                    bottom = ceil(h*block['Geometry']['BoundingBox']['Top'] + h*block['Geometry']['BoundingBox']['Height'])
                    center = ((left+right)//2,(top+bottom)//2)
                    operator_symbol = block['Text']
                    questions.append({
                        'operator_symbol':{
                            'left': left,
                            'top': top,
                            'right': right,
                            'bottom': bottom,
                            'center': center,
                            'operator_symbol': operator_symbol
                        }
                    })
        # 検出した数値のみのリスト
        extract_numbers = []
        for block in response['Blocks']:
            if block['BlockType'] == 'WORD' and block['Text'].isnumeric():
                number = block['Text']
                left = int(w*block['Geometry']['BoundingBox']['Left'])
                top = int(h*block['Geometry']['BoundingBox']['Top'])
                right = ceil(w*block['Geometry']['BoundingBox']['Left'] + w*block['Geometry']['BoundingBox']['Width'])
                bottom = ceil(h*block['Geometry']['BoundingBox']['Top'] + h*block['Geometry']['BoundingBox']['Height'])
                center = ((left+right)//2,(top+bottom)//2)
                extract_numbers.append({
                        'left': left,
                        'top': top,
                        'right': right,
                        'bottom': bottom,
                        'center': center,
                        'number': number
                })
        diff = 99999 # 演算子と数値の横方向の距離を大きい数字で初期化、小さければその値を採用する
        for i,question in enumerate(questions):
            diff = 99999
            candidates = []
            for extract_number in extract_numbers:
                if question['operator_symbol']['center'][1] - MARGIN <= extract_number['center'][1] <= question['operator_symbol']['center'][1] + MARGIN:
                    candidates.append(extract_number)
            for candidate in candidates:
                if diff > candidate['center'][0] - question['operator_symbol']['center'][0] > 0:
                    diff = question['operator_symbol']['center'][0] - candidate['center'][0]
                    questions[i]['y'] = candidate
        # y キー を持たない（= 計算問題ではない演算子）を除去する
        for question in questions:
            if 'y' in question:
                pass
            else:
                questions.remove(question)
        # 引く数値として使用したものをextract_numbersから除外
        for question in questions:
            if question['y'] in extract_numbers:
                extract_numbers.remove(question['y'])
                
        diff = 99999 # 演算子と数値の横方向の距離を大きい数字で初期化、小さければその値を採用する
        for i,question in enumerate(questions):
            diff = 99999
            candidates = []
            for extract_number in extract_numbers:
                # 筆算において数字は右詰めされるため、右端の px 値で評価する
                if question['y']['right'] - MARGIN <= extract_number['right'] <= question['y']['right'] + MARGIN:
                    candidates.append(extract_number)
            for candidate in candidates:
                if diff > question['y']['center'][1] - candidate['center'][1] > 0:
                    diff = question['y']['center'][1] - candidate['center'][1]
                    questions[i]['x'] = candidate

        # eval メソッドを使って計算を解く
        for i,question in enumerate(questions):
            formula = str(question['x']['number']) + ' ' + question['operator_symbol']['operator_symbol'] + ' ' + question['y']['number']
            questions[i]['formula'] = formula
            questions[i]['answer'] = {'number':eval(formula)}
                    
        # 解答を記載
        d = ImageDraw.Draw(img)
        for i,question in enumerate(questions):
            questions[i]['answer']['top'] = question['y']['top'] + (question['y']['top'] - question['x']['top'])

            # 文字数によって開始位置を変更する
            # 1 文字あたりどれくらいの幅を取るかを width_unit に格納し、その幅分で文字の左端位置を調整する
            width_unit = ((question['y']['right'] - question['y']['left']) / len(str(question['y']['number'])))
            questions[i]['answer']['left'] = int(question['y']['left'] - (len(str(question['answer']['number'])) - len(str(question['y']['number'])))*width_unit)

            # font = ImageFont.truetype("ZenjidoJP-FeltPenLMT-TTF.ttf", round(round(width_unit)*(10/6))) # 10/6 はフォントと幅を変換する定数
            # font = ImageFont.truetype("arial.ttf", round(round(width_unit)*(10/6))) # 10/6 はフォントと幅を変換する定数
            d.text((questions[i]['answer']['left']+10, questions[i]['answer']['top']), str(questions[i]['answer']['number']), fill='black',align='right') # +10 は手書き文字フォント用マジックナンバー
        # 解答を保存
        img.save(img_file.replace(IMG_DIR,OUT_DIR))
    return 0

if __name__ == "__main__":
    img_dir = sys.argv[1]
    out_dir = sys.argv[2]
    margin = int(sys.argv[3])
    start = time.time()
    calc_drill(img_dir, out_dir, margin)
    exec_sec = time.time() - start
    print (f"exec_sec: {exec_sec}")
    exit()