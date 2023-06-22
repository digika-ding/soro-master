from random import randint,seed
from PIL import Image,ImageDraw,ImageFont
from os import makedirs
output_dir = './question/'
makedirs(output_dir, exist_ok=True)
seed(1234) # 結果を再現できるようにするために乱数のシードを固定
blocksize = (400,240)
font = ImageFont.truetype("DejaVuSansMono.ttf", 30)
for i in range(5): # 問題を5枚作成する
    im = Image.new('L', (blocksize[0]*2,blocksize[1]*5),(255))
    d = ImageDraw.Draw(im)
    q_num = 0
    for r in range(5):
        for c in range(2):
            q_num += 1;q_num_text = '(' + str(q_num) + ')'
            d.text((c*blocksize[0],r*blocksize[1]), q_num_text, font=font, fill=(0))# 問題番号記入
            # 問題作成
            x,y = randint(1,9999),randint(1,9999)
            operator = '+' if randint(0,1) == 0 else '-'
            if operator=='-' and x < y:
                x,y = y,x
            x = str(x).rjust(5);y = str(y).rjust(5)
            d.text((c*blocksize[0]+200, r*blocksize[1]+50), x, font=font, fill=(0))# 上の数字
            d.text((c*blocksize[0]+200, r*blocksize[1]+90), y, font=font, fill=(0))# 下の数字
            d.text((c*blocksize[0]+100, r*blocksize[1]+90), operator, font=font, fill=(0))# 演算子
            d.line((c*blocksize[0]+100, r*blocksize[1]+124, c*blocksize[0]+300, r*blocksize[1]+124), fill=(0),width=1)# 線を描く
    file_path = output_dir + str(i).zfill(5) + '.png'
    im.save(file_path)
