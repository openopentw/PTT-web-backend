# PTT-web-backend

一個基於 Flask 實作的 PTT web API。

支援多人 non-blocking 登入使用。每 60 秒會踢掉沒有動作的 user。

支援 PTT 的功能有：登入/登出、抓我的最愛、抓看板文章列表、抓文章內文、推文、發文。

## DEMO

DEMO 網頁：https://140.112.31.150/

**警告：**

使用這個網頁登入 PTT 之後，會從 server 端登入 PTT，所以帳號密碼必須傳送到 server 端。

不過本人保證 server 端不會記錄使用者的密碼。其實我偷用密碼的話算是犯罪，可以被告的。

或者你也可以自己 clone 來用，就不用怕被別人記錄密碼了。

## 安裝

- Python >= 3.6
- dependency: requirements.txt
- 記得 clone submodule
- 從 (PTT-web-frontend/releases)[https://github.com/openopentw/PTT-web-frontend/releases] 下載 build 並解壓縮
- 把 (main.py#L19)[https://github.com/openopentw/PTT-web-backend/blob/master/main.py#L19] 的 static_folder 指向 build 資料夾即可。

## 回報問題

- 本 repo 基於 https://github.com/PttCodingMan/PyPtt 來連接 PTT，因此與連接 PTT 相關的問題可以前往詢問
- 其它的問題歡迎開 issue 回報/詢問
