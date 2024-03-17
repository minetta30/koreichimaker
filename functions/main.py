import functions_framework
from google.cloud import storage
import os
# Flask関連
from flask import send_file
from PIL import Image, ImageOps
import io

# 環境変数からGCPプロジェクトIDを取得
PROJECT_ID = os.environ.get('PROJECT_ID')

def set_koreichi(image):
	# 左側のトリミング
	width, height = image.size
	image = image.crop((width*0.05, 0, width, height))

	# リサイズ
	card_size = (120, 191)
	image = image.resize(card_size)
	
	# 背景画像読み込み
	base_image = Image.open('./images/koreichi.png')
	_, _, _, mask = Image.open('./images/finger.png').split()
	mask = ImageOps.invert(mask)

	# 画像を重ね合わせる
	position = (2, 317)
	base_image.paste(image, position, mask)
	
	return base_image

@functions_framework.http
def koreichi_maker_http(request):
	# リクエストがPOSTでない場合はエラーを返す
	if request.method != 'POST':
		return 'Only POST requests are accepted', 405

	# リクエストから画像ファイルを取得
	file = request.files['file']
	if not file:
		return 'No file provided', 400
	
	# 画像ファイルを読み込む
	image = Image.open(file.stream)

	# 画像処理部分
	image = set_koreichi(image)

	# Pillowイメージをバイト配列に変換
	img_byte_arr = io.BytesIO()
	image.save(img_byte_arr, format='PNG')
	img_byte_arr = img_byte_arr.getvalue()

	# 画像データをHTTPレスポンスとして返す
	response = send_file(
		io.BytesIO(img_byte_arr),
		mimetype='image/png',
		as_attachment=True,
		download_name='card_image.png'
	)
	response.status_code = 200

	return response
