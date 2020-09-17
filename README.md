# PTT-web-backend

一個基於 Flask 實作的 PTT web API。

支援多人 non-blocking 登入使用。每 60 秒會踢掉沒有動作的 user。

支援 PTT 的功能有：登入/登出、抓我的最愛、抓看板文章列表、抓文章內文、推文、發文。

## DEMO

DEMO 網頁：https://140.112.31.150/

警告：使用這個網頁登入 PTT 之後，會從 server 端登入 PTT，所以帳號密碼必須傳送到 server 端。本人保證 server 端不會記錄使用者的密碼。或者你也可以自己 fork 來用，就不用怕被別人記錄密碼了。

前端的程式碼改天也會開源，等我之後整理好就開源。

## 安裝細節

- Python >= 3.6
- Dependency: requirements.txt
- 記得 clone submodule

## 回報問題

- 本 repo 基於 https://github.com/PttCodingMan/PyPtt 來連接 PTT，因此與連接 PTT 相關的問題可以前往詢問
- 其它的問題歡迎開 issue 回報/詢問
