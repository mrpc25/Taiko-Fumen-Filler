# Fumen Filler
這是一個可以自動依照譜面填入音符的小工具
可以依照既有的譜面內容，重新填上新的音符（包括空白的譜面）

## How to Use
[![Video Title](https://img.youtube.com/vi/6VgpX50gQfA/maxresdefault.jpg)](https://youtu.be/6VgpX50gQfA)

下載後執行interface_multi.py，即可進行操作。

### Code
#### 主要檔案會包括以下
| file | function |
| :-----------: |:-------------:|
| interface_multi.py | 主程式，整個過程的操作介面 |
| taiko.py           | 解讀譜面內容 |
| predict_model.py   | 定義預測過程會會使用到的模型 |
| model/             | 儲存預測過程會會使用到的模型參數檔 |
| predict_process.py | 負責預測過程中的計算部分 |
| filling_process.py | 將預測好的結果轉回譜面的形式，並顯示在操作介面 |

#### 其他（非必要）
| file | function |
| :-----------: |:-------------:|
| empty_fumen_generator.py | 可初步生成工具需要使用的空白（待定）譜面<br>，同時也是以操作介面為主 |

### Rough Process:
* 製作一個`空白譜面`，並連結到正確的音源位置
> edit: 後來我覺得影片中「空白譜面」這個稱呼不太對，這個譜面的用途應該比較適合稱為「待定譜面」，下面的Notice有理由
* 利用此工具載入譜面
  * 在左上的`File`標籤裡，透過`Open`選項來載入譜面檔案(.tja)
  * 選擇對應的譜面代號後，按下 `FUMEN`進一步解讀譜面
  * > 因為一個譜面檔案裡面可能不只有一份譜面，例如鬼/松/竹，單雙人，表裏...<br>
      遮些在同一個譜面檔案的譜面會被此工具視為不同譜面，並加上編號，也就是上面的譜面代號。
* 選擇模型後開始做填入音符的預測
  * 選擇模型種類並選擇模型參數檔後， 按下 `MODEL`來載入模型.
  * 接著`Start Predicting Fumen Context`可以進行預測
* 取得預測的結果並輸出成譜面檔案
  * `Filling The Predict Result Info Fumen`: 將預測結果顯示在左下角的大文字框
  * 透過左上的`File`標籤裡，透過`Save`選項來將結果儲存成譜面檔案(.tja)

### GUI Flow Chart
![This is an alt text.](/img/gui_flow_chart.png "Flow Chart")

## Notice
所謂的`空白譜面`不能真的完全空白。

因為這個工具不會預測鼓點出現的時間點，只會依照給好的時間點來預測當下會有什麼音符。<br>
而這項工具會預先將譜面當中的鼓點轉換成時間點，再做後續處理。

### Example
以一個一段BPM120 4/4的小節為例，以16分音表示的話會變成：
```
0000 0000 0000 0000,
```
這樣的話，這個小節就會被切成16個鼓點，並在這16個原先的鼓點重新替換上新的音符 (無音符/咚/咔/大咚/大咔，沒有連打音符)。<br>
如果小節開始的時候是0秒的話。那麼就會在0秒、0.0625秒、0.125秒、...、0.8125、0.875秒、0.9375秒處，各做一次總共16次的預測

而如果是8分音表示的話：
```
00 00 00 00,
```
那麼最後這個小節就只會有8個鼓點。<br>
如果小節開始的時候是0秒的話。那麼就會在0秒、0.125秒、0.25秒、...、0.625、0.75秒、0.875秒處，各做一次總共8次的預測

而這個所謂的「空白譜面」其實也可以填其他東西，預先填好所有鼓點只是為了計算時間點而已<br>
以下三個小節其實是一樣的：
```
0000000000000000,
```
```
1000100010001000,
```
```
3333333333333333,
```
所以我覺得從功能和目的上來說，應該不是「空白譜面」，「待定譜面」會比較適合<br>
也可以使用本工具附的empty fumen generator來產生這個譜面。

而如果譜面是真的像以下這樣的「空白」:
```
#START
,
,
,
,
,
,
,
#END
```
即使這個譜面內容播放後是幾個無音符的小節，<br>
但是這個情況會發生錯誤，因為這個工具會找不到任何鼓點來設置時間點。

## Requirements
### Python
* 3.10 at least
### interface_multi
* torch & torchaudio (cuda)
* soundfile
* matplotlib
* tqdm
### empty_fumen_generator
* librosa
* numpy

```
Package            Version
------------------ ------------
librosa            0.10.2.post1
matplotlib         3.10.0
numpy              2.1.3
soundfile          0.13.1
torch              2.6.0+cu118
torchaudio         2.6.0+cu118
tqdm               4.67.1
```
> edit: 當初沒有特別注意版本問題，除了python本身的版本以外，以上版本只是做為參考用

## Model Types
| Model Name | Corresponding Model |  |
| :-----------: |:-------------:|:-------------:|
| 240618        | Pure CNN      | 著重在每個鼓點本身，運算上較快 |
| otherwise     | self-attention + CNN| 考慮進鼓點本身及附近的有限數量的鼓點，運算上稍慢 |
