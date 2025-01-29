import predict_model as pm

import torch
import torchaudio
import torch.nn as nn

from tqdm import tqdm

import configparser

def ReadConfig(configpath,SECTION,KEY):
    config = configparser.ConfigParser()
    config.read(configpath, encoding="utf-8")
    return config[SECTION][KEY]

ASIDE_NOTE = pm.ASIDE_NOTE
device = pm.device

minimum_frequency = 0
maximum_frequency = 22050

assert minimum_frequency>=0 and maximum_frequency>0, "Frequency Must Not Be Negative."
assert minimum_frequency<maximum_frequency, "Minimum Frequency Must Be Smaller Than Maximum Frequency."

def AdjustPeriod(period):
    while(period>=4): period = period/2
    while(period<=1/4): period = period*2
    return period

#attention+CNN模型需要的共(2*ASIDE_NOTE+1)個連續時刻的spectogram輸入
#這裡採用每次都重算，會使用當下輪到的音符左右的所有時刻的spectogram（共2*ASIDE_NOTE+1個），並組合成模型輸入
def fumen_predicting_attention_cnn_original(Audio_path, LocationToNotes, BpmConfiguration, AbsoluteTime, TaikoModel, song_branched):
    #新的純CNN模型使用單聲道
    DUAL_CHANNEL = False
    CHANNRL = 2 if DUAL_CHANNEL else 1
    #ZERO_CHANNEL_TENSOR = torch.full((CHANNRL, 1), 0).to(device)

    FREQ_BINS = int(ReadConfig("config.ini","AUDIO","freqency_bin"))
    SEGMENT = int(ReadConfig("config.ini","AUDIO","segment"))
    SR_MODE = bool(int(ReadConfig("config.ini","AUDIO","real_sample_rate")))
    print(f"freq_bins:{FREQ_BINS}, segment:{SEGMENT}")
    SOUNDWAVE, SR = torchaudio.load(Audio_path)
    SOUNDWAVE = SOUNDWAVE.to(device)
    FRAMES_LENGTH = len(SOUNDWAVE[0])

    channel_num = (SOUNDWAVE.shape)[0]
    assert channel_num==1 or channel_num==2, "Number of channel is not valid, expect 1 or 2."
    if(channel_num==1 and DUAL_CHANNEL):      SOUNDWAVE = SOUNDWAVE.repeat(2, 1)                               #將單聲道轉為雙聲道
    if(channel_num==2 and not DUAL_CHANNEL):  SOUNDWAVE = torch.unsqueeze((SOUNDWAVE[0]+SOUNDWAVE[1])/2, 0)    #將雙聲道轉為單聲道
    
    predictResult = []
    predictBar = []
    for NOTE_INDEX in tqdm(range(len(LocationToNotes))):
        def SoundPartByFrame(NOTE_OFFSRT):
            loop_index = NOTE_INDEX + NOTE_OFFSRT
            if(loop_index<0 or loop_index>=len(LocationToNotes)):
              return torch.zeros(CHANNRL, FREQ_BINS, SEGMENT+1).to(device)

            location = LocationToNotes[loop_index]
            [BAR, NOTE] = location
            BPM = BpmConfiguration[BAR][NOTE]
            PERIOD = AdjustPeriod(60 / BPM * 2)
            SHAPE = int(PERIOD*SEGMENT+1)

            EXACT_TIME = AbsoluteTime[loop_index]-PERIOD/2
            STARTING_FRAME = int(EXACT_TIME*SR)
            DURATION_FRAME = int(PERIOD*SR)
            #起始點是否在音樂開始前 / 起始點是否在音樂開始後 / 終止點是否在音樂開始前 / 終止點是否在音樂結束後
            IS_START_OUT_OF_MIN_INDEX = False if (STARTING_FRAME>=0) else True
            IS_START_OUT_OF_MAX_INDEX = False if (STARTING_FRAME<FRAMES_LENGTH) else True
            IS_FINAL_OUT_OF_NIN_INDEX = False if (STARTING_FRAME+DURATION_FRAME>=0) else True
            IS_FINAL_OUT_OF_NAX_INDEX = False if (STARTING_FRAME+DURATION_FRAME<FRAMES_LENGTH) else True

            assert not(IS_START_OUT_OF_MIN_INDEX and IS_START_OUT_OF_MAX_INDEX), f"The Start Window being Out Of Start/End point At The Same Time Doesn't Make Sense."
            assert not(IS_FINAL_OUT_OF_NIN_INDEX and IS_FINAL_OUT_OF_NAX_INDEX), f"The Final Window being Out Of Start/End point At The Same Time Doesn't Make Sense."

            match IS_START_OUT_OF_MIN_INDEX, IS_START_OUT_OF_MAX_INDEX, IS_FINAL_OUT_OF_NIN_INDEX, IS_FINAL_OUT_OF_NAX_INDEX:
                case False  , False , _     , False : #正常情況
                    SLICE = SOUNDWAVE[:, STARTING_FRAME: STARTING_FRAME+DURATION_FRAME]
                case True   , False , False , False : #開頭超出音樂開頭處，結尾則在音樂內
                    SLICE = SOUNDWAVE[:, 0: STARTING_FRAME+DURATION_FRAME]
                    RESIDUE_TENSOR = torch.zeros(CHANNRL, DURATION_FRAME-len(SLICE[0])).to(device)
                    SLICE = torch.cat((RESIDUE_TENSOR, SLICE), dim=1)
                case True   , False , True , False : #開頭和結尾都超出音樂開頭處
                    SLICE = torch.zeros(CHANNRL, DURATION_FRAME).to(device)
                case False  , False , _    , True  : #結尾超出音樂結束處，開頭則在音樂內
                    SLICE = SOUNDWAVE[:, STARTING_FRAME: FRAMES_LENGTH]
                    RESIDUE_TENSOR = torch.zeros(CHANNRL, DURATION_FRAME-len(SLICE[0])).to(device)
                    SLICE = torch.cat((SLICE, RESIDUE_TENSOR), dim=1)
                case False  , True  , _    , True  : #開頭跟結尾都已經在整首音樂結束後了
                    SLICE = torch.zeros(CHANNRL, DURATION_FRAME).to(device)
                case True   , _     , _    , True  : #不合理的情況，起始點在音樂開始前，終止點在音樂結束後
                    raise Exception(f"Chosen Segment Is Less Then {PERIOD}s.")

            to_mel_spectrogram = torchaudio.transforms.MelSpectrogram(
                sample_rate = SR if SR_MODE else DURATION_FRAME,   
                n_fft = 1024,   
                n_mels = FREQ_BINS,
                hop_length = int( DURATION_FRAME / SEGMENT ),
                f_min = minimum_frequency,      
                f_max = maximum_frequency,  
                normalized = True).to(device)

            log_mel_spec = to_mel_spectrogram(SLICE)
            return log_mel_spec

        info_per_note = []
        for aside_from_center in range(-ASIDE_NOTE, ASIDE_NOTE+1):
            info_per_note.append(SoundPartByFrame(aside_from_center))
        info_per_note = torch.stack(info_per_note)

        with torch.inference_mode():
          Result = TaikoModel(torch.unsqueeze(info_per_note, 0).to(device))
          Result = torch.squeeze(Result)
        predictResult.append(Result)
        predictBar.append(Result.argmax().item())
    
    for x, y in zip(LocationToNotes, predictBar): song_branched.EveryBar[x[0]] = song_branched.EveryBar[x[0]][:x[1]] + str(y) + song_branched.EveryBar[x[0]][x[1]+1:]
    return song_branched, predictResult

#attention+CNN模型需要的共(2*ASIDE_NOTE+1)個連續時刻的spectogram書入 (20250125更新)
#這裡採用先初始化第一顆音符前的spectogram組合輸入（也可以說假設成第0個位置），再根據當下輪到的音符，依序推入ASIDE_NOTE時刻後的音符的spectogram，並移除首相，組合成當下的模型輸入
def fumen_predicting_attention_cnn_modified(Audio_path, LocationToNotes, BpmConfiguration, AbsoluteTime, TaikoModel, song_branched):
    #新的純CNN模型使用單聲道
    DUAL_CHANNEL = False
    CHANNRL = 2 if DUAL_CHANNEL else 1
    #ZERO_CHANNEL_TENSOR = torch.full((CHANNRL, 1), 0).to(device)

    FREQ_BINS = int(ReadConfig("config.ini","AUDIO","freqency_bin"))
    SEGMENT = int(ReadConfig("config.ini","AUDIO","segment"))
    SR_MODE = bool(int(ReadConfig("config.ini","AUDIO","real_sample_rate")))
    print(f"freq_bins:{FREQ_BINS}, segment:{SEGMENT}")
    SOUNDWAVE, SR = torchaudio.load(Audio_path)
    SOUNDWAVE = SOUNDWAVE.to(device)
    FRAMES_LENGTH = len(SOUNDWAVE[0])

    channel_num = (SOUNDWAVE.shape)[0]
    assert channel_num==1 or channel_num==2, "Number of channel is not valid, expect 1 or 2."
    if(channel_num==1 and DUAL_CHANNEL):      SOUNDWAVE = SOUNDWAVE.repeat(2, 1)                               #將單聲道轉為雙聲道
    if(channel_num==2 and not DUAL_CHANNEL):  SOUNDWAVE = torch.unsqueeze((SOUNDWAVE[0]+SOUNDWAVE[1])/2, 0)    #將雙聲道轉為單聲道
    
    predictResult = []
    predictBar = []
    
    def SoundPartByNote(NOTE_INDEX):
        if(NOTE_INDEX<0 or NOTE_INDEX>=len(LocationToNotes)):
            return torch.zeros(CHANNRL, FREQ_BINS, SEGMENT+1).to(device)
        
        [BAR, NOTE] = LocationToNotes[NOTE_INDEX]
        BPM = BpmConfiguration[BAR][NOTE]
        PERIOD = AdjustPeriod(60 / BPM * 2)
        SHAPE = int(PERIOD*SEGMENT+1)

        EXACT_TIME = AbsoluteTime[NOTE_INDEX]-PERIOD/2
        STARTING_FRAME = int(EXACT_TIME*SR)
        DURATION_FRAME = int(PERIOD*SR)
        #起始點是否在音樂開始前 / 起始點是否在音樂開始後 / 終止點是否在音樂開始前 / 終止點是否在音樂結束後
        IS_START_OUT_OF_MIN_INDEX = False if (STARTING_FRAME>=0) else True
        IS_START_OUT_OF_MAX_INDEX = False if (STARTING_FRAME<FRAMES_LENGTH) else True
        IS_FINAL_OUT_OF_NIN_INDEX = False if (STARTING_FRAME+DURATION_FRAME>=0) else True
        IS_FINAL_OUT_OF_NAX_INDEX = False if (STARTING_FRAME+DURATION_FRAME<FRAMES_LENGTH) else True

        assert not(IS_START_OUT_OF_MIN_INDEX and IS_START_OUT_OF_MAX_INDEX), f"The Start Window being Out Of Start/End point At The Same Time Doesn't Make Sense."
        assert not(IS_FINAL_OUT_OF_NIN_INDEX and IS_FINAL_OUT_OF_NAX_INDEX), f"The Final Window being Out Of Start/End point At The Same Time Doesn't Make Sense."

        match IS_START_OUT_OF_MIN_INDEX, IS_START_OUT_OF_MAX_INDEX, IS_FINAL_OUT_OF_NIN_INDEX, IS_FINAL_OUT_OF_NAX_INDEX:
            case False  , False , _     , False : #正常情況
                SLICE = SOUNDWAVE[:, STARTING_FRAME: STARTING_FRAME+DURATION_FRAME]
            case True   , False , False , False : #開頭超出音樂開頭處，結尾則在音樂內
                SLICE = SOUNDWAVE[:, 0: STARTING_FRAME+DURATION_FRAME]
                RESIDUE_TENSOR = torch.zeros(CHANNRL, DURATION_FRAME-len(SLICE[0])).to(device)
                SLICE = torch.cat((RESIDUE_TENSOR, SLICE), dim=1)
            case True   , False , True , False : #開頭和結尾都超出音樂開頭處
                SLICE = torch.zeros(CHANNRL, DURATION_FRAME).to(device)
            case False  , False , _    , True  : #結尾超出音樂結束處，開頭則在音樂內
                SLICE = SOUNDWAVE[:, STARTING_FRAME: FRAMES_LENGTH]
                RESIDUE_TENSOR = torch.zeros(CHANNRL, DURATION_FRAME-len(SLICE[0])).to(device)
                SLICE = torch.cat((SLICE, RESIDUE_TENSOR), dim=1)
            case False  , True  , _    , True  : #開頭跟結尾都已經在整首音樂結束後了
                SLICE = torch.zeros(CHANNRL, DURATION_FRAME).to(device)
            case True   , _     , _    , True  : #不合理的情況，起始點在音樂開始前，終止點在音樂結束後
                raise Exception(f"Chosen Segment Is Less Then {PERIOD}s.")
            
        to_mel_spectrogram = torchaudio.transforms.MelSpectrogram(
                sample_rate = SR if SR_MODE else DURATION_FRAME,   
                n_fft = 1024,   
                n_mels = FREQ_BINS,
                hop_length = int( DURATION_FRAME / SEGMENT ),
                f_min = minimum_frequency,      
                f_max = maximum_frequency,  
                normalized = True).to(device)
        
        log_mel_spec = to_mel_spectrogram(SLICE)
        return log_mel_spec
    
    #初始化第一個音符之前
    info_per_note = []
    #[] -> [empty empty ... empty *empty*]
    for _ in range(ASIDE_NOTE+1): 
        info_per_note.append(torch.zeros(CHANNRL, FREQ_BINS, SEGMENT+1).to(device))
    # [empty empty ... empty empty] -> [empty empty ... empty *empty* note1 ... note (AN-1) note AN]
    for initial_index in range(ASIDE_NOTE):
        info_per_note.append(SoundPartByNote(initial_index))
        
    for NOTE_INDEX in tqdm(range(len(LocationToNotes))):
        APPEND_INDEX = NOTE_INDEX + ASIDE_NOTE
        appended_part = SoundPartByNote(APPEND_INDEX)

        #[note y note (y+1) ... note (x-1) *note x* note (x+1) ... note (z-1) note z] -> [note (y+1) note (y+2) ... note x *note (x+1)* note (x+2) ... note z note (z+1)]
        info_per_note.pop(0)
        info_per_note.append(appended_part)
        info_per_note_tensorized = torch.stack(info_per_note)

        with torch.inference_mode():
          Result = TaikoModel(torch.unsqueeze(info_per_note_tensorized, 0).to(device))
          Result = torch.squeeze(Result)
        predictResult.append(Result)
        predictBar.append(Result.argmax().item())
    
    for x, y in zip(LocationToNotes, predictBar): song_branched.EveryBar[x[0]] = song_branched.EveryBar[x[0]][:x[1]] + str(y) + song_branched.EveryBar[x[0]][x[1]+1:]
    return song_branched, predictResult

#舊的CNN模型，單純只對每個音符自己左右一個拍子內的聲音，處理成spectogram後直接作為輸入
def fumen_predicting_pure_cnn(Audio_path, LocationToNotes, BpmConfiguration, AbsoluteTime, TaikoModel, song_branched):
    #舊的純CNN模型使用雙聲道
    DUAL_CHANNEL = True
    CHANNRL = 2 if DUAL_CHANNEL else 1
    #ZERO_CHANNEL_TENSOR = torch.full((CHANNRL, 1), 0).to(device)

    FREQ_BINS = int(ReadConfig("config.ini","AUDIO","freqency_bin"))
    SEGMENT = int(ReadConfig("config.ini","AUDIO","segment"))
    SR_MODE = bool(int(ReadConfig("config.ini","AUDIO","real_sample_rate")))
    print(f"freq_bins:{FREQ_BINS}, segment:{SEGMENT}")
    SOUNDWAVE, SR = torchaudio.load(Audio_path)
    SOUNDWAVE = SOUNDWAVE.to(device)
    FRAMES_LENGTH = len(SOUNDWAVE[0])

    channel_num = (SOUNDWAVE.shape)[0]
    assert channel_num==1 or channel_num==2, "Number of channel is not valid, expect 1 or 2."
    if(channel_num==1 and DUAL_CHANNEL):      SOUNDWAVE = SOUNDWAVE.repeat(2, 1)                               #將單聲道轉為雙聲道
    #if(channel_num==2 and not DUAL_CHANNEL):  SOUNDWAVE = torch.unsqueeze((SOUNDWAVE[0]+SOUNDWAVE[1])/2, 0)    #將雙聲道轉為單聲道
    
    predictResult = []
    predictBar = []
    for NOTE_INDEX, location in enumerate(tqdm(LocationToNotes)):
        [BAR, NOTE] = location
        BPM = BpmConfiguration[BAR][NOTE]
        PERIOD = AdjustPeriod(60 / BPM * 2)
        SHAPE = int(PERIOD*SEGMENT+1)

        EXACT_TIME = AbsoluteTime[NOTE_INDEX]-PERIOD/2
        STARTING_FRAME = int(EXACT_TIME*SR)
        DURATION_FRAME = int(PERIOD*SR)

        #起始點是否在音樂開始前 / 起始點是否在音樂開始後 / 終止點是否在音樂開始前 / 終止點是否在音樂結束後
        IS_START_OUT_OF_MIN_INDEX = STARTING_FRAME < 0
        IS_START_OUT_OF_MAX_INDEX = STARTING_FRAME >= FRAMES_LENGTH
        IS_FINAL_OUT_OF_NIN_INDEX = STARTING_FRAME + DURATION_FRAME < 0
        IS_FINAL_OUT_OF_NAX_INDEX = STARTING_FRAME + DURATION_FRAME >= FRAMES_LENGTH

        assert not(IS_START_OUT_OF_MIN_INDEX and IS_START_OUT_OF_MAX_INDEX), f"The Start Window being Out Of Start/End point At The Same Time Doesn't Make Sense."
        assert not(IS_FINAL_OUT_OF_NIN_INDEX and IS_FINAL_OUT_OF_NAX_INDEX), f"The Final Window being Out Of Start/End point At The Same Time Doesn't Make Sense."

        match IS_START_OUT_OF_MIN_INDEX, IS_START_OUT_OF_MAX_INDEX, IS_FINAL_OUT_OF_NIN_INDEX, IS_FINAL_OUT_OF_NAX_INDEX:
            case False  , False , _     , False : #正常情況
                SLICE = SOUNDWAVE[:, STARTING_FRAME: STARTING_FRAME+DURATION_FRAME]
            case True   , False , False , False : #開頭超出音樂開頭處，結尾則在音樂內
                SLICE = SOUNDWAVE[:, 0: STARTING_FRAME+DURATION_FRAME]
                RESIDUE_TENSOR = torch.zeros(CHANNRL, DURATION_FRAME-len(SLICE[0])).to(device)
                SLICE = torch.cat((RESIDUE_TENSOR, SLICE), dim=1)
            case True   , False , True , False : #開頭和結尾都超出音樂開頭處
                SLICE = torch.zeros(CHANNRL, DURATION_FRAME).to(device)
            case False  , False , _    , True  : #結尾超出音樂結束處，開頭則在音樂內
                SLICE = SOUNDWAVE[:, STARTING_FRAME: FRAMES_LENGTH]
                RESIDUE_TENSOR = torch.zeros(CHANNRL, DURATION_FRAME-len(SLICE[0])).to(device)
                SLICE = torch.cat((SLICE, RESIDUE_TENSOR), dim=1)
            case False  , True  , _    , True  : #開頭跟結尾都已經在整首音樂結束後了
                SLICE = torch.zeros(CHANNRL, DURATION_FRAME).to(device)
            case True   , _     , _    , True  : #不合理的情況，起始點在音樂開始前，終止點在音樂結束後
                raise Exception(f"Chosen Segment Is Less Then {PERIOD}s.")

        to_mel_spectrogram = torchaudio.transforms.MelSpectrogram(
            sample_rate = SR if SR_MODE else DURATION_FRAME,   
            n_fft = 1024,   
            n_mels = FREQ_BINS,
            hop_length = int( DURATION_FRAME / SEGMENT ),
            f_min = minimum_frequency,      
            f_max = maximum_frequency,  
            normalized = True).to(device)

        log_mel_spec = to_mel_spectrogram(SLICE)

        with torch.inference_mode():
            Result = TaikoModel(torch.unsqueeze(log_mel_spec, 0)).to(device)
        predictResult.append(torch.squeeze(Result))
        predictBar.append(Result.argmax(dim=1).item())
    
    for x, y in zip(LocationToNotes, predictBar): song_branched.EveryBar[x[0]] = song_branched.EveryBar[x[0]][:x[1]] + str(y) + song_branched.EveryBar[x[0]][x[1]+1:]
    return song_branched, predictResult

#給出機率分布
softmax = nn.Softmax(dim=1)
def distribution_result_remake(LocationToNotes, predictResult):
    distribution = {}
    for location, result in zip(LocationToNotes, softmax(torch.stack(predictResult))):
        [BAR, NOTE] = location
        distribution[f"{BAR}/{NOTE}"] = result.tolist()
    return distribution

compute_set = {}
compute_set["240618"] = fumen_predicting_pure_cnn
compute_set["240804"] = fumen_predicting_attention_cnn_modified
compute_set["241025"] = fumen_predicting_attention_cnn_modified

if __name__=='__main__':
    print(f"This is not main script of the entire application, if GUI is needed, run \"interface_multi.py\".")