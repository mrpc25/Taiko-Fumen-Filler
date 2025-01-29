import librosa
import numpy as np

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

import time

def Reduced_file_path(Og_path):
    New = ""
    for char in Og_path:
        New = New + char if (char!="/") else "" #一遇到"/"，就代表真實檔案名稱還在後面，所以清空並再紀錄。
    return New

def File_Path_Only_Directory(path):
    if "/" not in path: return ""
    while(path[-1]!="/" and len(path)>0): path = path.rstrip(path[-1])
    return path

root = tk.Tk()
root.title('Empty Fumen Generator')

width = 300
height = 300
left = root.winfo_screenwidth() // 4
top = root.winfo_screenheight() // 4
root.geometry(f'{width}x{height}+{left}+{top}')  # 定義視窗的尺寸和位置

X_OFFSET = 0.02
X_SHIFT = 0
Y_OFFSET = 0.11
Y_SHIFT = 0.08
current_audio_selected = False

TITLE_text = tk.Label(root, text="TITLE")
TITLE_text.place(relx=0.02, rely=Y_OFFSET, anchor='w')
TITLE_value = tk.StringVar()
TITLE_value_display = tk.Entry(root, textvariable=TITLE_value, width=34, state='normal')
TITLE_value_display.place(relx=0.96, rely=Y_OFFSET, anchor='e')

SUBTITLE_text = tk.Label(root, text="SUBTITLE")
SUBTITLE_text.place(relx=0.02, rely=Y_OFFSET+1*Y_SHIFT, anchor='w')
SUBTITLE_value = tk.StringVar()
SUBTITLE_value.set("--")
SUBTITLE_value_display = tk.Entry(root, textvariable=SUBTITLE_value, width=22, state='normal')
SUBTITLE_value_display.place(relx=0.755, rely=Y_OFFSET+1*Y_SHIFT, anchor='e')

WAVE_text = tk.Label(root, text="WAVE")
WAVE_text.place(relx=0.02, rely=Y_OFFSET+2*Y_SHIFT, anchor='w')
WAVE_value = tk.StringVar()
WAVE_value_display = tk.Entry(root, textvariable=WAVE_value, width=25, state='normal')
WAVE_value_display.place(relx=0.755, rely=Y_OFFSET+2*Y_SHIFT, anchor='e')

BPM_text = tk.Label(root, text="BPM")
BPM_text.place(relx=0.02, rely=Y_OFFSET+3*Y_SHIFT, anchor='w')
BPM_value = tk.StringVar()
BPM_value_display = tk.Entry(root, textvariable=BPM_value, width=11, state='normal', justify='center')
BPM_value_display.place(relx=0.405, rely=Y_OFFSET+3*Y_SHIFT, anchor='e')

OFFSET_text = tk.Label(root, text="OFFSET")
OFFSET_text.place(relx=0.425, rely=Y_OFFSET+3*Y_SHIFT, anchor='w')
OFFSET_value_List = ttk.Combobox(root, width=12, height=10, values=[], justify='center', state="active")
OFFSET_value_List.place(relx=0.96, rely=Y_OFFSET+3*Y_SHIFT, anchor='e')

COURSE_text = tk.Label(root, text="COURSE")
COURSE_text.place(relx=0.02, rely=Y_OFFSET+4*Y_SHIFT, anchor='w')
COURSE_value = tk.StringVar()
COURSE_value.set(3)
COURSE_value_display = tk.Entry(root, textvariable=COURSE_value, width=10, state='normal', justify='center')
COURSE_value_display.place(relx=0.45, rely=Y_OFFSET+4*Y_SHIFT, anchor='e')

LEVEL_text = tk.Label(root, text="LEVEL")
LEVEL_text.place(relx=0.452, rely=Y_OFFSET+4*Y_SHIFT, anchor='w')
LEVEL_value = tk.StringVar()
LEVEL_value.set(8)
LEVEL_value_display = tk.Entry(root, textvariable=LEVEL_value, width=15, state='normal', justify='center')
LEVEL_value_display.place(relx=0.96, rely=Y_OFFSET+4*Y_SHIFT, anchor='e')

SONGVOL_text = tk.Label(root, text="SONGVOL")
SONGVOL_text.place(relx=0.02, rely=Y_OFFSET+5*Y_SHIFT, anchor='w')
SONGVOL_value = tk.StringVar()
SONGVOL_value.set(100)
SONGVOL_value_display = tk.Entry(root, textvariable=SONGVOL_value, width=8, state='normal', justify='center')
SONGVOL_value_display.place(relx=0.03, rely=Y_OFFSET+6*Y_SHIFT, anchor='w')

SEVOL_text = tk.Label(root, text="SEVOL")
SEVOL_text.place(relx=0.25, rely=Y_OFFSET+5*Y_SHIFT, anchor='w')
SEVOL_value = tk.StringVar()
SEVOL_value.set(100)
SEVOL_value_display = tk.Entry(root, textvariable=SEVOL_value, width=6, state='normal', justify='center')
SEVOL_value_display.place(relx=0.25, rely=Y_OFFSET+6*Y_SHIFT, anchor='w')

SCOREINIT_text = tk.Label(root, text="ScoreInit")
SCOREINIT_text.place(relx=0.432, rely=Y_OFFSET+5*Y_SHIFT, anchor='w')
SCOREINIT_value = tk.StringVar()
SCOREINIT_value_display = tk.Entry(root, textvariable=SCOREINIT_value, width=8, state='normal', justify='center')
SCOREINIT_value_display.place(relx=0.425, rely=Y_OFFSET+6*Y_SHIFT, anchor='w')

SCOREDIFF_text = tk.Label(root, text="ScoreDiff")
SCOREDIFF_text.place(relx=0.645, rely=Y_OFFSET+5*Y_SHIFT, anchor='w')
SCOREDIFF_value = tk.StringVar()
SCOREDIFF_value_display = tk.Entry(root, textvariable=SCOREDIFF_value, width=8, state='normal', justify='center')
SCOREDIFF_value_display.place(relx=0.645, rely=Y_OFFSET+6*Y_SHIFT, anchor='w')

SIDE_text = tk.Label(root, text="Side")
SIDE_text.place(relx=0.962, rely=Y_OFFSET+5*Y_SHIFT, anchor='e')
SIDE_value = tk.StringVar()
SIDE_value_display = tk.Entry(root, textvariable=SIDE_value, width=4, state='normal', justify='center')
SIDE_value_display.place(relx=0.965, rely=Y_OFFSET+6*Y_SHIFT, anchor='e')

DEMOSTART_text = tk.Label(root, text="DEMOSTART")
DEMOSTART_text.place(relx=0.02, rely=Y_OFFSET+7*Y_SHIFT, anchor='w')
DEMOSTART_value_List = ttk.Combobox(root, width=9, height=10, values=[], justify='center', state="active")
DEMOSTART_value_List.place(relx=0.3, rely=Y_OFFSET+7*Y_SHIFT, anchor='w')

SCOREMODE_text = tk.Label(root, text="SCOREMODE")
SCOREMODE_text.place(relx=0.6, rely=Y_OFFSET+7*Y_SHIFT, anchor='w')
SCOREMODE_value = tk.StringVar()
SCOREMODE_value_display = tk.Entry(root, textvariable=SCOREMODE_value, width=3, state='normal', justify='center')
SCOREMODE_value_display.place(relx=0.965, rely=Y_OFFSET+7*Y_SHIFT, anchor='e')

def AudioSelected():
    global tempo
    global beat_times
    global audio_path
    global current_audio_selected

    audio_path = filedialog.askopenfilename(filetypes=[("Select Audio File", '*')])
    current_audio_selected = audio_path!=""
    if not current_audio_selected: return
    audio_file_name = Reduced_file_path(audio_path)
    WAVE_value.set(audio_file_name)

    if Auto_needed.get()=="0": return

    last = time.time()
    print(f"Loading File \"{audio_file_name}\"...",end="")
    WAVEFORM, SR = librosa.load(audio_path)
    print(f" ({round((time.time()-last)*100)/100}s)")
    last = time.time()
    print(f"Analyzing Audio...",end="")
    tempo, beat_frames = librosa.beat.beat_track(y=WAVEFORM, sr=SR)
    beat_times = librosa.frames_to_time(beat_frames, sr=SR)
    print(f" ({round((time.time()-last)*100)/100}s)")
    last = time.time()
    print(f"Finished")

    global BPM_value
    global OFFSET_value_List
    global DEMOSTART_value_List

    auto_offset_list = -np.round(beat_times,5)
    BPM_value.set(round(tempo[0],3))
    OFFSET_value_List.configure(values=auto_offset_list)
    OFFSET_value_List.set(auto_offset_list[0])
    DEMOSTART_value_List.configure(values=auto_offset_list)

    global audio_length
    audio_length = len(WAVEFORM)/SR

    SetNumberOfBar()

def SetNumberOfBar():
    global MEASURE_value_List
    global BAR_NUM_value
    global audio_length
    try:
        beat_to_measure = MEASURE_value_List.get().split("/")
        BEAT = int(beat_to_measure[0])
        MEASURE = int(beat_to_measure[1])
        assert BEAT>0 and MEASURE>0
    except:
        raise Exception(f"Invaild measure input. ({MEASURE_value_List.get()})")
    bar_numer = int((audio_length - beat_times[0]) / (60 / float(BPM_value.get()) * 4 * ( BEAT / MEASURE ) ) )
    BAR_NUM_value.set(bar_numer)

Auto_needed = tk.StringVar()
Auto_needed_btn = tk.Checkbutton(root, text='AUTO', variable=Auto_needed, onvalue=1, offvalue=0, state='normal')
Auto_needed_btn.place(relx=0.97, rely=Y_OFFSET+1*Y_SHIFT, anchor='e')
Auto_needed_btn.select()

SelectAudio_btn = tk.Button(root, text="SELECT" , width=7, command=AudioSelected, height=1, justify='center')
SelectAudio_btn.place(relx=0.96, rely=Y_OFFSET+2*Y_SHIFT, anchor='e')

basic_information_text = tk.Label(root, text="Beforehand Information")
basic_information_text.place(relx=0.5, rely=Y_OFFSET-0.85*Y_SHIFT, relwidth=0.96, anchor='center')
separator_1 = ttk.Separator(root, orient='horizontal')
separator_1.place(relx=0.5, rely=Y_OFFSET+7.75*Y_SHIFT, relwidth=0.96, anchor='center')

inner_context_text = tk.Label(root, text="Inner Context")
inner_context_text.place(relx=0.5, rely=Y_OFFSET+8.2*Y_SHIFT, relwidth=0.96, anchor='center')

def Consider_new_selected_measure(event):
    if Auto_needed.get()=="0": return
    SetNumberOfBar()

def Consider_new_entered_measure(event):
    if Auto_needed.get()=="0": return
    SetNumberOfBar()

def Consider_new_measure(event):
    global current_audio_selected
    if Auto_needed.get()=="0" or (not current_audio_selected): return
    SetNumberOfBar()

MEASURE_text = tk.Label(root, text="MEASURE")
MEASURE_text.place(relx=0.02, rely=Y_OFFSET+9.1*Y_SHIFT, anchor='w')
MEASURE_value = tk.StringVar()
MEASURE_value_List = ttk.Combobox(root, width=5, height=10, values=["4/4", "3/4", "6/4", "2/4", "5/4", "12/8", "8/8", "6/8", "3/8"], justify='center', state="active")
MEASURE_value_List.set("4/4")
MEASURE_value_List.place(relx=0.03, rely=Y_OFFSET+10.2*Y_SHIFT, anchor='w')
MEASURE_value_List.bind("<<ComboboxSelected>>", Consider_new_measure)
MEASURE_value_List.bind("<Return>",Consider_new_measure) 

BAR_NOTE_text = tk.Label(root, text="Note/Bar")
BAR_NOTE_text.place(relx=0.25, rely=Y_OFFSET+9.1*Y_SHIFT, anchor='w')
BAR_NOTE_value = tk.StringVar()
BAR_NOTE_value.set(16)
BAR_NOTE_value_display = tk.Entry(root, textvariable=BAR_NOTE_value, width=8, state='normal', justify='center')
BAR_NOTE_value_display.place(relx=0.25, rely=Y_OFFSET+10.2*Y_SHIFT, anchor='w')

BAR_NUM_text = tk.Label(root, text="Number of Bar")
BAR_NUM_text.place(relx=0.47, rely=Y_OFFSET+9.1*Y_SHIFT, anchor='w')
BAR_NUM_value = tk.StringVar()
BAR_NUM_value_display = tk.Entry(root, textvariable=BAR_NUM_value, width=12, state='normal', justify='center')
BAR_NUM_value_display.place(relx=0.47, rely=Y_OFFSET+10.2*Y_SHIFT, anchor='w')


def fumen_generating():
    if Auto_needed.get()=="0": return

    Remastered_fumen_info = ""
    Remastered_fumen_context = ""

    TITLE = TITLE_value.get()
    SUBTITLE = SUBTITLE_value.get()
    DEMOSTART = DEMOSTART_value_List.get()
    INIT_BPM = BPM_value.get()
    WAVE = WAVE_value.get()
    OFFSET = OFFSET_value_List.get()
    LEVEL = LEVEL_value.get()
    COURSE = COURSE_value.get()

    SONGVOL = SONGVOL_value.get()
    SEVOL = SEVOL_value.get()
    SCOREINIT = SCOREINIT_value.get()
    SCOREDIFF = SCOREDIFF_value.get()
    SIDE = SIDE_value.get()

    #Basic Info
    Remastered_fumen_info += f"TITLE:{TITLE}\n"
    Remastered_fumen_info += f"SUBTITLE:{SUBTITLE}\n"
    Remastered_fumen_info += f"BPM:{INIT_BPM}\n"
    Remastered_fumen_info += f"WAVE:{WAVE}\n"
    Remastered_fumen_info += f"OFFSET:{OFFSET}\n"
    Remastered_fumen_info += f"LEVEL:{LEVEL}\n"
    Remastered_fumen_info += f"COURSE:{COURSE}\n"
    Remastered_fumen_info += f"DEMOSTART:{DEMOSTART}\n"
    Remastered_fumen_info += f"SONGVOL:{SONGVOL}\n"
    Remastered_fumen_info += f"SEVOL:{SEVOL}\n"
    Remastered_fumen_info += f"SCOREINIT:{SCOREINIT}\n"
    Remastered_fumen_info += f"SCOREDIFF:{SCOREDIFF}\n"
    Remastered_fumen_info += f"SIDE:{SIDE}\n"

    beat_to_measure = MEASURE_value_List.get()
    [beat, measure] = beat_to_measure.split("/")
    beat, measure = int(beat), int(measure)

    notes_per_bar = int(BAR_NOTE_value.get())
    beat_in_bar = [int(index/measure*notes_per_bar) for index in range(beat) ]
    CONTEXT_PER_BAR = ""
    for note_order in range(notes_per_bar):
        CONTEXT_PER_BAR += "1" if note_order in beat_in_bar else "0"
    CONTEXT_PER_BAR+=",\n"

    Remastered_fumen_context += "#START\n"

    if beat_to_measure!="4/4":
        Remastered_fumen_context += f"#MEASURE {MEASURE_value_List.get()}"
    Remastered_fumen_context += CONTEXT_PER_BAR*int(BAR_NUM_value.get())

    Remastered_fumen_context += "#END"

    global Remastered_fumen
    Remastered_fumen = Remastered_fumen_info + Remastered_fumen_context

def SaveFile():
    global audio_path
    save_path = filedialog.asksaveasfilename(filetypes=[("Save fumen", '*.tja')], initialdir=File_Path_Only_Directory(audio_path))
    
    if save_path=="": return
    if not save_path.endswith(".tja"): save_path = save_path + ".tja"

    with open(save_path, 'w', encoding="utf-8") as writer:
        writer.write(Remastered_fumen)

    messagebox.showinfo('showinfo', f"Succesfully Ouput As A File Called \"{Reduced_file_path(save_path)}\"")

Generate_btn = tk.Button(root, text="Generate" , width=7, command=fumen_generating, height=1, justify='center')
Generate_btn.place(relx=0.97, rely=Y_OFFSET+9.1*Y_SHIFT, anchor='e')

Save_btn = tk.Button(root, text="Save" , width=7, command=SaveFile, height=1, justify='center')
Save_btn.place(relx=0.97, rely=Y_OFFSET+10.2*Y_SHIFT, anchor='e')

root.resizable(False, False)
root.mainloop()