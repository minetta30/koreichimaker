import functions_framework
from google.cloud import storage
import os
# Flask関連
from flask import abort, send_file
from PIL import Image, ImageOps
import io

# 環境変数からGCPプロジェクトIDとバケット名を取得
PROJECT_ID = os.environ.get('PROJECT_ID')
BUCKET_NAME = os.environ.get('BUCKET_NAME')

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
def koreichi_http(request):
	# カード名をHTTPリクエストから取得
	request_json = request.get_json(silent=True)
	if request_json and 'card_name' in request_json:
		card_name = request_json['card_name']
	else:
		return abort(400, 'The request must contain "card_name".')
	
	# Storageクライアントを初期化
	storage_client = storage.Client(PROJECT_ID)
	bucket = storage_client.get_bucket(BUCKET_NAME)

	# ファイルを指定して読み込み
	blob = bucket.blob(f'yugioh/{card_name}.png')
	
	# ファイルの内容を読み込む
	file_contents = blob.download_as_bytes()
	image = Image.open(io.BytesIO(file_contents))

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
