from taiko import TaikoFumen
from taiko import TaikoFumenInner
from taiko import TaikoFumenBranched
import predict_model as pm
import predict_process as pp
import filling_process as fp

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import os
import configparser

import torch

def ReadConfig(configpath,SECTION,KEY):
    config = configparser.ConfigParser()
    config.read(configpath, encoding="utf-8")
    return config[SECTION][KEY]

def WriteConfig(configpath,SECTION,KEY,value):
    config = configparser.ConfigParser()
    config.read(configpath)
    config[SECTION][KEY] = value
    with open(configpath, 'w') as configfile:    # save
        config.write(configfile)

device = pm.device

root = tk.Tk()
root.iconbitmap('img/root.ico')
root.title('Taiko Fumen Filler (v1.04)')

width = 640
height = 480
left = root.winfo_screenwidth() // 4
top = root.winfo_screenheight() // 4
root.geometry(f'{width}x{height}+{left}+{top}')  # 定義視窗的尺寸和位置

#--------------------------------------------------------初始化--------------------------------------------------------

def value_initialization():
    global fumen_path
    global ChooseFumen_btn
    global StratPrediction_btn
    global FillingFumen_btn
    global BranchOptionList
    global fumen_Info_Update_btn
    global Remastered_fumen
    global Codec_verified_btn

    ChooseFumen_btn.configure(state="disabled")
    fumen_path = "-"

    FumenOptionList.configure(values=[], state="disable")
    FumenOptionList.set("-")

    BranchOptionList = ttk.Combobox(root, width=34, height=10, values=[], justify='center', state="disable")
    BranchOptionList.set("-")
    BranchOptionList.place(relx=0.12, rely=0.175, anchor='w')

    StratPrediction_btn.configure(state='disabled')
    FillingFumen_btn.configure(state='disabled')
    fumen_Info_Update_btn.configure(state='disabled')

    filemenu.entryconfigure(2, state='disabled') #把"filemenu"的第2個選項作修改

    COURSE_value.set("")
    DUAL_value.set("")
    LEVEL_value.set("")
    SIDE_value.set("")
    TITLE_value.set("")
    SUBTITLE_value.set("")
    WAVE_value.set("")
    OFFSET_value.set("")
    INITIAL_BPM_value.set("")
    DEMOSTART_value.set("")
    COURSE_CUS_value.set("")
    LEVEL_CUS_value.set("")
    OFFSET_current_text_value.set("")
    fumen_path_value.set("")
    OFFSET_change_value.set("-0.0")

    Remastered_fumen = ""
    Remastered_fumen_display.delete(1.0, tk.END)

    global PredictDistribution_bar_List
    global PredictDistribution_note_List

    PredictDistribution_bar_List.configure(values=[], state='disabled')
    PredictDistribution_bar_List.set('-')

    PredictDistribution_note_List.configure(values=[], state='disabled')
    PredictDistribution_note_List.set('-')

    make_possibility_distribution_figure([0]*5)
    Codec_verified_btn.deselect()

    global fumen_info_ready
    global model_weight_ready
    global fumen_prediction_ready
    
    fumen_info_ready = False

    global Codec_prepared
    Codec_prepared = False
current_fumen_selected = False

#--------------------------------------------------------決定讀取譜面的Codec--------------------------------------------------------

Codec = ReadConfig("config.ini", "FUMEN", "codec")
Codec_text = tk.Label(root, text="Codec" + " = ")
Codec_text.place(relx=0.555, rely=0.005, anchor='nw')
Codec_Option = ["utf_8", "ascii", "cp860", "johab", "shift_jis", "big5", "hz", "unicode_escape", "raw_unicode_escape"]

CodecOptionList = ttk.Combobox(root, width=24, height=5, values=Codec_Option, justify='center')
CodecOptionList.set(Codec)

def Update_Codec_Option(event):  #隨著選項，更新譜面的選用Codec
    global CodecOptionList
    global Codec
    Codec = CodecOptionList.get()
    Codec_verified_btn.deselect()
    WriteConfig("config.ini", "FUMEN", "codec", Codec)

def Custom_Codec_Input_CallBack(event): #自行輸入，並更新Codec (https://stackoverflow.com/questions/60692345/how-to-use-ttk-combobox-with-keyboard-entry-using-return-key-press-as-event)
    Codec = CodecOptionList.get()
    Codec_verified_btn.deselect()
    WriteConfig("config.ini", "FUMEN", "codec", Codec)

CodecOptionList.bind("<<ComboboxSelected>>", Update_Codec_Option)
CodecOptionList.bind("<Return>",Custom_Codec_Input_CallBack) 
CodecOptionList.place(relx=0.94, rely=0.005, anchor='ne')

Codec_verified = tk.StringVar()
Codec_verified_btn = tk.Checkbutton(root, text='', variable=Codec_verified, onvalue=1, offvalue=0, state='disabled')
Codec_verified_btn.place(relx=0.99, rely=0.005, anchor='ne')
Codec_verified_btn.deselect()

#--------------------------------------------------------讀取譜面--------------------------------------------------------

def Reduced_file_path(Og_path):
    New = ""
    for char in Og_path:
        New = New + char if (char!="/") else "" #一遇到"/"，就代表真實檔案名稱還在後面，所以清空並再紀錄。
    return New

def Ask_forfile():
    global fumen_path
    global ChooseFumen_btn
    global FumenOptionList
    global current_fumen_selected

    if current_fumen_selected:
        continue_process = messagebox.askokcancel('prompt', "Open Alert: Opening New Fumen File Will Erase Data Of The Old Fumen.")
        if(not continue_process): return
    value_initialization()
    fumen_path = filedialog.askopenfilename(filetypes=[("Choose a fumen", '*.tja')])
    current_fumen_selected = True
    if(fumen_path==""): 
        current_fumen_selected = False
        return

    ChooseFumen_btn.configure(state='active')
    fumen_path_value.set(Reduced_file_path(fumen_path))
    Ask_WhichFumen()

FumenOptionList = ttk.Combobox(root, width=2, height=5, values=[], justify='center', state='disable')
FumenOptionList.place(relx=0.12, rely=0.1, anchor='w')
SelectedYet = False
def Ask_WhichFumen():
    global fumen_path
    global song_basic
    global Fumen_Option_raw
    global FumenOptionList
    global current_fumen_selected

    try:
        song_basic = TaikoFumen(fumen_path, Codec)
    except:
        error_message = f"Error Reading Basic Context Using: {Codec}"
        messagebox.showerror('showinfo', error_message)
        current_fumen_selected = False
        raise Exception(error_message)
    
    Fumen_Option_raw = song_basic.BasicInfoOverViewDict
    Fumen_Option = list(range(len(Fumen_Option_raw)))

    FumenOptionList = ttk.Combobox(root, width=2, height=5, values=Fumen_Option, justify='center', state="readonly")
    FumenOptionList.bind("<<ComboboxSelected>>", Update_FumenOption)
    FumenOptionList.place(relx=0.12, rely=0.1, anchor='w')

def Update_FumenOption(event):  #隨著選項，更新譜面顯示的相關資訊
    global BranchOptionList
    global SelectedYet
    
    FumenOption = FumenOptionList.get()
    SelectedYet = not (FumenOption=="-" or FumenOption==None)

    COURSE_value.set(Fumen_Option_raw[int(FumenOption)]["difficulty"])
    DUAL_value.set(Fumen_Option_raw[int(FumenOption)]["dual"])
    LEVEL_value.set(Fumen_Option_raw[int(FumenOption)]["level"])
    SIDE_value.set(Fumen_Option_raw[int(FumenOption)]["side"])

fumen_path_text = tk.Label(root, text="FileName ")
fumen_path_text.place(relx=0.005, rely=0.005, anchor='nw')
fumen_path_value = tk.StringVar()
fumen_path_display = tk.Entry(root, textvariable=fumen_path_value, width=37, state="readonly")
fumen_path_display.place(relx=0.12, rely=0.005, anchor='nw')

#Step2 / 選擇譜面以後，載入基本資訊，並判斷有無分岐
ChoosenBranch = ""
ChoosenBranchValue = tk.StringVar()                                        # 取值
ChoosenBranchValue.set(ChoosenBranch)

Branch = ["0 / 普通譜面 / Normal", "1 / 玄人譜面 / Professional", "2 / 達人譜面 / Master"]
BranchOptionList = ttk.Combobox(root, width=29, height=10, values=[], justify='center', state='disabled')
ProcessedYet_branch = False
def Ask_FumenInner():
    global fumen_path
    global song_selected
    global BranchOptionList
    global ChoosenBranchValue #test
    global Fumen_Option_raw
    global FumenOption
    global current_fumen_selected

    FumenOption = FumenOptionList.get()
    try: 
        song_selected = TaikoFumenInner(fumen_path, Codec, int(FumenOption[0]))
    except: 
        error_message = f"Error Reading Inner Context Using: {Codec}"
        messagebox.showerror('showinfo', error_message)
        current_fumen_selected = False
        raise Exception(error_message)

    if(song_selected.IsBranchExist):
        #按鈕狀態設定
        ChooseBranch_btn.configure(state="active")
        ChoosenBranchValue.set(Branch[2])

        BranchOptionList.configure(values=Branch, justify='center', state="readonly")
        BranchOptionList.bind("<<ComboboxSelected>>", Update_BranchOption)
        BranchOptionList.set(Branch[2])

    else:
        #按鈕狀態設定
        ChooseBranch_btn.configure(state="disabled")
        ChoosenBranchValue.set(None)

        BranchOptionList.configure(values=[], justify='center', state='disabled')
        BranchOptionList.set("No Branches Was Found")

        Ask_FinalFumen() #沒有分歧，就可以直接進行譜面最後解析的動作

def Update_BranchOption(event): pass

ChooseFumen_btn = tk.Button(root, text="FUMEN" , width=7, command=Ask_FumenInner, height=1, justify='center')          #不能寫成"Ask_FumenInner()"，這樣會自動執行Ask_FumenInner的函式
ChooseFumen_btn.place(relx=0.01, rely=0.1, anchor='w')

#Step3 / 選擇分期狀態以後，
def Ask_FinalFumen():
    global fumen_path
    global song_branched
    global SelectedYet
    global BranchOption
    global current_fumen_selected

    FumenOption = FumenOptionList.get()
    BranchOption = BranchOptionList.get()
    try: 
        song_branched = TaikoFumenBranched(fumen_path, Codec, int(FumenOption), int(BranchOption[0]) if song_selected.IsBranchExist else None)
    except: 
        error_message = f"Error Reading Branched Context Using: {Codec}"
        messagebox.showerror('showinfo', error_message)
        current_fumen_selected = False
        raise Exception(error_message)

    Extract_Info_For_Use()

#Step / 擷取出需要用以預測的資料，
def Extract_Info_For_Use():
    global song_branched
    global Audio_path
    global fumen_info_ready
    audio_name = song_branched.OffsetThingsValue_PareIgnored("WAVE:",[0, len(song_branched.EveryRow)])
    def FilePathOnlyDir(path):
        if "/" not in path: return ""
        while(path[-1]!="/" and len(path)>0): path = path.rstrip(path[-1])
        return path
    Audio_path = FilePathOnlyDir(fumen_path) + audio_name

    global LocationToNotes
    global LocationToNotes
    global OFFSET
    global OFFSET_CHANGE
    global AbsoluteTime
    global MeasureConfiguration
    global BpmConfiguration
    global NUM_OF_BAR
    LocationToNotes = song_branched.FindEveryPassedNotesLocation()
    OFFSETString = song_branched.OffsetThingsValue("OFFSET:", [0, song_branched.Song_Begin[0]])
    OFFSETChangeString = OFFSET_change_value.get()
    OFFSET = 0 if OFFSETString=='' else float(OFFSETString)
    OFFSET_CHANGE = 0 if OFFSETChangeString=='' else float(OFFSETChangeString)
    AbsoluteTime = [-(OFFSET+OFFSET_CHANGE) + song_branched.Duration([0,0],location)[0] for location in LocationToNotes]
    MeasureConfiguration = song_branched.Find_BeatsToMeasure_Of_EachNotesInLoaction()
    BpmConfiguration = song_branched.Find_BPM_Of_EachNotesInLoaction()
    NUM_OF_BAR = len(song_branched.EveryBar)

    OFFSET_current_text_value.set(OFFSET+OFFSET_CHANGE)
    Codec_verified_btn.select()

    fumen_info_ready = True
    if(fumen_info_ready and model_weight_ready): StratPrediction_btn.configure(state='active')

ChooseBranch_btn = tk.Button(root, text="BRANCH", width=7, command=Ask_FinalFumen, state="disabled")          #同ChooseFumen_btn
ChooseBranch_btn.place(relx=0.01, rely=0.175, anchor='w')

#顯示選擇譜面時的基本資訊
COURSE_text = "-"
COURSE_value = tk.StringVar()              
COURSE_dis = tk.Entry(root, textvariable=COURSE_value, width=6, justify='center', state="readonly")
COURSE_dis.place(relx=0.232, rely=0.1, anchor='center')

DUAL_text = "-"
DUAL_value = tk.StringVar()              
DUAL_dis = tk.Entry(root, textvariable=DUAL_value, width=6, justify='center', state="readonly")
DUAL_dis.place(relx=0.319, rely=0.1, anchor='center')

LEVEL_text = "-"
LEVEL_value = tk.StringVar()              
LEVEL_dis = tk.Entry(root, textvariable=LEVEL_value, width=6, justify='center', state="readonly")
LEVEL_dis.place(relx=0.406, rely=0.1, anchor='center')

SIDE_text = "-"
SIDE_value = tk.StringVar()              
SIDE_dis = tk.Entry(root, textvariable=SIDE_value, width=6, justify='center', state="readonly")
SIDE_dis.place(relx=0.493, rely=0.1, anchor='center')

#--------------------------------------------------------定義模型--------------------------------------------------------

MODEL_PLACE = "model_multi"
model_types = os.listdir(MODEL_PLACE)
model_weight = ""

def Update_Model_Type_Option(event):
    global ModelTypeOptionList
    global ModelWeightOptionList
    global ChooseModel_btn
    global model_type
    global model_weight
    model_type = MODEL_PLACE + "/" + ModelTypeOptionList.get()
    model_weights = os.listdir(model_type)
    model_weights = [file for file in model_weights if file.endswith(".pth")]
    ModelWeightOptionList.set("<No Weight>")
    ModelWeightOptionList.configure(values=model_weights)
    ChooseModel_btn.configure(state="disabled")
    WriteConfig("config.ini", "AUDIO", "freqency_bin", ReadConfig(model_type+"/config.ini","AUDIO","freqency_bin")) #從選定模型讀取自己的模型初始架構參數，並修改最外層記載的模型參數
    WriteConfig("config.ini", "AUDIO", "segment", ReadConfig(model_type+"/config.ini","AUDIO","segment"))

def Update_Model_Weight_Option(event):  #隨著選項，更新譜面顯示的相關資訊
    global model_weight
    global ModelTypeOptionList
    global ModelWeightOptionList
    global ChooseModel_btn
    global model_type

    model_weight = model_type + "/" + ModelWeightOptionList.get()

    if (model_weight!="<No Weight>"):
        ChooseModel_btn.configure(state="active")
    else:
        ChooseModel_btn.configure(state="disabled")

model_weight_ready = False
def Load_Model_Parameters():
    global device
    global model_weight
    global TaikoModel
    global model_weight_ready
    global ModelTypeOptionList

    global model_used

    MODEL_TYPE = ReadConfig(f"model_multi/{ModelTypeOptionList.get()}/config.ini", "MODEL", "type")
    model_used = pm.model_set[MODEL_TYPE]
    
    #定義模型
    TaikoModel = model_used(5).to(device)
    TaikoModel.load_state_dict(torch.load(model_weight, map_location=torch.device(device)))
    TaikoModel.state_dict()
    TaikoModel.eval()

    OFFSET_model_text_value.set(ModelTypeOptionList.get() + "/" + ModelWeightOptionList.get())

    global fumen_info_ready
    global model_weight_ready
    model_weight_ready = True
    if(fumen_info_ready and model_weight_ready): StratPrediction_btn.configure(state='active')

ChooseModel_btn = tk.Button(root, text="MODEL" , width=7, command=Load_Model_Parameters, height=1, justify='center', state='disabled')
ChooseModel_btn.place(relx=0.01, rely=0.25, anchor='w')

ModelTypeOptionList = ttk.Combobox(root, width=10, height=10, values=model_types, justify='center', state="readonly")
ModelTypeOptionList.set("<No Model>")
ModelTypeOptionList.bind("<<ComboboxSelected>>", Update_Model_Type_Option)
ModelTypeOptionList.place(relx=0.12, rely=0.25, anchor='w')

ModelWeightOptionList = ttk.Combobox(root, width=20, height=10, values=[], justify='center', state="readonly")
ModelWeightOptionList.set("<No Weight>")
ModelWeightOptionList.bind("<<ComboboxSelected>>", Update_Model_Weight_Option)
ModelWeightOptionList.place(relx=0.275, rely=0.25, anchor='w')

#--------------------------------------------------------開始預測--------------------------------------------------------

def Predict_Fumen_Context():
    global Audio_path
    global LocationToNotes
    global BpmConfiguration
    global AbsoluteTime
    global TaikoModel
    global song_branched
    global predictResult
    global predictResult_to_dict
    global PredictDistribution_bar_List
    global ModelTypeOptionList
    global NUM_OF_BAR

    MODEL_TYPE = ReadConfig(f"model_multi/{ModelTypeOptionList.get()}/config.ini", "MODEL", "type")
    compute_process = pp.compute_set[MODEL_TYPE]

    song_branched, predictResult = compute_process(Audio_path, LocationToNotes, BpmConfiguration, AbsoluteTime, TaikoModel, song_branched)
    predictResult_to_dict = pp.distribution_result_remake(LocationToNotes, predictResult)

    global fumen_prediction_ready
    fumen_prediction_ready = True
    FillingFumen_btn.configure(state='active')

    PredictDistribution_bar_List.configure(values=list(range(NUM_OF_BAR)), state='readonly')
    PredictDistribution_bar_List.set('-')

StratPrediction_btn = tk.Button(root, text="Start Predicting Fumen Context" , width=37, command=Predict_Fumen_Context, height=1, justify='center', state="disabled")
StratPrediction_btn.place(relx=0.975, rely=0.25, anchor='e')

#--------------------------------------------------------填上結果--------------------------------------------------------

def ReFilling_Fummen_By_NewInfo():
    global model_weight
    global fumen_info_pack
    fumen_info_pack.TITLE = TITLE_value.get()
    fumen_info_pack.SUBTITLE = SUBTITLE_value.get()
    fumen_info_pack.WAVE = WAVE_value.get()
    fumen_info_pack.OFFSET = OFFSET_value.get()
    fumen_info_pack.INIT_BPM = INITIAL_BPM_value.get()
    fumen_info_pack.DEMOSTART = DEMOSTART_value.get()
    fumen_info_pack.COURSE = COURSE_CUS_value.get()
    fumen_info_pack.LEVEL = LEVEL_CUS_value.get()
    
    global Remastered_fumen
    global Bar
    Remastered_fumen = fp.fumen_filling(song_branched, fumen_info_pack.OFFSET, model_weight, Bar.get(), fumen_info_pack)
    Update_Displayed_Context(Remastered_fumen)
    filemenu.entryconfigure(2, state='active') #把"filemenu"的第2個選項作修改

def Update_Current_Info():
    global fumen_info_pack
    global TITLE_value
    global SUBTITLE_value
    global WAVE_value
    global OFFSET_value
    global INITIAL_BPM_value
    global DEMOSTART_value
    global COURSE_value
    global LEVEL_value
    global OFFSET_CHANGE

    TITLE_value.set(fumen_info_pack.TITLE)
    SUBTITLE_value.set(fumen_info_pack.SUBTITLE)
    WAVE_value.set(fumen_info_pack.WAVE)
    OFFSET_value.set(f"{float(fumen_info_pack.OFFSET) + OFFSET_CHANGE}")
    INITIAL_BPM_value.set(fumen_info_pack.INIT_BPM)
    DEMOSTART_value.set(fumen_info_pack.DEMOSTART)
    COURSE_CUS_value.set(fumen_info_pack.COURSE)
    LEVEL_CUS_value.set(fumen_info_pack.LEVEL)

def Filling_Fumen():
    global fumen_info_pack
    global Fumen_Option_raw
    global song_branched
    global OFFSET
    global OFFSET_CHANGE
    global model_weight
    global Remastered_fumen
    global Remastered_fumen_display
    global Bar

    fumen_info_pack = fp.fumen_info_before_start(song_branched, Fumen_Option_raw[int(FumenOption)]["level"], Fumen_Option_raw[int(FumenOption)]["difficulty"])
    Remastered_fumen = fp.fumen_filling(song_branched, OFFSET+OFFSET_CHANGE, model_weight, Bar.get(), fumen_info_pack)
    
    Update_Displayed_Context(Remastered_fumen)
    Update_Current_Info()

    fumen_Info_Update_btn.configure(state="active")
    filemenu.entryconfigure(2, state='active') #把"filemenu"的第2個選項作修改

def Update_Displayed_Context(Remastered_fumen):
    Remastered_fumen_display.delete(1.0, tk.END)
    Remastered_fumen_display.insert(tk.END, Remastered_fumen)

FillingFumen_btn = tk.Button(root, text="Filling The Predict Result Into Fumen" , width=87, command=Filling_Fumen, height=1, justify='center', state="disabled")
FillingFumen_btn.place(relx=0.491, rely=0.325, anchor='center')

#--------------------------------------------------------結果展示--------------------------------------------------------

Remastered_fumen_display = tk.Text(root, font=("consolas",10) ,wrap="word", width=47, height=19)  # 放入多行輸入框
Remastered_fumen_display.place(relx=0.27, rely=0.67, anchor='center')

Remastered_fumen_display_text = tk.Label(root, text="Remastered Fumen Preview")
Remastered_fumen_display_text.place(relx=0.65, rely=0.365, anchor='nw')

separator_1 = ttk.Separator(root, orient='horizontal')
separator_1.place(relx=0.765, rely=0.415, relwidth=0.42, anchor='center')

Custom_parameters_display_text = tk.Label(root, text="Custom Parameters In Fumen")
Custom_parameters_display_text.place(relx=0.56, rely=0.422, anchor='nw')

fumen_Info_Update_btn = tk.Button(root, text="Update" , width=10, command=ReFilling_Fummen_By_NewInfo, height=1, justify='center', state="disabled")
fumen_Info_Update_btn.place(relx=0.85, rely=0.417, anchor='nw')

TITLE_text = tk.Label(root, text="TITLE")
TITLE_text.place(relx=0.56, rely=0.49, anchor='w')
TITLE_value = tk.StringVar()
TITLE_value_display = tk.Entry(root, textvariable=TITLE_value, width=32, state='normal')
TITLE_value_display.place(relx=0.975, rely=0.49, anchor='e')

SUBTITLE_text = tk.Label(root, text="SUBTITLE")
SUBTITLE_text.place(relx=0.56, rely=0.54, anchor='w')
SUBTITLE_value = tk.StringVar()
SUBTITLE_value_display = tk.Entry(root, textvariable=SUBTITLE_value, width=29, state='normal')
SUBTITLE_value_display.place(relx=0.975, rely=0.54, anchor='e')

WAVE_text = tk.Label(root, text="WAVE")
WAVE_text.place(relx=0.56, rely=0.59, anchor='w')
WAVE_value = tk.StringVar()
WAVE_value_display = tk.Entry(root, textvariable=WAVE_value, width=31, state='normal')
WAVE_value_display.place(relx=0.975, rely=0.59, anchor='e')

OFFSET_text = tk.Label(root, text="OFFSET")
OFFSET_text.place(relx=0.56, rely=0.64, anchor='w')
OFFSET_value = tk.StringVar()
OFFSET_value_display = tk.Entry(root, textvariable=OFFSET_value, width=13, state='normal', justify='center')
OFFSET_value_display.place(relx=0.795, rely=0.64, anchor='e')

INITIAL_BPM_text = tk.Label(root, text="BPM")
INITIAL_BPM_text.place(relx=0.805, rely=0.64, anchor='w')
INITIAL_BPM_value = tk.StringVar()
INITIAL_BPM_value_display = tk.Entry(root, textvariable=INITIAL_BPM_value, width=10, state='normal', justify='center')
INITIAL_BPM_value_display.place(relx=0.975, rely=0.64, anchor='e')

DEMOSTART_text = tk.Label(root, text="DEMOSTART")
DEMOSTART_text.place(relx=0.56, rely=0.69, anchor='w')
DEMOSTART_value = tk.StringVar()
DEMOSTART_value_display = tk.Entry(root, textvariable=DEMOSTART_value, width=25, state='normal', justify='center')
DEMOSTART_value_display.place(relx=0.975, rely=0.69, anchor='e')

COURSE_CUS_text = tk.Label(root, text="COURSE")
COURSE_CUS_text.place(relx=0.56, rely=0.74, anchor='w')
COURSE_CUS_value = tk.StringVar()
COURSE_CUS_value_display = tk.Entry(root, textvariable=COURSE_CUS_value, width=7, state='normal', justify='center')
COURSE_CUS_value_display.place(relx=0.735, rely=0.74, anchor='e')

LEVEL_CUS_text = tk.Label(root, text="LEVEL")
LEVEL_CUS_text.place(relx=0.745, rely=0.74, anchor='w')
LEVEL_CUS_value = tk.StringVar()
LEVEL_CUS_value_display = tk.Entry(root, textvariable=LEVEL_CUS_value, width=4, state='normal', justify='center')
LEVEL_CUS_value_display.place(relx=0.865, rely=0.74, anchor='e')

Bar = tk.StringVar()
Bar_btn = tk.Checkbutton(root, text='BarTag', variable=Bar, onvalue=1, offvalue=0)
Bar_btn.place(relx=0.98, rely=0.74, anchor='e')
Bar_btn.select()

#--------------------------------------------------------機率接露--------------------------------------------------------

def Update_predict_dis_bar(event):
    global song_branched
    global PredictDistribution_bar_List
    global PredictDistribution_note_List

    CHOSEN_BAR = int(PredictDistribution_bar_List.get())
    NOTE_NUM = len(song_branched.EveryBar[CHOSEN_BAR])-1
    PredictDistribution_note_List.configure(values=list(range(NOTE_NUM)), state="readonly" if NOTE_NUM!=0 else "disabled")
    PredictDistribution_note_List.set("-")
    PredictDistribution_note_List.configure()

    make_possibility_distribution_figure([0]*5)
    
def Update_predict_dis_note(event):
    global PredictDistribution_bar_List
    global PredictDistribution_note_List
    global predictResult_to_dict

    BAR = PredictDistribution_bar_List.get()
    NOTE = PredictDistribution_note_List.get()
    note_correspoding_distribution = predictResult_to_dict[f"{BAR}/{NOTE}"]
    
    make_possibility_distribution_figure(note_correspoding_distribution)

def make_possibility_distribution_figure(info):
    f = Figure(figsize=(2.1, 0.64), dpi=100)
    ax = f.add_subplot(111)
    ind = [0, 1, 2, 3, 4]  # the x locations for the groups
    width = .5

    max_value = max(info) # Find the maximum value in the distribution
    colors = ['blue' if value != max_value else 'red' for value in info] # Set colors for the bars

    ax.bar(ind, info, width, align='center', color=colors)
    ax.set_ylim(0, 1)
    ax.set_xticks(ind)

    canvas = FigureCanvasTkAgg(f, master=root)
    canvas.draw()
    canvas.get_tk_widget().place(relx=0.81, rely=0.908, anchor='center')

Distribution_possibility_text = tk.Label(root, text="Result Possibility")
Distribution_possibility_text.place(relx=0.78, rely=0.79, anchor='center')

separator_1 = ttk.Separator(root, orient='horizontal')
separator_1.place(relx=0.765, rely=0.82, relwidth=0.42, anchor='center')

note_for_predict_text = tk.Label(root, text="NOTE")
note_for_predict_text.place(relx=0.56, rely=0.855, anchor='w')

PredictDistribution_bar_List = ttk.Combobox(root, width=3, height=10, values=[], justify='center', state="readonly")
PredictDistribution_bar_List.set("-")
PredictDistribution_bar_List.bind("<<ComboboxSelected>>", Update_predict_dis_bar)
PredictDistribution_bar_List.place(relx=0.56, rely=0.905, anchor='w')


PredictDistribution_note_List = ttk.Combobox(root, width=3, height=10, values=[], justify='center', state="readonly")
PredictDistribution_note_List.set("-")
PredictDistribution_note_List.bind("<<ComboboxSelected>>", Update_predict_dis_note)
PredictDistribution_note_List.place(relx=0.56, rely=0.955, anchor='w')

#-------------------------------------------------顯示目前狀態/OFFSET更動-------------------------------------------------

OFFSET_change_text = tk.Label(root, text="OFFSET additional change: \t\t           s")
OFFSET_change_text.place(relx=0.555, rely=0.187, anchor='w')
OFFSET_change_value = tk.StringVar()
OFFSET_change_value_display = tk.Entry(root, textvariable=OFFSET_change_value, width=12, state='normal', justify='center')
OFFSET_change_value_display.place(relx=0.95, rely=0.187, anchor='e')

OFFSET_current_text = tk.Label(root, text="Current OFFSET value used: \t\t           s")
OFFSET_current_text.place(relx=0.555, rely=0.137, anchor='w')
OFFSET_current_text_value = tk.StringVar()
OFFSET_current_text_value_display = tk.Entry(root, textvariable=OFFSET_current_text_value, width=12, state='disabled', justify='center')
OFFSET_current_text_value_display.place(relx=0.95, rely=0.137, anchor='e')

OFFSET_model_text = tk.Label(root, text="Current Model: ")
OFFSET_model_text.place(relx=0.555, rely=0.087, anchor='w')
OFFSET_model_text_value = tk.StringVar()
OFFSET_model_text_value_display = tk.Entry(root, textvariable=OFFSET_model_text_value, width=24, state='disabled', justify='center')
OFFSET_model_text_value_display.place(relx=0.975, rely=0.087, anchor='e')

#--------------------------------------------------------儲存譜面--------------------------------------------------------

def SaveFile():
    save_path = filedialog.asksaveasfilename(filetypes=[("Save fumen", '*.tja')])
    if save_path=="": return
    if not save_path.endswith(".tja"): save_path = save_path + ".tja"

    with open(save_path, 'w', encoding=CodecOptionList.get()) as writer:
        writer.write(Remastered_fumen_display.get(1.0, tk.END))

    messagebox.showinfo('showinfo', f"Succesfully Save As A File Called \"{Reduced_file_path(save_path)}\"")

#--------------------------------------------------------Tkinter視窗--------------------------------------------------------

#主選單
menubar = tk.Menu(root)               # 建立主選單
filemenu = tk.Menu(menubar)           # 建立子選單，選單綁定 menubar 主選單
filemenu.add_command(label="Open", command=Ask_forfile, state='active')    # 子選單項目
filemenu.add_command(label="Save", command=SaveFile, state='disabled')    # 子選單項目
menubar.add_cascade(label="File", menu=filemenu)   # 建立主選單，內容為子選單
filemenu.configure()

root.config(menu=menubar)             # 主視窗加入主選單

root.resizable(False, False)
value_initialization()
root.mainloop()