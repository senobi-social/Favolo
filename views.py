from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import TemplateView
from .forms import FavoloForm
from .forms import SignUpForm
from .forms import UserForm

# TwitterAPIの仕様に関するimport
import json
import re
from requests_oauthlib import OAuth1Session

#MySQLの接続に関するimport
import MySQLdb

# パスワードのハッシュ化に関するimport
import hashlib

# index.html　で使用
# mainクラス
class FavoloView(TemplateView):

    def __init__(self):
        self.params = {
            'title': 'Favolo',
            'form': FavoloForm()
        }
    
    def get(self, request):
        return render(request, 'favolo/index.html', self.params)


# signup.htmlで使用
# redirectは転送先URLを指定する
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('favolo:profile')
    else:
        form = SignUpForm()

    context = {'form':form}
    return render(request, 'favolo/signup.html', context)

# profile.htmlで使用
# signup.htmlの情報を確認する
# ユーザーの基本情報を入力させる
def profile(request):
    email = request.POST.get('email')

    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            # form.save()

            # パスワードのハッシュ化
            s = 'seisei'
            encoded_pass = s.encode()
            hash_pass = hashlib.sha256(encoded_pass).hexdigest()

            # データベースへの接続
            connection = MySQLdb.connect(
                host='localhost',
                user='bluesky',
                passwd='bluesky',
                db='favolo_db',
                charset="utf8"
            )

            # カーソルの取得
            cursor = connection.cursor()

            username = request.POST.get('username')
            account = request.POST.get('account')
            password = request.POST.get('password')

            # クエリのセット
            sql = "INSERT INTO favolo_members (user_id ,name ,mail ,password ,account) \
                values(UUID_TO_BIN(UUID()) ,username ,email ,hash_pass ,account);"

            # クエリの実行
            cursor.execute(sql)
        
            # 接続を終了する
            cursor.close()
            connection.close()

            return redirect('favolo:form')
        
    else:
        form = UserForm()
            
    params = {
        'title': '確認ページ',
        'form': UserForm(),
        'email': email,
    }
    return render(request, 'favolo/profile.html', params)


# database.html　で使用
def database(request):

    # データベースへの接続
    connection = MySQLdb.connect(
    host='localhost',
    user='bluesky',
    passwd='bluesky',
    db='favolo_db',
    charset="utf8"
    )

    # カーソルの取得
    cursor = connection.cursor()

    # クエリの実行
    sql = "select * from favolo_pages"
    cursor.execute(sql)

    # 実行結果を取得する
    rows = cursor.fetchall()

    # 接続を終了する
    cursor.close()
    connection.close()

    params = {
        'title': 'Favolo',
        'rows': rows,
    }
    return render(request, 'favolo/database.html', params)

# result.html で使用
# mainクラス
# 結果を表示するメソッド
def result(request):
    # リクエストパラメータを取得
    username = request.POST['username']
    account = request.POST['account']

    # TwitterのAPI仕様部分
    CONSUMER_KEY = 'erBtan8n2XL6epdGj0FGBuC48'
    CONSUMER_SECRET = 'jakIESg0xMvMkI3xZkEf4zxXBd1HlMcCRTZu3SuEj7bNAXbTrQ'
    ACCESS_TOKEN = '1224321904216956930-7cTpzTD85LGNc0MR1CAzWRPMQDITlR'
    ACCESS_TOKEN_SECRET = 'MqmvP7KjhR77aNhhvBZrtrLfHVZjSwFaRJz4dvnOuL72y'
    twitter = OAuth1Session(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    # 複数の返り値はタプルとして返される
    # res = twitter.get(url, params= params)
    # loads = json.loads(res.text)
    result = get_fav_list(request, twitter)
    res = result[0]
    loads = result[1]

    # リターン用のリストを用意
    textList = []
    imageList = []
    idList = []

    # 繰り返し部分はmainメソッドでする
    # それ以外の取得処理は他メソッドでする
    for num in range(10):
        load = loads[num]
        # テキスト取得部分
        text = get_text(res, load, num)
        # テキストのリスト
        textList.append(text)

        # 画像or動画取得部分
        # 画像１つの場合-１つだけのURL
        # 画像複数の場合-URLのリスト
        # 動画１つの場合-１つだけのURL
        types = photo_or_video(res, load, num)
        type = types[0]
        id = types[1]

        # イメージリストに格納
        imageList.append(type) 
        idList.append(id)
            
    # zip関数でまとめる
    List = zip(textList, imageList, idList)

    params = {
        'title': 'Favolo',
        'message': 'Name:' + username + '<br>ID:' + account,
        'username': username,
        'account': account,
        'textList': textList,
        'imageList': imageList,
        'idList': idList,
        'list': List,
    }
    return render(request, 'favolo/result.html', params) #第２引数には使うテンプレートを指定

# get_fav_list()
# ユーザー名からいいねリストを取得
# 返り値：resとjson
def get_fav_list(request, twitter):
    url = 'https://api.twitter.com/1.1/favorites/list.json?tweet_mode=extended'
    name = request.POST['account']
    params = {'screen_name': name, 'count': 15}
    res = twitter.get(url, params = params)

    if res.status_code == 200:
        load = json.loads(res.text)
        return res, load
    
    return res, false

# photo_or_video()
# ツイートが画像もしくは動画をもつか評価する
# 持つ場合、画像か動画化を判別する
# id = 1 は画像
# id = 2 は動画
# id = 3 はどちらでもない
def photo_or_video(res, load, num):

    # 画像か動画がある場合
    if 'extended_entities' in load:
        media = load['extended_entities']['media']
        type = media[0]['type']
        # 動画だったときの処理
        if type == "video":
            # get_videoメソッドを呼び起こす
            id = 2
            video = get_video(res,load, num)
            return video, id
        # 画像だったときの処理
        else:
            # get_imageメソッドを呼び起こす
            id = 1
            photo = get_image(res, load, num)
            return photo, id
    # 画像も動画もなかった場合
    else:
        id = 3
        str = "動画も画像もありません"
        return str, id

# get_image()
# resとjsonから画像を取得する
# 最後のnumは取得ツイートの特定
def get_image(res, load, num):
    # 画像がある場合
    if 'extended_entities' in load:
        medias = load['extended_entities']['media']
        return [m['media_url_https'] for m in medias]
    # 画像がない場合
    else:
        error = "画像はありません"
        return error

# get_video()
# resとjsonから動画を取得する
# 最後のnumは取得ツイートの特定
def get_video(res, load, num):
     # 動画がある場合
    if 'extended_entities' in load:
        # 投稿動画を取得する
        media = load['extended_entities']['media']
        video_info = media[0]['video_info']
        variants = video_info['variants']
        location = variants[0]
        url = location['url']
        return url
    # 動画がない場合
    else:
        error = "動画はありません"
        return error

# get_text()
# resとjsonからテキストを取得する
# 最後のnumは取得ツイートの特定
def get_text(res, load, num):
    text = load['full_text']
    # テキストクレイジング
    first = re.sub(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-…]+', "" ,text)
    second = re.sub(r'#.*', "" ,first)
    return second 

