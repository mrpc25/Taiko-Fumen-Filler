import predict_model as pm
import taiko

SEQ = pm.SEQ
DisplayBarNumber = True

class fumen_info_before_start:
    def __init__(self, song_branched:taiko.TaikoFumenBranched, input_level, input_course):
        TempContent = song_branched.OffsetThingsValue("BPM:",[song_branched.ChosenReady,song_branched.ChosenBegin]) #預設使用譜面開始前設定的BPM
        OFFSETString = song_branched.OffsetThingsValue("OFFSET:", [0, song_branched.Song_Begin[0]])

        self.TITLE = song_branched.TITLE
        self.SUBTITLE = song_branched.OffsetThingsValue_PareIgnored("SUBTITLE:",[0,len(song_branched.EveryRow)])
        self.DEMOSTART = song_branched.OffsetThingsValue("DEMOSTART:",[0,len(song_branched.EveryRow)])
        self.INIT_BPM = song_branched.OffsetThingsValue("BPM:",[0, song_branched.Song_Begin[0]]) if TempContent=="" else TempContent
        self.WAVE = song_branched.OffsetThingsValue_PareIgnored("WAVE:",[0,len(song_branched.EveryRow)])
        self.OFFSET = 0 if OFFSETString=='' else float(OFFSETString)
        self.LEVEL = input_level
        self.COURSE = input_course

def fumen_filling(song_branched:taiko.TaikoFumenBranched, OFFSET, MODEL_PATH, DisplayBarNumber, fumen_basic_info_pack:fumen_info_before_start):
    
    #印出結果
    TempContent = song_branched.OffsetThingsValue("BPM:",[song_branched.ChosenReady,song_branched.ChosenBegin]) #預設使用譜面開始前設定的BPM
    if(TempContent==""): TempContent = song_branched.OffsetThingsValue("BPM:",[0, song_branched.Song_Begin[0]]) #沒有該譜面自設定的BPM，則沿用譜面檔案一開始能找到的數值

    songvol_text = song_branched.OffsetThingsValue_PareIgnored("SONGVOL:",[0,len(song_branched.EveryRow)])
    sevol_test = song_branched.OffsetThingsValue_PareIgnored("SEVOL:",[0,len(song_branched.EveryRow)])

    TITLE = fumen_basic_info_pack.TITLE
    SUBTITLE = fumen_basic_info_pack.SUBTITLE
    DEMOSTART = fumen_basic_info_pack.DEMOSTART
    INIT_BPM = fumen_basic_info_pack.INIT_BPM
    WAVE = fumen_basic_info_pack.WAVE
    LEVEL = fumen_basic_info_pack.LEVEL
    COURSE = fumen_basic_info_pack.COURSE
    SONGVOL = "100" if songvol_text=="" else songvol_text
    SEVOL = "100" if sevol_test=="" else sevol_test

    _bpm = float(TempContent)
    _scr = 1
    _measure = [4, 4]
    _barline = True
    _gogo = False
    _note = None

    set_bpm = song_branched.BPMValueSet
    set_scr = song_branched.ScrollSet
    set_measure = song_branched.BeatsToMeasureSet
    set_barline = song_branched.BarlineSet
    set_gogo = song_branched.GOGOSet
    set_delay = song_branched.DelaySet

    Remastered_fumen_info = ""
    Remastered_fumen_context = ""

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

    Remastered_fumen_context += "#START\n"

    #Actual Fumen Context
    for bar, bar_bpm, bar_scr, bar_measure, bar_barline, bar_gogo, bar_delay in zip(song_branched.EveryBar, set_bpm, set_scr, set_measure, set_barline, set_gogo, set_delay):
        for note, bpm, scr, measure, barline, gogo, delay in zip(bar, bar_bpm, bar_scr, bar_measure, bar_barline, bar_gogo, bar_delay):
            IsCommandChange = True if (_bpm, _scr, _measure, _barline, _gogo) != (bpm, scr, measure, barline, gogo) else False
            #如果現在有指令的話，會在開頭自動加上一次換行。而如果上一個位置就是小節結束點(換行)，那就省掉上一次加的換行
            if( IsCommandChange and ( _note == "," or _note is None ) ):  Remastered_fumen_context = Remastered_fumen_context[:-1]
            if(_bpm!=bpm):
                _bpm = bpm
                Remastered_fumen_context = Remastered_fumen_context + f"\n#BPMCHANGE {bpm}"
            if(_scr!=scr):
                _scr = scr
                Scroll_text = str(scr.real) if (scr.imag==0) else f"{scr.real}+{scr.imag}i"
                Remastered_fumen_context = Remastered_fumen_context + f"\n#SCROLL {Scroll_text}"
            if(_measure!=measure):
                _measure = measure
                Remastered_fumen_context = Remastered_fumen_context + f"\n#MEASURE {measure[0]}/{measure[1]}"
            if(_barline!=barline):
                _barline = barline
                Barline_text = "#BARLINEON" if barline else "#BARLINEOFF"
                Remastered_fumen_context = Remastered_fumen_context + f"\n{Barline_text}"
            if(_gogo!=gogo):
                _gogo = gogo
                GOGO_text = "#GOGOSTART" if gogo else "#GOGOEND"
                Remastered_fumen_context = Remastered_fumen_context + f"\n{GOGO_text}"
            if(delay!=0):
                Remastered_fumen_context = Remastered_fumen_context + f"\n#DELAY {delay}\n"

            Extra_Newline = "\n" if IsCommandChange else ""
            if(_note=="5" and note=="0"): note = "8"        #Visible Only When Using Roll Considered Version
            Remastered_fumen_context = Remastered_fumen_context + Extra_Newline + note

            _note = note

        Remastered_fumen_context = Remastered_fumen_context + "\n"

    Remastered_fumen_context = Remastered_fumen_context + "#END"

    #Add Bar Number
    if int(DisplayBarNumber)==1:
      Remastered_fumen_with_bar = ""
      bar = 0
      for char in Remastered_fumen_context:
        Remastered_fumen_with_bar = Remastered_fumen_with_bar + char
        if char==",":
          bar = bar + 1
          Remastered_fumen_with_bar = Remastered_fumen_with_bar + f"//{bar}"
      Remastered_fumen_context = Remastered_fumen_with_bar

    #Model Used
    Remastered_fumen_context = Remastered_fumen_context + f"\n\n//Sequence Length: {SEQ}\n//Model Used:\n//{MODEL_PATH}"

    return Remastered_fumen_info + Remastered_fumen_context

if __name__=='__main__':
    print(f"This is not main script of the entire application, if GUI is needed, run \"interface_multi.py\".")