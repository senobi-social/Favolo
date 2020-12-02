from django.shortcuts import render, redirect
from django.http import HttpResponse
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
from .forms import SettingsTagsForm

# TwitterAPIの仕様に関するimport
import json
import re
from requests_oauthlib import OAuth1Session

#MySQLの接続に関するimport
import MySQLdb

# パスワードのハッシュ化に関するimport
import hashlib

# アクセスキー生成に関するimport
import random, string

# Ajax、JSONに関するimport
from django.http.response import JsonResponse
from django.template.loader import render_to_string

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

            sql_pages_select = "SELECT BIN_TO_UUID(page_id) FROM favolo_pages where user_id=UUID_TO_BIN(%s);"

            sql_buzz_insert = "INSERT INTO favolo_buzz (page_id, likes) values(UUID_TO_BIN(%s), default);"

            sql_count_insert = "INSERT INTO favolo_follow_count (user_id, follow, followed) values(UUID_TO_BIN(%s), default, default);"
	
            # クエリの実行

            # メンバーに追加
            cursor.execute(sql_members_insert, (username, email, hash_pass, account))

            # user_idを取得
            cursor.execute(sql_members_select, (email,))
            row_members = cursor.fetchone()
            user_id = row_members[0]

            # ページに追加
            cursor.execute(sql_pages_insert, (user_id, accesskey, ))

            # page_idを取得
            cursor.execute(sql_pages_select, (user_id,))
            row_pages = cursor.fetchone()
            page_id = row_pages[0]

            # buzzに追加
            cursor.execute(sql_buzz_insert, (page_id, ))

            # follow_countに追加
            cursor.execute(sql_count_insert, (user_id, ))
        
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
        'title': 'Favolo',
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
        'title': 'Favolo',
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

    sql_tags_select = "SELECT BIN_TO_UUID(tag_id) FROM favolo_tags_map where page_id=UUID_TO_BIN(%s);"

    sql_tagname_select = "SELECT name FROM favolo_tags_master where tag_id=UUID_TO_BIN(%s);"

    sql_followcount_select = "SELECT follow, followed FROM favolo_follow_count where user_id=UUID_TO_BIN(%s);"

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

    # タグ情報の取得
    cursor.execute(sql_tags_select, (page_id, ))
    row_tags = cursor.fetchone()

    # フォロー情報の取得
    cursor.execute(sql_followcount_select, (user_id, ))
    row_follow = cursor.fetchone()
    login_user_follow = row_follow[0]
    login_user_followed = row_follow[1]

    if row_tags == None:
        # タグが設定されていない場合の処理
        tag_name = None
    else:
        # タグが設定されている場合の処理
        tag_id = row_tags[0]
        cursor.execute(sql_tagname_select, (tag_id, ))
        row_tagname = cursor.fetchone()
        tag_name = row_tagname[0]

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
    for num in range(18):
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

    # プロフィール画像の取得
    profile_image = get_profile_image(request, twitter)
    request.session['page_profile_image'] = profile_image

    # いいねの状態を把握する
    liked = liked_status(request, accesskey)
    # いいねの状態をセッションに保存(一時的)
    request.session['page_liked_status'] = liked

    # フォローの状態を把握する
    status = followed_status(request, accesskey)
    followed_status_code = status[0]
    followed = status[1]
    # フォローの状態をセッションに保存（一時的）
    request.session['page_followed_status'] = followed


    params = {
        'title': 'Favolo',
        'page_accesskey': accesskey,
        'page_title': page_title,
        'page_comment': page_comment,
        'page_name': username,
        'page_profile_image': profile_image,
        'page_likes': likes,
        'page_liked_status': liked,
        'page_followed_status': followed,
        'page_followed_status': followed_status_code,
        'page_tag_name': tag_name,
        'username': username,
        'account': account,
        'follow': login_user_follow,
        'followed': login_user_followed,
        'textList': textList,
        'imageList': imageList,
        'idList': idList,
        'list': List,
    }
    return render(request, 'favolo/result.html', params) #第２引数には使うテンプレートを指定


# get_profile_image()
# ユーザー名からプロフィール画像を取得
def get_profile_image(request, twitter):
    url = 'https://api.twitter.com/1.1/users/show.json'
    name = request.session.get('account')
    params = {'screen_name': name, }
    res = twitter.get(url, params = params)

    if res.status_code == 200:
        load = json.loads(res.text)
        if 'profile_image_url_https' in load:
            profile_image = load['profile_image_url_https']
            return profile_image
    str = "画像がありません"
    return str



# get_fav_list()
# ユーザー名からいいねリストを取得
# 返り値：resとjson
def get_fav_list(request, twitter):
    url = 'https://api.twitter.com/1.1/favorites/list.json?tweet_mode=extended'
    name = request.session.get('account')
    params = {'screen_name': name, 'count': 21}
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
    username = request.session.get('username')
    account = request.session.get('account')
    page_profile_image = request.session.get('page_profile_image')


    params = {
        'title': 'Favolo',
        'username': username,
        'account': account,
        'page_profile_image': page_profile_image,
    }
    return render(request, 'favolo/settings.html', params)


# usernameの変更機能
# settings/username.htmlで使用
@login_required
def settings_username(request):

    # ユーザー情報の取得
    email = request.session.get('email')
    username = request.session.get('username')
    account = request.session.get('account')
    profile_image = request.session.get('page_profile_image')

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
        'title': 'Favolo',
        'form': form,
        'email': email,
        'username': username,
        'account': account,
        'page_profile_image': profile_image,
    }
    return render(request, 'favolo/settings/username.html', params)


# passwordの変更機能
# settings/password.htmlで使用
@login_required
def settings_password(request):

    # ユーザー情報の取得
    email = request.session.get('email')
    username = request.session.get('username')
    account = request.session.get('account')
    profile_image = request.session.get('page_profile_image')

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
        'title': 'Favolo',
        'username': username,
        'account': account,
        'page_profile_image': profile_image,
        'form': form,
    }
    return render(request, 'favolo/settings/password.html', params)


# designの変更機能
# settings/design.htmlで使用
@login_required
def settings_design(request):

    # ユーザー情報の取得
    email = request.session.get('email')
    username = request.session.get('username')
    account = request.session.get('account')
    profile_image = request.session.get('page_profile_image')

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
        'title': 'Favolo',
        'username': username,
        'account': account,
        'page_profile_image': profile_image,
        'form': form,
    }
    return render(request, 'favolo/settings/design.html', params)


# title, commentの変更機能
# settings/introduction.htmlで使用
@login_required
def settings_introduction(request):

    # ユーザー情報の取得
    email = request.session.get('email')
    username = request.session.get('username')
    account = request.session.get('account')
    profile_image = request.session.get('page_profile_image')
    
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
        'title': 'Favolo',
        'username': username,
        'account': account,
        'page_profile_image': profile_image,
        'form': form,
    }
    return render(request, 'favolo/settings/introduction.html', params)

# タグの変更機能
# settings/tags.htmlで使用
@login_required
def settings_tags(request):

    # ユーザー情報の取得
    email = request.session.get('email')
    username = request.session.get('username')
    account = request.session.get('account')
    profile_image = request.session.get('page_profile_image')

    if request.method == 'POST':
        form = SettingsTagsForm(request.POST)
        if form.is_valid():
            tags = request.POST.getlist('new_tags') # リストで返ってくる
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
            sql_members_select = "SELECT BIN_TO_UUID(user_id) FROM favolo_members where mail=%s;"

            sql_pages_select = "SELECT BIN_TO_UUID(page_id) FROM favolo_pages where user_id=UUID_TO_BIN(%s);"

            sql_tags_delete = "DELETE from favolo_tags_map where page_id=UUID_TO_BIN(%s);"

            sql_tags_select = "SELECT BIN_TO_UUID(tag_id) FROM favolo_tags_master where master_id=%s;"

            sql_tags_insert = "INSERT INTO favolo_tags_map (tag_id, page_id) values (UUID_TO_BIN(%s), UUID_TO_BIN(%s));"
    
            # クエリの実行
            # ユーザーIDの取得
            cursor.execute(sql_members_select, (email, ))
            row_members = cursor.fetchone()
            user_id = row_members[0]

            # ページIDの取得
            cursor.execute(sql_pages_select, (user_id, ))
            row_pages = cursor.fetchone()
            page_id = row_pages[0]

            # 既存タグマップの削除
            cursor.execute(sql_tags_delete, (page_id, ))

            # 単一選択なのでfor文は回さない
            # 将来的に複数選択にする場合はfor文を使ってリストから取り出してください
            # タグIDの取得
            cursor.execute(sql_tags_select, (tags, ))
            row_tags = cursor.fetchone()
            tag_id = row_tags[0]

            # 新規タグマップの挿入
            # ページIDとタグIDを使用
            cursor.execute(sql_tags_insert, (tag_id, page_id))

            # 接続を終了する
            cursor.close()
            connection.commit()
            connection.close()
            
            request.session['tags'] = tags
            return redirect('favolo:result')
    else:
        form = SettingsTagsForm()

    params = {
        'title': 'Favolo',
        'username': username,
        'account': account,
        'page_profile_image': profile_image,
        'form': form,
    }
    return render(request, 'favolo/settings/tags.html', params)

@login_required
def pages(request, accesskey):

    # セッションからユーザー情報を取得
    username = request.session.get('username')
    account = request.session.get('account')
    profile_image = request.session.get('page_profile_image')
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
    sql_pages_select = "SELECT BIN_TO_UUID(user_id), BIN_TO_UUID(page_id), design, title, comment FROM favolo_pages where accesskey=%s;"

    sql_members_select = "SELECT name, account FROM favolo_members where user_id=UUID_TO_BIN(%s);"

    sql_buzz_select = "SELECT likes FROM favolo_buzz where page_id=UUID_TO_BIN(%s);"

    sql_tags_select = "SELECT BIN_TO_UUID(tag_id) FROM favolo_tags_map where page_id=UUID_TO_BIN(%s);"

    sql_tagname_select = "SELECT name FROM favolo_tags_master where tag_id=UUID_TO_BIN(%s);"

    sql_loginuser_select = "SELECT BIN_TO_UUID(user_id) FROM favolo_members where mail=%s;"

    sql_followcount_select = "SELECT follow, followed FROM favolo_follow_count where user_id=UUID_TO_BIN(%s);"

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

    # タグ情報の取得
    cursor.execute(sql_tags_select, (page_id, ))
    row_tags = cursor.fetchone()

    # フォロー情報の取得
    cursor.execute(sql_loginuser_select, (email,))
    row_loginuser = cursor.fetchone()
    login_user = row_loginuser[0]

    cursor.execute(sql_followcount_select, (login_user, ))
    row_follow = cursor.fetchone()
    login_user_follow = row_follow[0]
    login_user_followed = row_follow[1]

    if row_tags == None:
        # タグが設定されていない場合の処理
        tag_name = None
    else:
        # タグが設定されている場合の処理
        tag_id = row_tags[0]
        cursor.execute(sql_tagname_select, (tag_id, ))
        row_tagname = cursor.fetchone()
        tag_name = row_tagname[0]

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
    for num in range(21):
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

    # いいねの状態を把握する
    liked = liked_status(request, accesskey)
    # いいねの状態をセッションに保存(一時的)
    request.session['page_liked_status'] = liked

    # フォローの状態を把握する
    status = followed_status(request, accesskey)
    followed_status_code = status[0]
    followed = status[1]
    # フォローの状態をセッションに保存（一時的）
    request.session['page_followed_status'] = followed


    # 注意
    # サイドバーに表示させるusernameと
    # ページ所有者のnameは別物
    params = {
        'title': 'Favolo',
        'username': username,
        'account': account,
        'follow': login_user_follow,
        'followed': login_user_followed,
        'page_accesskey': accesskey,
        'page_name': name,
        'page_account': page_account,
        'page_profile_image': profile_image,
        'page_design': design,
        'page_title': title,
        'page_comment': comment,
        'page_likes': likes,
        'page_liked_status': liked,
        'page_followed_status': followed,
        'page_followed_status_code': followed_status_code,
        'page_tag_name': tag_name,
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
    params = {'screen_name': account, 'count': 21}
    res = twitter.get(url, params = params)

    if res.status_code == 200:
        load = json.loads(res.text)
        return res, load
    
    return res, false

# 記事一覧ページ
@login_required
def all_pages(request):

    # セッションからユーザー情報を取得
    username = request.session.get('username')
    account = request.session.get('account')
    profile_image = request.session.get('page_profile_image')

    params = {
        'title': 'Favolo',
        'username': username,
        'account': account,
        'page_profile_image': profile_image,
    }
    return render(request, 'favolo/all.html', params)

# ユーザーがページに対していいねしているか判別
# いいねの数の検索はresult, pagesで行っている
@login_required
def liked_status(request, accesskey):

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

    sql_likes_select = "SELECT COUNT(*) FROM favolo_likes where page_id = UUID_TO_BIN(%s) and user_id = UUID_TO_BIN(%s);"

    # クエリの実行
    #　ページ情報の取得
    cursor.execute(sql_pages_select, (accesskey, ))
    row_pages = cursor.fetchone()
    page_id = row_pages[0]

    # ユーザー情報の取得
    cursor.execute(sql_members_select, (email,))
    row_members = cursor.fetchone()
    user_id = row_members[0]

    # favolo_likesに存在するか（いいねされているか確認）
    cursor.execute(sql_likes_select, (page_id, user_id))
    row_likes = cursor.fetchone()
    likes = row_likes[0]

    # もしlikesが0より大きかったらTrue
    # likesが0だったらFalseを返す
    liked = False
    if likes > 0 :
        liked = True
    return liked

@login_required
def likes(request, accesskey):

    # セッションからユーザー情報を取得
    username = request.session.get('username')
    email = request.session.get('email')

    # セッションからいいねの状態を取得
    liked = request.session.get('page_liked_status')

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

    # 共通クエリのセット
    sql_pages_select = "SELECT BIN_TO_UUID(page_id) FROM favolo_pages where accesskey=%s;"

    sql_members_select = "SELECT BIN_TO_UUID(user_id) FROM favolo_members where mail=%s;"

    # 共通クエリの実行
    # ページ情報の取得
    cursor.execute(sql_pages_select, (accesskey, ))
    row_pages = cursor.fetchone()
    page_id = row_pages[0]

    # ユーザー情報の取得
    cursor.execute(sql_members_select, (email,))
    row_members = cursor.fetchone()
    user_id = row_members[0]

    if liked == False:
        # クエリのセット
        sql_buzz_update = "UPDATE favolo_buzz SET likes = likes + 1 where page_id=UUID_TO_BIN(%s);"  

        sql_likes_insert = "INSERT into favolo_likes (user_id, page_id) values(UUID_TO_BIN(%s), UUID_TO_BIN(%s));"

        # クエリの実行
        cursor.execute(sql_buzz_update, (page_id, ))

        cursor.execute(sql_likes_insert, (user_id, page_id))

        # 接続を終了する
        cursor.close()
        connection.commit()
        connection.close() 

        # いいねした状態にする
        liked = True
        request.session['page_liked_status'] = liked
    
    else:
        # クエリのセット
        sql_buzz_update = "UPDATE favolo_buzz SET likes = likes - 1 where page_id=UUID_TO_BIN(%s);"

        sql_likes_delete = "DELETE FROM favolo_likes where page_id=UUID_TO_BIN(%s) and user_id=UUID_TO_BIN(%s);"

        # クエリの実行
        cursor.execute(sql_buzz_update, (page_id, ))

        cursor.execute(sql_likes_delete, (page_id, user_id))

        # 接続を終了する
        cursor.close()
        connection.commit()
        connection.close() 

        # いいねしていない状態にする
        liked = False
        request.session['page_liked_status'] = liked

    return redirect('favolo:accesskey', accesskey)

# ユーザーが特定のユーザーをフォローしているか判別
# フォロー数、フォロワー数はresult、pagesで行っている
@login_required
def followed_status(request, accesskey):

    # セッションからログインユーザーの情報の取得
    # ページユーザーの情報の取得はアクセスキーを使って行う
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
    # ページユーザーのIDを取得する
    sql_pages_select = "SELECT BIN_TO_UUID(user_id) FROM favolo_pages where accesskey=%s;"

    # ログインユーザーのIDを取得する
    sql_members_select = "SELECT BIN_TO_UUID(user_id) FROM favolo_members where mail=%s;"

    # ２つのIDをもつレコードがあるか調べる
    sql_followrelation_select = "SELECT COUNT(*) FROM favolo_follow_relation where user_id = UUID_TO_BIN(%s) and followed_id = UUID_TO_BIN(%s);"

    # クエリの実行
    # ページユーザー情報の取得
    cursor.execute(sql_pages_select, (accesskey, ))
    row_pages = cursor.fetchone()
    followed_id = row_pages[0]

    # ログインユーザー情報の取得
    cursor.execute(sql_members_select, (email,))
    row_members = cursor.fetchone()
    user_id = row_members[0]

    # ログインユーザーとページユーザーが同一人物か判定
    if followed_id == user_id:
        followed_status_code = 1
    else:
        followed_status_code = 2

    # favolo_likesに存在するか（いいねされているか確認）
    cursor.execute(sql_followrelation_select, (user_id, followed_id))
    row_followrelation = cursor.fetchone()
    follows = row_followrelation[0]

    # もしfollowsが0より大きかったらTrue
    # followssが0だったらFalseを返す
    followed = False
    if follows > 0 :
        followed = True
    
    return followed_status_code, followed

@login_required
def follows(request, accesskey):

    # セッションからユーザー情報を取得
    username = request.session.get('username')
    email = request.session.get('email')

    # セッションからいいねの状態を取得
    followed = request.session.get('page_followed_status')

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

    # 共通クエリのセット
    sql_pages_select = "SELECT BIN_TO_UUID(user_id) FROM favolo_pages where accesskey=%s;"

    sql_members_select = "SELECT BIN_TO_UUID(user_id) FROM favolo_members where mail=%s;"

    # 共通クエリの実行
    # ページユーザー情報の取得
    cursor.execute(sql_pages_select, (accesskey, ))
    row_pages = cursor.fetchone()
    followed_id = row_pages[0]

    # ログインユーザー情報の取得
    cursor.execute(sql_members_select, (email,))
    row_members = cursor.fetchone()
    user_id = row_members[0]

    # 自分自身はフォローできないようにする
    if user_id == followed_id:
        followed = False
        request.session['page_followed_status'] = followed
    else:
        if followed == False:
            # クエリのセット
            # 新規フォロー関係の挿入
            sql_followrelation_insert = "INSERT INTO favolo_follow_relation (user_id, followed_id) values(UUID_TO_BIN(%s), UUID_TO_BIN(%s));"

            # ログインユーザーのフォロー数を１つ増やす
            sql_follow_update = "UPDATE favolo_follow_count SET follow = follow + 1 where user_id=UUID_TO_BIN(%s);"  

            # ページユーザーのフォロワー数を１つ増やす
            sql_followed_update = "UPDATE favolo_follow_count SET followed = followed + 1 where user_id=UUID_TO_BIN(%s);"

            # クエリの実行
            cursor.execute(sql_followrelation_insert, (user_id, followed_id))

            cursor.execute(sql_follow_update, (user_id, ))

            cursor.execute(sql_followed_update, (followed_id, ))

            # 接続を終了する
            cursor.close()
            connection.commit()
            connection.close() 

            # フォローした状態にする
            followed = True
            request.session['page_followed_status'] = followed

        else:
            # クエリのセット
            # フォロー関係の削除
            sql_followrelation_delete = "DELETE FROM favolo_follow_relation where user_id=UUID_TO_BIN(%s) and followed_id = UUID_TO_BIN(%s);"

            # ログインユーザーのフォロー数を１つ減らす
            sql_follow_update = "UPDATE favolo_follow_count SET follow = follow - 1 where user_id=UUID_TO_BIN(%s);"

            # ページユーザーのフォロワー数を１つ減らす
            sql_followed_update = "UPDATE favolo_follow_count SET followed = followed - 1 where user_id=UUID_TO_BIN(%s);"

            # クエリの実行
            cursor.execute(sql_followrelation_delete, (user_id, followed_id))

            cursor.execute(sql_follow_update, (user_id, ))

            cursor.execute(sql_followed_update, (followed_id, ))

            # 接続を終了する
            cursor.close()
            connection.commit()
            connection.close() 

            # フォローしていない状態にする
            followed = False
            request.session['page_followed_status'] = followed

    return redirect('favolo:accesskey', accesskey)




