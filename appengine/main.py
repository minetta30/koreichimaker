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
ext_list = ['jpeg', 'png', 'bmp']
# Cloud FunctionsのAPIエンドポイント
api_url = f'https://asia-northeast1-{PROJECT_ID}.cloudfunctions.net/koreichi-maker-api'

# Google Cloudのデフォルト認証情報を取得
auth_req = google.auth.transport.requests.Request()
id_token = google.oauth2.id_token.fetch_id_token(auth_req, api_url)
# ヘッダーにBearerトークンを設定
headers = {
	'Authorization': f'Bearer {id_token}',
}

# カードリストを読み込む
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)
blobs = storage_client.list_blobs(bucket, prefix='yugioh')
suggestions = [x.name.replace('yugioh/', '').replace('.png', '') for x in blobs]
suggestions = [x for x in suggestions if x != '']

# 失敗時の画像
with open('./static/koreichi.png', 'rb') as image_file:
	# Base64にエンコード
	failed_image_string = base64.b64encode(image_file.read()).decode().replace("'", "")

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
				result = f'ファイルエラー: {extension} ファイルがありません。'
				return render_template("index.html", result=result, img_data=failed_image_string)
			
			f = request.files["file"]

			# 拡張子の確認
			filename = secure_filename(f.filename)
			extension = str.lower(filename.split('.')[-1]).replace('jpg', 'jpeg')
			if extension not in ext_list:
				result = f'ファイルエラー: {extension} ファイルには対応しておりません。対応形式: jpg, png, bmp'
				return render_template("index.html", result=result, img_data=failed_image_string)
			
			# アップロードされたファイルをいったん保存する
			filepath = tempfile.mkdtemp()+"/a.png"
			f.save(filepath)
			f.seek(0)
			image = f.read()
			
			# ファイルを'multipart/form-data'で送信するためのファイルディクショナリを作成
			files = {'file': (filepath, image, f'image/{extension}')}
			
			# POSTリクエストで画像を送信
			response = requests.post(api_url, files=files, headers=headers)

			# レスポンスのステータスコードをチェック
			if response.status_code == 200:
				# レスポンスのコンテンツ（画像データ）をバイトストリームとして取得
				image_data = io.BytesIO(response.content)
				# バイトストリームからPillowで画像を開く
				image = Image.open(image_data)
				result = '画像の加工に成功しました。'
			else:
				result = '画像の加工に失敗しました。'
				return render_template("index.html", result=result, img_data=failed_image_string)
		
		elif submit_button == '送信':
			# テキストデータの処理
			card_name = request.form['text']
			if card_name not in suggestions:
				result = f'カード名エラー: {card_name} には対応しておりません。'
				return render_template("index.html", result=result, img_data=failed_image_string)

			# ファイルを指定して読み込み
			file_path = f'yugioh/{card_name}.png'
			blob = bucket.blob(file_path)
			# ファイルの内容を読み込む
			image = blob.download_as_bytes()
			# ファイルを'multipart/form-data'で送信するためのファイルディクショナリを作成
			files = {'file': (file_path, image, 'image/png')}
			
			# POSTリクエストで画像を送信
			response = requests.post(api_url, files=files, headers=headers)

			# レスポンスのステータスコードをチェック
			if response.status_code == 200:
				# レスポンスのコンテンツ（画像データ）をバイトストリームとして取得
				image_data = io.BytesIO(response.content)
				# バイトストリームからPillowで画像を開く
				image = Image.open(image_data)
				result = '画像の加工に成功しました。'
			else:
				result = '画像の加工に失敗しました。'
				return render_template("index.html", result=result, img_data=failed_image_string)

		# base64でエンコード
		buffer = io.BytesIO()
		image.save(buffer, format="PNG")
		img_string = base64.b64encode(buffer.getvalue()).decode().replace("'", "")
		
		return render_template("index.html", result=result, img_data=img_string)
	
@app.route('/api/suggestions')
def get_suggestions():
	# カードリストを渡す
	return jsonify(suggestions)

if __name__ == "__main__":
	 app.run(host="127.0.0.1", port=8080, debug=True)
