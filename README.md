# PTT-web-backend

一個基於 Flask 實作的 PTT web API。

支援多人 non-blocking 登入使用。每 60 秒會踢掉沒有動作的 user。

支援 PTT 的功能有：登入/登出、抓我的最愛、抓看板文章列表、抓文章內文、推文。

## DEMO

DEMO 網頁：https://140.112.31.150/

DEMO 影片：https://youtu.be/c4JDuU\_OIR0

**警告：**

使用這個網頁登入 PTT 之後，會從 server 端登入 PTT，所以帳號密碼必須傳送到 server 端。

不過本人保證 server 端不會記錄使用者的密碼。其實我偷用密碼的話算是犯罪，可以被告的。

或者你也可以自己 clone 來用，或是用下面的相關連結提到的本地 app，就不用怕被別人記錄密碼了。

## 安裝

- Python >= 3.6
- dependency: requirements.txt
- 從 [PTT-web-frontend/releases](https://github.com/openopentw/PTT-web-frontend/releases) 下載 build 並解壓縮
- 執行 main.py 時，讓 `--static` 的參數指向上述的這個 build 資料夾即可。

## 相關連結

- 本 repo 是基於 [PttCodingMan/PyPtt](https://github.com/PttCodingMan/PyPtt) 來連接 PTT，這是一個很好用的套件，也一直有在更新，推薦各位前往使用。
- 基於這個 repo 做的本地 app：https://github.com/openopentw/PTT-app ，可以在本地登入使用，就不用連到我的 server 了。

## 回報問題

有問題歡迎開 issue 回報/詢問。但我還是學生，有時候很忙，不一定能馬上回覆或實作，請見諒！
