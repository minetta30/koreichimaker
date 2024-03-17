# 必要なモジュールを読み込む
# Flask関連
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import requests
import base64
import tempfile
from PIL import Image, ImageOps
import io
import os
import google.oauth2.id_token
import google.auth.transport.requests
from google.cloud import storage

app = Flask(__name__)

PROJECT_ID = os.environ.get('PROJECT_ID')
BUCKET_NAME = os.environ.get('BUCKET_NAME')

# 対応している拡張子
ext_list = ['jpg', 'jpeg', 'png', 'bmp']
# Cloud FunctionsのAPIエンドポイント
api_url = f'https://asia-northeast1-{PROJECT_ID}.cloudfunctions.net/koreichi-card-api'

# Google Cloudのデフォルト認証情報を取得
auth_req = google.auth.transport.requests.Request()
id_token = google.oauth2.id_token.fetch_id_token(auth_req, api_url)
# ヘッダーにBearerトークンを設定
headers = {
	'Authorization': f'Bearer {id_token}',
	'Content-Type': 'application/json'
}

# カードリストを読み込む
client = storage.Client()
bucket = client.bucket(BUCKET_NAME)
blobs = client.list_blobs(bucket, prefix='yugioh')
suggestions = [x.name.replace('yugioh/', '').replace('.png', '') for x in blobs]

def set_koreichi(image):
	# 左側のトリミング
	width, height = image.size
	image = image.crop((width*0.05, 0, width, height))

	# リサイズ
	card_size = (120, 191)
	image = image.resize(card_size)
	
	# 背景画像読み込み
	base_image = Image.open('./static/koreichi.png')
	_, _, _, mask = Image.open('./static/finger.png').split()
	mask = ImageOps.invert(mask)

	# 画像を重ね合わせる
	position = (2, 317)
	base_image.paste(image, position, mask)
	
	return base_image

@app.route("/", methods=["GET", "POST"])
def upload_file():
	if request.method == "GET":
		return render_template("index.html")
	if request.method == "POST":
		# try:
		submit_button = request.form.get('submit_button')
		if submit_button == 'アップロード':
			# ファイルアップロードの処理
			if 'file' not in request.files:
				return jsonify({'error': 'ファイルがありません'}), 400
			# アップロードされたファイルをいったん保存する
			f = request.files["file"]
			filepath = tempfile.mkdtemp()+"/a.png"
			filename = secure_filename(f.filename)
			extension = str.lower(filename.split('.')[-1])
			if extension in ext_list:
				f.save(filepath)
				image = Image.open(filepath)
				# 画像処理部分
				image = set_koreichi(image)
				# result = f"君達まとめて「{filename.split('.')[0]}」一枚で十分かな♧"
				result = '画像の加工に成功しました。'
			else:
				image = Image.open('./static/koreichi.png')
				result = f'申し訳ございませんが {extension} ファイルには対応しておりません。対応形式: jpg, png, bmp'
		
		elif submit_button == '送信':
			# テキストデータの処理
			card_name = request.form['text']
			
			# Cloud FunctionsのAPIにHTTP GETリクエストを送信
			json_data = {'card_name': f'{card_name}'}
			response = requests.post(api_url, json=json_data, headers=headers)

			# レスポンスのステータスコードをチェック
			if response.status_code == 200:
				# レスポンスのコンテンツ（画像データ）をバイトストリームとして取得
				image_data = io.BytesIO(response.content)
				# バイトストリームからPillowで画像を開く
				image = Image.open(image_data)

				# 画像処理部分
				# image = set_koreichi(image)
				result = '画像の加工に成功しました。'
			else:
				image = Image.open('./static/koreichi.png')
				result = '画像の加工に失敗しました。'

		# except:
		# 	image = Image.open('./static/koreichi.png')
		# 	result = '画像の加工に失敗しました。'
		# finally:
		# base64でエンコード
		buffer = io.BytesIO()
		image.save(buffer, format="PNG")
		img_string = base64.b64encode(buffer.getvalue()).decode().replace("'", "")
		
		return render_template("index.html", result=result, img_data=img_string)
	
@app.route('/api/suggestions')
def get_suggestions():
	# カードリストを渡す
	print(suggestions)
	return jsonify(suggestions)

if __name__ == "__main__":
	 app.run(host="127.0.0.1", port=8080, debug=True)
