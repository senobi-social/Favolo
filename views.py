from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http.response import JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import FavoloForm
from .forms import SignUpForm
from .forms import LoginForm
from .forms import SettingsUsernameForm
from .forms import SettingsPasswordForm
from .forms import SettingsDesignForm
from .forms import SettingsIntroductionForm

# TwitterAPIの仕様に関するimport
import json
import re
from requests_oauthlib import OAuth1Session

#MySQLの接続に関するimport
import MySQLdb

# パスワードのハッシュ化に関するimport
import hashlib

# アクセスキー生成に関するインポート
import random, string

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

# サインイン機能
# signup.htmlで使用
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            save = form.save()
            username = save[0]
            account = save[1]
            password = save[2]
            email = request.POST.get('email')

            # パスワードのハッシュ化
            encoded_pass = password.encode()
            hash_pass = hashlib.sha256(encoded_pass).hexdigest()

            # アクセスキーの取得
            accesskey = Create_Accesskey(request)

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

            # クエリのセット
            sql_members_insert = "INSERT INTO favolo_members (user_id, name, mail, password, account) \
                values(UUID_TO_BIN(UUID()), %s, %s, %s, %s);"

            sql_members_select = "SELECT BIN_TO_UUID(user_id) FROM favolo_members where mail=%s;"

            sql_pages_insert = "INSERT INTO favolo_pages (page_id ,user_id ,accesskey ,design ,title ,comment) \
                values(UUID_TO_BIN(UUID()), UUID_TO_BIN(%s), %s, 1, 'Favoにタイトルをつけてみよう！', 'コメントで紹介しよう！');"
	
            # クエリの実行
            cursor.execute(sql_members_insert, (username, email, hash_pass, account))
            cursor.execute(sql_members_select, (email,))

            row = cursor.fetchone()
            user_id = row[0]

            cursor.execute(sql_pages_insert, (user_id, accesskey, ))
        
            # 接続を終了する
            cursor.close()
            connection.commit()
            connection.close()            

            # セッションでユーザー情報を保存
            request.session['username'] = username
            request.session['account'] = account
            request.session['email'] = email
            return redirect('favolo:profile')
    else:
        form = SignUpForm()

    params = {
        'form':form,
        }
    return render(request, 'favolo/signup.html', params)

# アクセスキーを作成する昨日
# signup.htmlで使用する
def Create_Accesskey(request):
    Alpha1 = ''.join(random.choices(string.ascii_letters, k=4))
    Alpha2 = ''.join(random.choices(string.ascii_letters, k=4))
    Nume1 = ''.join(random.choices(string.digits, k=4))
    Nume2 = ''.join(random.choices(string.digits, k=4))

    version = '1.0'
    removed = version.replace(".", "")

    accesskey = removed + Alpha1 + Nume1 + Alpha2 + Nume2
    return accesskey

# サインインの確認機能
# profile.htmlで使用
def profile(request):
    # セッションからユーザー情報を取得
    username = request.session.get('username')
    account = request.session.get('account')
    email = request.session.get('email')
            
    params = {
        'title': '確認ページ',
        'username': username,
        'account': account,
        'email': email,
    }
    return render(request, 'favolo/profile.html', params)

# ログイン機能
# login.htmlで使用
def account_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = request.POST.get('email')
            password = request.POST.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:

                # favolo_membersからユーザー情報を取得する
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

                # クエリのセット
                sql_members_select = "SELECT BIN_TO_UUID(user_id), name, account FROM favolo_members where mail=%s;"

                sql_pages_select = "SELECT title, comment FROM favolo_pages where user_id=UUID_TO_BIN(%s);"
    
                # クエリの実行
                cursor.execute(sql_members_select, (email,))

                # ユーザー情報の取得
                row_members = cursor.fetchone()
                user_id = row_members[0]
                username = row_members[1]
                account = row_members[2]

                cursor.execute(sql_pages_select, (user_id,))

                # ページ情報の取得
                row_pages = cursor.fetchone()
                page_title = row_pages[0]
                page_comment = row_pages[1]

                # ユーザー情報をセッションに保存
                request.session['username'] = username
                request.session['account'] = account
                request.session['email'] = email

                # ページ情報をセッションに保存
                request.session['page_title'] = page_title
                request.session['page_comment'] = page_comment
      
                # 接続を終了する
                cursor.close()
                connection.commit()
                connection.close()

                # ログインする
                login(request, user)                      

                # ログイン成功ページへリダイレクト
                return redirect('favolo:result')
            else:
                # ログイン失敗時の処理
                return 'メールアドレスまたはパスワードが違います' 
    else:
        form = LoginForm()

    params = {
        'title': 'ログインページ',
        'form':form,
    }
    return render(request, 'favolo/login.html', params)

# ログアウト機能
# logout.htmlで使用
def account_logout(request):
    logout(request)
    return redirect('favolo:login')


# result.html で使用
# 結果を表示するメソッド
@login_required
def result(request):

    # セッションからユーザー情報を取得
    username = request.session.get('username')
    account = request.session.get('account')
    email = request.session.get('email')

    # セッションからページ情報を取得
    page_title = request.session.get('page_title')
    page_comment = request.session.get('page_comment')

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

    # クエリのセット

    sql_members_select = "SELECT BIN_TO_UUID(user_id) FROM favolo_members where mail=%s;"

    sql_pages_select = "SELECT BIN_TO_UUID(page_id), accesskey FROM favolo_pages where user_id =UUID_TO_BIN(%s);"

    sql_buzz_select = "SELECT likes FROM favolo_buzz where page_id=UUID_TO_BIN(%s);"  

    # クエリの実行
    cursor.execute(sql_members_select, (email, ))

    # ユーザー情報の取得
    row_members = cursor.fetchone()
    user_id = row_members[0]

    cursor.execute(sql_pages_select, (user_id,))

    # ページ情報の取得
    row_pages = cursor.fetchone()
    page_id = row_pages[0]
    accesskey = row_pages[1]

    cursor.execute(sql_buzz_select, (page_id, ))

    # いいね情報の取得
    row_buzz = cursor.fetchone()
    likes = row_buzz[0]

    # 接続を終了する
    cursor.close()
    connection.commit()
    connection.close()

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
    for num in range(16):
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
        'page_accesskey': accesskey,
        'page_title': page_title,
        'page_comment': page_comment,
        'page_name': username,
        'page_likes': likes,
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
    name = request.session.get('account')
    params = {'screen_name': name, 'count': 16}
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



# settingsの設定ページ
@login_required
def settings(request):

    params = {
        'title': '設定画面',
    }
    return render(request, 'favolo/settings.html', params)


# usernameの変更機能
# settings/username.htmlで使用
@login_required
def settings_username(request):
    email = request.session.get('email')
    if request.method == 'POST':
        form = SettingsUsernameForm(request.POST)
        if form.is_valid():
            new_username = request.POST.get('new_username')

            # favolo_membersからユーザー情報を取得する
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

            # クエリのセット
            sql_members_update = "UPDATE favolo_members SET name=%s where mail=%s;"
    
            # クエリの実行
            cursor.execute(sql_members_update, (new_username, email,))

            # 接続を終了する
            cursor.close()
            connection.commit()
            connection.close()

            # ユーザー情報の更新
            request.session['username'] = new_username

            return redirect('favolo:result')   
    else:
        form = SettingsUsernameForm()

    params = {
        'title': 'ユーザーネームの変更',
        'form': form,
        'email': email,
    }
    return render(request, 'favolo/settings/username.html', params)


# passwordの変更機能
# settings/password.htmlで使用
@login_required
def settings_password(request):
    if request.method == 'POST':
        form = SettingsPasswordForm(request.POST)
        if form.is_valid():
            save = form.save()
            new_password = save[0]
            email = save[1]

            # パスワードのハッシュ化
            encoded_pass = new_password.encode()
            hash_pass = hashlib.sha256(encoded_pass).hexdigest()

            # favolo_membersからユーザー情報を取得する
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

            # クエリのセット
            sql_members_update = "UPDATE favolo_members SET password=%s where mail=%s"
    
            # クエリの実行
            cursor.execute(sql_members_update, (hash_pass, email,))

            # 接続を終了する
            cursor.close()
            connection.commit()
            connection.close()

            return redirect('favolo:result')
    else:
        form = SettingsPasswordForm()

    params = {
        'title': 'パスワードの変更',
        'form': form,
    }
    return render(request, 'favolo/settings/password.html', params)


# designの変更機能
# settings/design.htmlで使用
@login_required
def settings_design(request):
    if request.method == 'POST':
        form = SettingsDesignForm(request.POST)
        if form.is_valid():
            new_design = request.POST.get('new_design')
            email = request.session.get('email')

            # favolo_membersからユーザー情報を取得する
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

            # クエリのセット
            sql_members_select = "SELECT BIN_TO_UUID(user_id) FROM favolo_members where mail=%s;"

            sql_pages_update = "UPDATE favolo_pages SET design=%s where user_id=UUID_TO_BIN(%s);"
    
            # クエリの実行
            cursor.execute(sql_members_select, (email,))

            # ユーザーIDの取得
            row_members = cursor.fetchone()
            user_id = row_members[0]

            cursor.execute(sql_pages_update, (new_design, user_id,))

            # 接続を終了する
            cursor.close()
            connection.commit()
            connection.close()

            # ページ情報の更新
            request.session['page_design'] = new_design

            return redirect('favolo:result')
    else:
        form = SettingsDesignForm()

    params = {
        'title': 'デザインの変更',
        'form': form,
    }
    return render(request, 'favolo/settings/design.html', params)


# title, commentの変更機能
# settings/introduction.htmlで使用
@login_required
def settings_introduction(request):
    if request.method == 'POST':
        form = SettingsIntroductionForm(request.POST)
        if form.is_valid():
            new_title = request.POST.get('new_title')
            new_comment = request.POST.get('new_comment')
            email = request.session.get('email')

            # favolo_membersからユーザー情報を取得する
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

            # クエリのセット
            sql_members_select = "SELECT BIN_TO_UUID(user_id) FROM favolo_members where mail=%s;"

            sql_pages_update = "UPDATE favolo_pages SET title=%s, comment=%s where user_id=UUID_TO_BIN(%s);"
    
            # クエリの実行
            cursor.execute(sql_members_select, (email,))

            # ユーザーIDの取得
            row_members = cursor.fetchone()
            user_id = row_members[0]

            cursor.execute(sql_pages_update, (new_title, new_comment, user_id,))

            # 接続を終了する
            cursor.close()
            connection.commit()
            connection.close()

            # ページ情報をセッションに保存
            request.session['page_title'] = new_title
            request.session['page_comment'] = new_comment

            return redirect('favolo:result')
    else:
        # セッションからページ情報を取得
        page_title = request.session.get('page_title')
        page_comment = request.session.get('page_comment')

        # フォームに初期値をつける
        initial_dict = dict(new_title=page_title, new_comment=page_comment)
        form = SettingsIntroductionForm(initial = initial_dict)

    params = {
        'title': 'タイトル/コメントの変更',
        'form': form,
    }
    return render(request, 'favolo/settings/introduction.html', params)

@login_required
def pages(request, accesskey):

    # セッションからユーザー情報を取得
    username = request.session.get('username')
    account = request.session.get('account')

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

    # クエリのセット
    sql_pages_select = "SELECT BIN_TO_UUID(user_id), BIN_TO_UUID(page_id), design, title, comment FROM favolo_pages where accesskey=%s;"

    sql_members_select = "SELECT name, account FROM favolo_members where user_id=UUID_TO_BIN(%s);"

    sql_buzz_select = "SELECT likes FROM favolo_buzz where page_id=UUID_TO_BIN(%s);"

    # クエリの実行
    cursor.execute(sql_pages_select, (accesskey,))

    # ページ情報の取得
    row_pages = cursor.fetchone()
    user_id = row_pages[0]
    page_id = row_pages[1]
    design = row_pages[2]
    title = row_pages[3]
    comment = row_pages[4]

    cursor.execute(sql_members_select, (user_id, ))

    # ユーザー情報の取得
    row_members = cursor.fetchone()
    name = row_members[0]
    page_account = row_members[1]

    cursor.execute(sql_buzz_select, (page_id, ))

    # いいね情報の取得
    row_buzz = cursor.fetchone()
    likes = row_buzz[0]

    # 接続を終了する
    cursor.close()
    connection.commit()
    connection.close()


    # TwitterのAPI仕様部分
    CONSUMER_KEY = 'erBtan8n2XL6epdGj0FGBuC48'
    CONSUMER_SECRET = 'jakIESg0xMvMkI3xZkEf4zxXBd1HlMcCRTZu3SuEj7bNAXbTrQ'
    ACCESS_TOKEN = '1224321904216956930-7cTpzTD85LGNc0MR1CAzWRPMQDITlR'
    ACCESS_TOKEN_SECRET = 'MqmvP7KjhR77aNhhvBZrtrLfHVZjSwFaRJz4dvnOuL72y'
    twitter = OAuth1Session(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    # 複数の返り値はタプルとして返される
    # res = twitter.get(url, params= params)
    # loads = json.loads(res.text)
    result = get_other_fav_list(request, twitter, page_account)
    res = result[0]
    loads = result[1]

    # リターン用のリストを用意
    textList = []
    imageList = []
    idList = []

    # 繰り返し部分はmainメソッドでする
    # それ以外の取得処理は他メソッドでする
    for num in range(16):
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

    # 注意
    # サイドバーに表示させるusernameと
    # ページ所有者のnameは別物
    params = {
        'title': 'Favolo',
        'username': username,
        'account': account,
        'page_accesskey': accesskey,
        'page_name': name,
        'page_account': page_account,
        'page_design': design,
        'page_title': title,
        'page_comment': comment,
        'page_likes': likes,
        'textList': textList,
        'imageList': imageList,
        'idList': idList,
        'list': List,
    }
    return render(request, 'favolo/result.html', params)

# get_fav_list()
# ユーザー名からいいねリストを取得
# 返り値：resとjson
def get_other_fav_list(request, twitter, account):
    url = 'https://api.twitter.com/1.1/favorites/list.json?tweet_mode=extended'
    params = {'screen_name': account, 'count': 16}
    res = twitter.get(url, params = params)

    if res.status_code == 200:
        load = json.loads(res.text)
        return res, load
    
    return res, false

# settingsの設定ページ
@login_required
def all_pages(request):

    params = {
        'title': '全てのFavolo一覧',
    }
    return render(request, 'favolo/all.html', params)

@login_required
def likes(request, accesskey):

    # セッションからユーザー情報を取得
    username = request.session.get('username')
    email = request.session.get('email')

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

    # クエリのセット
    sql_pages_select = "SELECT BIN_TO_UUID(page_id) FROM favolo_pages where accesskey=%s;"

    sql_members_select = "SELECT BIN_TO_UUID(user_id) FROM favolo_members where mail=%s;"

    sql_buzz_update = "UPDATE favolo_buzz SET likes = likes + 1 where page_id=UUID_TO_BIN(%s);"  

    sql_likes_insert = "INSERT into favolo_likes (user_id, page_id) values(UUID_TO_BIN(%s), UUID_TO_BIN(%s));"


    # クエリの実行
    cursor.execute(sql_pages_select, (accesskey, ))

    # ページ情報の取得
    row_pages = cursor.fetchone()
    page_id = row_pages[0]

    cursor.execute(sql_members_select, (email,))

    # ユーザー情報の取得
    row_members = cursor.fetchone()
    user_id = row_members[0]

    cursor.execute(sql_buzz_update, (page_id, ))

    cursor.execute(sql_likes_insert, (user_id, page_id))

    # 接続を終了する
    cursor.close()
    connection.commit()
    connection.close() 

    return redirect('favolo:accesskey', accesskey)

@login_required
def api_likes(request, accesskey):

    # セッションからユーザー情報を取得
    username = request.session.get('username')
    email = request.session.get('email')

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

    # クエリのセット
    sql_pages_select = "SELECT BIN_TO_UUID(page_id) FROM favolo_pages where accesskey=%s;"

    sql_members_select = "SELECT BIN_TO_UUID(user_id) FROM favolo_members where mail=%s;"

    sql_buzz_update = "UPDATE favolo_buzz SET likes = likes + 1 where page_id=UUID_TO_BIN(%s);"  

    sql_likes_insert = "INSERT into favolo_likes (user_id, page_id) values(UUID_TO_BIN(%s), UUID_TO_BIN(%s));"

    sql_buzz_select = "SELECT likes FROM favolo_buzz where page_id=UUID_TO_BIN(%s);"


    # クエリの実行
    cursor.execute(sql_pages_select, (accesskey, ))

    # ページ情報の取得
    row_pages = cursor.fetchone()
    page_id = row_pages[0]

    cursor.execute(sql_members_select, (email,))

    # ユーザー情報の取得
    row_members = cursor.fetchone()
    user_id = row_members[0]

    cursor.execute(sql_buzz_update, (page_id, ))

    cursor.execute(sql_likes_insert, (user_id, page_id))

    # いいね情報の取得
    cursor.execute(sql_buzz_select, (page_id, ))
    row_buzz = cursor.fetchone()
    likes = row_buzz[0]

    # 接続を終了する
    cursor.close()
    connection.commit()
    connection.close() 

    return JsonResponse({"likes":likes})


