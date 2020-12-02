# Favolo
・Twitterのいいね！をテーマに沿って紹介できるアプリ

・いいね！をしてデザインを選ぶだけでオリジナルな発信ができる

・企業のコンテンツ紹介なども可能

### 機能面
・TwitterAPIの取得機能（APIトークンを使用）

・フォロー機能（表示まで）

・いいね機能（カウント表示ができる）

・タグ機能（１つまで）

・設定機能（パスワード、コメント、デザイン、タグの変更ができる）

### テーブル設計
・favolo_members(会員情報テーブル）

・favolo_pages(会員ページテーブル）

・favolo_likes(いいねログテーブル）

・favolo_buzz(いいねカウントテーブル）

・favolo_follow_count（フォロー数テーブル）

・favolo_follow_relation（フォロー関係テーブル）

・favolo_tags_map (ページとタグの関係テーブル）

・favolo_tags_master（タグの管理テーブル）

```
CREATE TABLE favolo_members (
user_id binary(16) NOT NULL PRIMARY KEY,
name VARCHAR(30) NOT NULL,
mail VARCHAR(30) NOT NULL,
password VARCHAR(64) NOT NULL,
account VARCHAR(30) NOT NULL,
createtime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE favolo_pages (
page_id binary(16) NOT NULL PRIMARY KEY,
user_id binary(16) NOT NULL,
accesskey varchar(20) NOT NULL,
design int NOT NULL,
title varchar(50) NOT NULL,
comment varchar(500),
updatetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE favolo_likes (
like_id INT AUTO_INCREMENT PRIMARY KEY,
user_id binary(16) NOT NULL,
page_id binary(16) NOT NULL
);

CREATE TABLE favolo_buzz (
buzz_id INT AUTO_INCREMENT PRIMARY KEY,
page_id binary(16) NOT NULL,
likes INT NOT NULL DEFAULT 0
);

CREATE TABLE favolo_follow_relation (
relation_id INT AUTO_INCREMENT PRIMARY KEY,
user_id binary(16) NOT NULL,
followed_id binary(16) NOT NULL
);

CREATE TABLE favolo_follow_count (
count_id INT AUTO_INCREMENT PRIMARY KEY,
user_id binary(16) NOT NULL,
follow INT NOT NULL DEFAULT 0,
followed INT NOT NULL DEFAULT 0
);

CREATE TABLE favolo_tags_master (
master_id INT AUTO_INCREMENT PRIMARY KEY,
tag_id binary(16) NOT NULL,
name VARCHAR(30) NOT NULL,
official boolean DEFAULT TRUE
);

CREATE TABLE favolo_tags_map (
map_id INT AUTO_INCREMENT PRIMARY KEY,
tag_id binary(16) NOT NULL,
page_id binary(16) NOT NULL
);
```


## α版での問題点 
・素のSQL文を記述している

・モデルを利用していない

・関数ベースビューの記述になっている

・アプリケーションの分割ができていない

・コードが冗長

・変数の取り扱いが煩雑

### β版への移行

機能の拡充、可読性の向上、Djangoの最大利用のためにもβ版に移動する



