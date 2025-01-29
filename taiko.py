import configparser

def WriteConfig(configpath,SECTION,KEY,value):
    config = configparser.ConfigParser()
    config.read(configpath)
    config[SECTION][KEY] = value
    with open(configpath, 'w') as configfile:
        config.write(configfile)

def ReadConfig(configpath,SECTION,KEY):
    config = configparser.ConfigParser()
    config.read(configpath, encoding="utf-8")
    return config[SECTION][KEY]

class TaikoFumen():
    def __init__(self, Path, codec):
        with open(Path + "", mode='r' ,encoding = codec) as f:
            words_raw = f.read()

        #按行將原始檔案做切割
        EveryRow = []
        TempRow = ""
        for char in words_raw:
            if(char!="\n"):
                TempRow = TempRow + char
            else:
                EveryRow.append(TempRow)
                TempRow = ""
        EveryRow.append(TempRow)

        self.words_raw = words_raw
        self.EveryRow = EveryRow

        Command_BPMCHANGE_storage = ""
        Command_SCROLL_storage = ""
        Command_MEASURE_storage = ""
        Command_DELAY_storage = ""
        Command_BARLINE_storage = ""
        Command_GOGO_storage = ""

        new_EveryRow = []
        BranchEncounter = False

        def IsPhraseShowUpBeforeComma(phrase, rowindex):
          while("," not in EveryRow[rowindex]):
            if(phrase in EveryRow[rowindex]): return True
            rowindex = rowindex + 1
          return False

        for x in range(len(EveryRow)):
          row = EveryRow[x]

          if "#BPMCHANGE" in row: Command_BPMCHANGE_storage = row
          if "#SCROLL" in row: Command_SCROLL_storage = row
          if "#MEASURE" in row: Command_MEASURE_storage = row
          if "#DELAY" in row: Command_DELAY_storage = row
          if "#BARLUNE" in row: Command_BARLINE_storage = row
          if "#GOGO" in row: Command_GOGO_storage = row

          if "#BRANCHSTART" in row:
            BranchEncounter = True
            Command_BPMCHANGE_BeforeBranch = Command_BPMCHANGE_storage
            Command_SCROLL_BeforeBranch = Command_SCROLL_storage
            Command_MEASURE_BeforeBranch = Command_MEASURE_storage
            Command_DELAY_BeforeBranch = Command_DELAY_storage
            Command_BARLINE_BeforeBranch = Command_BARLINE_storage
            Command_GOGO_BeforeBranch = Command_GOGO_storage
          
          new_EveryRow.append(row)
          if BranchEncounter:
            if ("#N" in row) or ( ("#E" in row) and ("#END" not in row) ) or ( ("#M" in row) and ("#MEASURE" not in row) ):
              if ( Command_BPMCHANGE_BeforeBranch!="" ) and ( not IsPhraseShowUpBeforeComma("#BPMCHANGE", x) )  : new_EveryRow.append(Command_BPMCHANGE_BeforeBranch)
              if ( Command_SCROLL_BeforeBranch!="" )    and ( not IsPhraseShowUpBeforeComma("#SCROLL", x) )     : new_EveryRow.append(Command_SCROLL_BeforeBranch)
              if ( Command_MEASURE_BeforeBranch!="" )   and ( not IsPhraseShowUpBeforeComma("#MEASURE", x) )    : new_EveryRow.append(Command_MEASURE_BeforeBranch)
              if ( Command_DELAY_BeforeBranch!="" )     and ( not IsPhraseShowUpBeforeComma("#DELAY", x) )      : new_EveryRow.append(Command_DELAY_BeforeBranch)
              if ( Command_BARLINE_BeforeBranch!="" )   and ( not IsPhraseShowUpBeforeComma("#BARLUNE", x) )    : new_EveryRow.append(Command_BARLINE_BeforeBranch)
              if ( Command_GOGO_BeforeBranch!="" )      and ( not IsPhraseShowUpBeforeComma("#GOGO", x) )       : new_EveryRow.append(Command_GOGO_BeforeBranch)
              pass

          if "#END" in row:
          # if "#BRANCHEND" in row:
            Command_BPMCHANGE_storage = ""
            Command_SCROLL_storage = ""
            Command_MEASURE_storage = ""
            Command_DELAY_storage = ""
            Command_BARLINE_storage = ""
            Command_GOGO_storage = ""
            BranchEncounter = False

        EveryRow = new_EveryRow
        self.EveryRow = EveryRow

        #先尋找所有難度以及星級
        Song_Difficulty = self.FindPhraseInRow("COURSE:")
        Song_level = self.FindPhraseInRow("LEVEL:")

        Song_Begin = self.FindPhraseInRow("#START")
        Song_Endin = self.FindPhraseInRow("#END")

        assert len(Song_Begin)==len(Song_Endin), "The amount of \"#START(P1/2)\' and \"#END\" command is not equal, you might need to check if some necessary command was lost."
            
        self.Song_Begin = Song_Begin
        self.Song_Endin = Song_Endin

        self.FumanClassfication = []
        self.BasicInfoOverViewDict = []           #20240622 更新
        self.BasicInfoOverViewDictWithIndex = []  #20240622 更新

        #20240909 更新: 若同檔案超過一個譜面，則除了位於最上面的譜面以外，並不一定需要填進所有資訊，可以以預設資訊或先前資訊替代。
        _last_record_difficulty = "N/A"
        _last_record_side = "-"
        _last_record_level = "?"
        _last_record_style = ""

        #20240914 更新: 改動偵測譜面的方式，不再先區分是否含有雙人譜面。
        for i in range(len(Song_Begin)):
            if(i!=0):
                difficulty = self.OffsetThingsValue("COURSE:", [Song_Endin[i-1]+1, Song_Begin[i]])
                level = self.OffsetThingsValue("LEVEL:", [Song_Endin[i-1]+1, Song_Begin[i]])
                style = self.OffsetThingsValue("STYLE:", [Song_Endin[i-1]+1, Song_Begin[i]])
            else:
                difficulty = self.OffsetThingsValue("COURSE:", [0, Song_Begin[0]])
                level = self.OffsetThingsValue("LEVEL:", [0, Song_Begin[0]])
                style = self.OffsetThingsValue("STYLE:", [0, Song_Begin[0]])
            difficulty = difficulty.replace(" ", "")
            level = level.replace(" ", "")
            style = style.replace(" ", "")

            #20240909 更新:
            still_in_same_course = False
            match difficulty.lower():
                case "4"|"edit"  : difficulty = "Edit"
                case "3"|"oni"   : difficulty = "Oni"
                case "2"|"hard"  : difficulty = "Hard"
                case "1"|"normal": difficulty = "Normal"
                case "0"|"easy"  : difficulty = "Easy"
                case "": 
                  difficulty = _last_record_difficulty
                  still_in_same_course = True
                case _: raise Exception(f"difficulty not existed. (Input: \"{difficulty}\")")
            _last_record_difficulty = difficulty

            if level=="" : level = _last_record_level
            _last_record_level = level
                
            #20240622 更新:
            directness = self.OffsetThingsValue("SIDE:",[Song_Begin[i],Song_Begin[i]+1])
            directness = directness.replace(" ", "")
            match directness.lower():
                case "1"|"normal": side = "OUTSIDE"
                case "2"|"ex": side = "INSIDE"
                case "3": side = "-"
                case "": side = _last_record_side
                case _: raise Exception(f"Not a available side symbol, expect 1/2/3/None, (Input: \"{directness}\")")
            _last_record_side = side

            StringOfSTART = self.OffsetThingsValue("#START",[Song_Begin[i],Song_Begin[i]+1])
            dualstatestr = ""
            for x in StringOfSTART: #把偵測到的文字裡，只留下P/1/2三種（因為只有#START/#START P1/#START P2三種可能）
                if(x=="P" or x=="1" or x=="2"): dualstatestr = dualstatestr + x
            
            #20240914 更新:
            match dualstatestr:
               case "P1": dual = "P1"
               case "P2": dual = "P2"
               case "": dual = "-"
               case _: raise Exception(f"Invalid input for \"dualstatestr\". (input: {dualstatestr})")
            if style=="" and still_in_same_course: style = _last_record_style
            _last_record_style = style

            style_declaration = style.lower()=="double" or style=="2"
            extracted_dual_sign = dual=="P1" or dual=="P2"
            if (not style_declaration) and extracted_dual_sign : 
               raise Exception("Find that \"#START P1/2\" is written in file, but \"STYLE:\" section doesn't declare it's as a fumen for double player.")
            if style_declaration and (not extracted_dual_sign) :
               raise Exception("Find that double player mode is mentioned in \"STYLE:\" section, but \"#START P1/2\" is not written.")

            self.FumanClassfication.append([i, difficulty, dual, side, level])

            #20240622 更新:
            fumen_dict = {'difficulty':difficulty, 'dual':dual, 'side':side, 'level':level}
            self.BasicInfoOverViewDictWithIndex.append([i, fumen_dict])
            self.BasicInfoOverViewDict.append(fumen_dict)
        
        #20240914 更新: "IsAnyDual"不再作為必要的判斷過程後，轉而使用分類後的譜面資訊來判斷
        IsAnyDual = False
        for fumrn in self.BasicInfoOverViewDict:
           if(fumrn['dual']!="-"): 
              IsAnyDual = True
              break

        self.Song_Difficulty = Song_Difficulty
        self.Song_level = Song_level
        self.IsAnyDual = IsAnyDual


    #定義在指定的行內（範圍），是否有出現過特定文字，並輸出所有含有該特定文字的所在行數，形式是List
    def FindPhraseInRow(self, Phrase, Coverage=None):
        if(Coverage is None):
            Coverage = [0, len(self.EveryRow)]
        Order = []
        for i in range(Coverage[0],Coverage[1]):
            #20240909更新
            reference = self.EveryRow[i].find(Phrase)
            annotation = self.EveryRow[i].find("//")
            reference_exist = reference!=-1                           #確認目標的字眼到底在不在該行內
            annotation_exist = annotation!=-1                         #確認該行有沒有註解符號
            if (not annotation_exist) and reference_exist: Order.append(i)
            if annotation_exist and reference_exist and (reference < annotation): Order.append(i)

        return Order
    
    def FindPhraseInRowRev(self, Phrase, Coverage=None):
        if(Coverage is None):
            Coverage = [0, len(self.EveryRow)]
        Order = []
        for i in range(Coverage[0],Coverage[1]):
            if(self.EveryRow[i].rfind(Phrase)!=-1):
                Order.append(i)
        return Order
    
    #尋找特定字詞所在地，在那個字詞之後出現的字詞，並去除在註解符號"//"和"("後的部分
    def OffsetThingsValue(self,Phrase,Range):
        PhraseInRegion = self.FindPhraseInRow(Phrase,Range)
        output = ""
        if(len(PhraseInRegion)>0):
            Observed = self.EveryRow[PhraseInRegion[0]]
            Anno = Observed.find("//")
            lebr = Observed.find("(")
            if(Anno == -1 and lebr == -1):
                EndLocation = len(Observed)
            elif(Anno == -1):
                EndLocation = lebr
            elif(lebr == -1):
                EndLocation = Anno
            else:
                if(lebr<Anno):
                    EndLocation = lebr
                else:
                    EndLocation = Anno

            for i in range(Observed.find(Phrase)+len(Phrase),EndLocation):
                output = output + Observed[i]
        return output
    
    #尋找特定字詞所在地，在那個字詞之後出現的字詞，並去除在註解符號"//"後的部分（"("不受影響）。
    def OffsetThingsValue_PareIgnored(self,Phrase,Range):
      PhraseInRegion = self.FindPhraseInRow(Phrase,Range)
      output = ""
      if(len(PhraseInRegion)==0): return output
      Observed = self.EveryRow[PhraseInRegion[0]]
      Anno = Observed.find("//")
      EndLocation = len(Observed) if (Anno == -1) else Anno
      for i in range(Observed.find(Phrase)+len(Phrase),EndLocation): output = output + Observed[i]
      return output
    
    def abc(self):
        print("blablablaJustTesting")

class TaikoFumenInner(TaikoFumen):
    def __init__(self, Path, codec, UserChosenFumen):

        super().__init__(Path, codec)
        EveryBar = []          #每個小節的內容
        EveryBarRowLocation = []    #每個小節所在的行數(位置)
        CurrentMeasure = ""         #每次迴圈內暫存的小節內容
        CurrentMeasureRowLocation = []   #每次迴圈內暫存的小節位置

        if(UserChosenFumen>=0):
          if(UserChosenFumen==0):
            ChosenReady = 0
          else:
            ChosenReady = self.Song_Endin[UserChosenFumen-1]
          ChosenBegin = self.Song_Begin[UserChosenFumen]
          ChosenEndin = self.Song_Endin[UserChosenFumen]

        self.ChosenBegin = ChosenBegin
        self.ChosenEndin = ChosenEndin
        self.ChosenReady = ChosenReady

        for i in range(ChosenBegin+1,ChosenEndin):

            #檢查該小節是否有註解用的"//"符號，並記錄位置
            Annotation = self.EveryRow[i].find("//")

            #檢查該小節是否有譜面功能用的"#"符號，並記錄位置
            if(Annotation==-1):
                FunctionUsage = self.EveryRow[i].find("#")
            else:
                FunctionUsage = self.EveryRow[i].find("#", 0, Annotation)

            #判斷是否有使用函式"#"
            if(FunctionUsage==-1):
                for j in range(len(self.EveryRow[i])):
                    if(self.EveryRow[i][j]!=","):

                        #確認這一行文字中有沒有註解用的"//"
                        if(Annotation==-1):
                          #逐一檢視小節當中的字元，是數字就紀錄
                          if(str.isnumeric(self.EveryRow[i][j])):
                                #紀錄實際的字元
                                CurrentMeasure = CurrentMeasure + self.EveryRow[i][j]

                                #記錄這個字源所在的行
                                CurrentMeasureRowLocation.append(i)
                        else:
                          #逐一檢視小節當中的字元，是數字且是註解記號以前的文字就紀錄
                          if(str.isnumeric(self.EveryRow[i][j]) and j<Annotation):
                                #紀錄實際的字元
                                CurrentMeasure = CurrentMeasure + self.EveryRow[i][j]

                                #記錄這個字源所在的行
                                CurrentMeasureRowLocation.append(i)
                    else:
                        CurrentMeasure = CurrentMeasure + self.EveryRow[i][j]
                        CurrentMeasureRowLocation.append(i)

                        #小節結束時，暫時紀錄的str輸出到另外一個list，再讓暫時紀錄的str清空。
                        EveryBar.append(CurrentMeasure)
                        CurrentMeasure = ""

                        #小節結束時，暫時紀錄的str行位置輸出到另外一個list，再讓暫時紀錄清空。
                        EveryBarRowLocation.append(CurrentMeasureRowLocation)
                        CurrentMeasureRowLocation = []

        EveryBarWithoutComma = []
        for Bar in EveryBar:
          BarWithoutComma = ""
          for i in range(len(Bar)-1):
            BarWithoutComma = BarWithoutComma + Bar[i]
          EveryBarWithoutComma.append(BarWithoutComma)
        
        self.EveryBar = EveryBar

        #每個小節開始時在檔案內所位於的行數
        BarBeginLoaction = []
        temp = EveryBarRowLocation[0][0]
        BarBeginLoaction.append(temp)
        for bar in EveryBarRowLocation:
            for notesLocation in bar:
                if(notesLocation != temp):
                    temp = notesLocation
                    BarBeginLoaction.append(temp)

        temp = None
        BarLocation = []
        for bar in EveryBarRowLocation:
            #針對同一個小節，找出所有notes出現過的行數。
            NotesInBarLocation = []
            for notesLocation in bar:
                #紀錄同一個小節內的每個notes，是否有出現過不同的行數，有的話就做紀錄
                if(notesLocation != temp):
                    temp = notesLocation
                    NotesInBarLocation.append(temp)
            #記錄所有小節的結果
            BarLocation.append(NotesInBarLocation)
            
        self.BarBeginLoaction = BarBeginLoaction
        self.EveryBarRowLocation = EveryBarRowLocation

        #將譜面的所有資訊座儲存
        ScrollSet = self.Find_Scroll_Of_EachNotesInLoaction()
        BPMValueSet = self.Find_BPM_Of_EachNotesInLoaction()
        BeatsToMeasureSet = self.Find_BeatsToMeasure_Of_EachNotesInLoaction()
        DelaySet = self.Find_Delay_Of_EachNotesInLoaction()
        BarlineSet = self.Find_Barline_Of_EachNotesInLoaction()
        GOGOSet = self.Find_GOGO_Of_EachNotesInLoaction()

        BeatsToMeasureSetPure = self.DeleteCommmaInfo(self.Find_BeatsToMeasure_Of_EachNotesInLoaction())
        BPMValueSetPure = self.DeleteCommmaInfo(self.Find_BPM_Of_EachNotesInLoaction())
        ScrollSetPure = self.DeleteCommmaInfo(self.Find_Scroll_Of_EachNotesInLoaction())

        HasBrachProcessYet = False
        BranchStateSet = self.Find_Branch_Of_EachNotesInLoaction()

        self.ScrollSet = ScrollSet
        self.BPMValueSet = BPMValueSet
        self.BeatsToMeasureSet = BeatsToMeasureSet
        self.DelaySet = DelaySet
        self.BarlineSet = BarlineSet
        self.GOGOSet = GOGOSet

        self.BeatsToMeasureSetPure = BeatsToMeasureSetPure
        self.BPMValueSetPure = BPMValueSetPure
        self.ScrollSetPure = ScrollSetPure

        self.HasBrachProcessYet = HasBrachProcessYet
        self.BranchStateSet = BranchStateSet

        if(len(self.FindPhraseInRow("#BRANCHSTART",[ChosenBegin, ChosenEndin]))==0):
          self.IsBranchExist = False
        else:
          self.IsBranchExist = True

    def Find_Scroll_Of_EachNotesInLoaction(self):
      LastLocation = self.ChosenBegin
      MeasureInfo = []
      TempContent = "1" #預設值1
      for MeasureLocationList in self.EveryBarRowLocation:
        NotesInfo = []
        for NotesLocation in MeasureLocationList:
          Content = self.OffsetThingsValue("#SCROLL",[LastLocation,NotesLocation])
          if(Content!="" and not str.isspace(Content)):
            TempContent = ""
            for char in Content:
              if(str.isnumeric(char) or char=="+" or char=="-" or char=="." or char=="i"):
                if(char != "i"):
                    TempContent = TempContent + char
                else:
                    TempContent = TempContent + "j" #複數譜面會有虛數
          TempContent = complex(TempContent) #同BPM作法

          NotesInfo.append(TempContent)
          LastLocation = NotesLocation
        MeasureInfo.append(NotesInfo)
      return MeasureInfo

    def Find_BPM_Of_EachNotesInLoaction(self):
      LastLocation = self.ChosenBegin
      MeasureInfo = []
      TempContent = self.OffsetThingsValue("BPM:",[self.ChosenReady,self.ChosenBegin]) #預設使用譜面開始前設定的BPM
      if(TempContent==""):
        TempContent = self.OffsetThingsValue("BPM:",[0, self.Song_Begin[0]]) #沒有該譜面自設定的BPM，則沿用譜面檔案一開始能找到的數值

      for MeasureLocationList in self.EveryBarRowLocation:
        NotesInfo = []
        for NotesLocation in MeasureLocationList:
          Content = self.OffsetThingsValue("#BPMCHANGE",[LastLocation,NotesLocation])
          if(Content!="" and not str.isspace(Content)):
            TempContent = ""
            for char in Content:
              if(str.isnumeric(char) or char=="+" or char=="-" or char=="."):
                  TempContent = TempContent + char
          TempContent = float(TempContent)

          NotesInfo.append(TempContent)
          LastLocation = NotesLocation
        MeasureInfo.append(NotesInfo)
      return MeasureInfo
    
    def Find_BeatsToMeasure_Of_EachNotesInLoaction(self):
      LastLocation = self.ChosenBegin
      MeasureInfo = []
      TempContent = [4, 4] #預設4/4拍
      for MeasureLocationList in self.EveryBarRowLocation:
        NotesInfo = []
        for NotesLocation in MeasureLocationList:
          Content = self.OffsetThingsValue("#MEASURE",[LastLocation,NotesLocation])
          if(Content!="" and not str.isspace(Content)):
            TempContent = ""
            for char in Content:
              if(str.isnumeric(char) or char=="+" or char=="-" or char=="/" or char=="."):
                  TempContent = TempContent + char
            TempContent = TempContent.split("/")
            TempContent = [int(TempContent[0]), int(TempContent[1])]

          NotesInfo.append(TempContent)
          LastLocation = NotesLocation
        MeasureInfo.append(NotesInfo)
      return MeasureInfo
    
    def Find_Delay_Of_EachNotesInLoaction(self):
      LastLocation = self.ChosenBegin
      MeasureInfo = []
      for MeasureLocationList in self.EveryBarRowLocation:
        NotesInfo = []
        for NotesLocation in MeasureLocationList:
          Content = self.OffsetThingsValue("#DELAY",[LastLocation,NotesLocation])
          if(Content!="" and not str.isspace(Content)):
            TempContent = ""
            for char in Content:
              if(str.isnumeric(char) or char=="+" or char=="-" or char=="."):
                  TempContent = TempContent + char
            TempContent = float(TempContent)
          else:
            TempContent = 0.0
          NotesInfo.append(TempContent)
          LastLocation = NotesLocation
        MeasureInfo.append(NotesInfo)
      return MeasureInfo
    
    def Find_Barline_Of_EachNotesInLoaction(self):
      LastLocation = self.ChosenBegin
      MeasureInfo = []
      TempContent = True
      for MeasureLocationList in self.EveryBarRowLocation:
        NotesInfo = []
        for NotesLocation in MeasureLocationList:
          Content = self.OffsetThingsValue("#BARLINE",[LastLocation,NotesLocation])
          if(Content!="" and not str.isspace(Content)):
            TempContent = ""
            for char in Content:
              if(char!="" and char!=" " and char!="　"):
                  TempContent = TempContent + char
            if(TempContent=="ON"):
              TempContent = True
            else:
              TempContent = False

          NotesInfo.append(TempContent)
          LastLocation = NotesLocation
        MeasureInfo.append(NotesInfo)
      return MeasureInfo
    
    def Find_GOGO_Of_EachNotesInLoaction(self):
      LastLocation = self.ChosenBegin
      MeasureInfo = []
      TempContent = False
      for MeasureLocationList in self.EveryBarRowLocation:
        NotesInfo = []
        for NotesLocation in MeasureLocationList:
          Content = self.OffsetThingsValue("#GOGO",[LastLocation,NotesLocation])
          if(Content!="" and not str.isspace(Content)):
            TempContent = ""
            for char in Content:
              if(char!="" and char!=" " and char!="　"):
                  TempContent = TempContent + char
            if(TempContent=="START"):
              TempContent = True
            else:
              TempContent = False

          NotesInfo.append(TempContent)
          LastLocation = NotesLocation
        MeasureInfo.append(NotesInfo)
      return MeasureInfo
    
    #處理分歧問題
    def Find_Branch_Of_EachNotesInLoaction(self):
      LastLocation = self.ChosenBegin
      MeasureInfo = []

      TempIsBranched = False
      BranchCondition = None
      BranchSwitchSide = None
      if(len(self.FindPhraseInRow("#SECTION",[self.ChosenBegin, self.ChosenEndin]))!=0):
        ConditionResetTimes = 0
      else:
        ConditionResetTimes = None

      for MeasureLocationList in self.EveryBarRowLocation:
        NotesInfo = []
        for NotesLocation in MeasureLocationList:
          if(len(self.FindPhraseInRow("#BRANCHSTART",[LastLocation,NotesLocation]))!=0):
            TempIsBranched = True
            BranchCondition = self.OffsetThingsValue("#BRANCHSTART",[LastLocation,NotesLocation])
            BranchCondition = BranchCondition.split(",")
            BranchCondition[1]=float(BranchCondition[1])
            BranchCondition[2]=float(BranchCondition[2])
          if(TempIsBranched):
            if(len(self.FindPhraseInRow("#N",[LastLocation,NotesLocation]))!=0):
              BranchSwitchSide = 0
            elif(( len(self.FindPhraseInRow("#E",[LastLocation,NotesLocation])) - len(self.FindPhraseInRow("#END",[LastLocation,NotesLocation])) ) != 0):
              BranchSwitchSide = 1
            elif(( len(self.FindPhraseInRow("#M",[LastLocation,NotesLocation])) - len(self.FindPhraseInRow("#MEASURE",[LastLocation,NotesLocation])) ) != 0):
              BranchSwitchSide = 2
          else:
            pass

          if(len(self.FindPhraseInRow("#BRANCHEND",[LastLocation,NotesLocation]))!=0):
            TempIsBranched = False
            BranchCondition = None
            BranchSwitchSide = None
          else:
            pass

          if(len(self.FindPhraseInRow("#SECTION",[LastLocation,NotesLocation]))!=0):
            ConditionResetTimes = ConditionResetTimes + 1

          #TempContent形式: [是否在分歧狀態， 這個分岐的條件， 有分歧的話目前是在哪一個譜面, 條件重設次數]
          NotesInfo.append([TempIsBranched, BranchCondition, BranchSwitchSide, ConditionResetTimes])
          LastLocation = NotesLocation
        MeasureInfo.append(NotesInfo)
      return MeasureInfo

    def FindEveryPassedNotesLocation(self):
      locationinfo = []
      for i in range(len(self.EveryBar)):
        for j in range(len(self.EveryBar[i])):
          notes = self.EveryBar[i][j]
          if(notes!=","):
            locationinfo.append([i,j])
      return locationinfo
    
    def DeleteCommmaInfo(self, KindOfEveryBar):
      KindOfEveryBarWithoutComma = []
      for Bar in KindOfEveryBar:
        try:
          KindOfBarWithoutComma = ""
          for i in range(len(Bar)-1):
            KindOfBarWithoutComma = KindOfBarWithoutComma + Bar[i]
        except:
          KindOfBarWithoutComma = []
          for i in range(len(Bar)-1):
            KindOfBarWithoutComma.append(Bar[i])

        KindOfEveryBarWithoutComma.append(KindOfBarWithoutComma)
      return KindOfEveryBarWithoutComma
    
class TaikoFumenBranched(TaikoFumenInner):
    def __init__(self, Path, codec, UserChosenFumen, UserChosenBranchDirection):
        super().__init__(Path, codec, UserChosenFumen)
        if(not self.HasBrachProcessYet):

            OG_BranchStateSet = self.BranchStateSet

            OG_EveryBarRowLocation = self.EveryBarRowLocation
            OG_EveryBar = self.EveryBar

            OG_ScrollSet = self.ScrollSet
            OG_BPMValueSet = self.BPMValueSet
            OG_BeatsToMeasureSet = self.BeatsToMeasureSet
            OG_DelaySet = self.DelaySet
            OG_BarlineSet = self.BarlineSet
            OG_GOGOSet = self.GOGOSet

        EveryBarRowLocation = []
        EveryBar = []

        ScrollSet = []
        BPMValueSet = []
        BeatsToMeasureSet = []
        DelaySet = []
        BarlineSet = []
        GOGOSet = []

        BranchStateSet = []       #2024.03.22 新增

        for i in range(len(OG_EveryBar)):
            if(OG_BranchStateSet[i][0][2]==None or OG_BranchStateSet[i][0][2]==int(UserChosenBranchDirection)):
                EveryBarRowLocation.append(OG_EveryBarRowLocation[i])
                EveryBar.append(OG_EveryBar[i])

                ScrollSet.append(OG_ScrollSet[i])
                BPMValueSet.append(OG_BPMValueSet[i])
                BeatsToMeasureSet.append(OG_BeatsToMeasureSet[i])
                DelaySet.append(OG_DelaySet[i])
                BarlineSet.append(OG_BarlineSet[i])
                GOGOSet.append(OG_GOGOSet[i])

                BranchStateSet.append(OG_BranchStateSet[i])

        self.EveryBarRowLocation = EveryBarRowLocation
        self.EveryBar = EveryBar

        self.ScrollSet = ScrollSet
        self.BPMValueSet = BPMValueSet
        self.BeatsToMeasureSet = BeatsToMeasureSet
        self.DelaySet = DelaySet
        self.BarlineSet = BarlineSet
        self.GOGOSet = GOGOSet

        self.BranchStateSet = BranchStateSet

        TempContent = self.OffsetThingsValue("BPM:",[self.ChosenReady,self.ChosenBegin]) #預設使用譜面開始前設定的BPM
        if(TempContent==""):
            TempContent = self.OffsetThingsValue("BPM:",[0, self.Song_Begin[0]]) #沒有該譜面自設定的BPM，則沿用譜面檔案一開始能找到的數值
        TempContent = float(TempContent)
        self.TempContent = TempContent

        #譜面基本資訊
        TITLE = self.OffsetThingsValue_PareIgnored("TITLE:", [0, self.Song_Begin[0]])
        if(not self.IsAnyDual):
            COURSE = self.OffsetThingsValue("COURSE:", [self.ChosenReady, self.ChosenBegin])
            LevelStar = self.OffsetThingsValue("LEVEL:", [self.ChosenReady, self.ChosenBegin])
        else:
            COURSE = self.OffsetThingsValue("COURSE:", [self.Song_Difficulty[int(UserChosenFumen)], self.Song_Difficulty[int(UserChosenFumen)]+1])
            LevelStar = self.OffsetThingsValue("LEVEL:", [self.Song_level[int(UserChosenFumen)], self.Song_level[int(UserChosenFumen)]+1])
        COURSE = COURSE.replace(" ", "")

        match COURSE.lower():
          case "4"|"edit"   : COURSE = "Edit"
          case "3"|"oni"    : COURSE = "Oni"
          case "2"|"hard"   : COURSE = "Hard"
          case "1"|"normal" : COURSE = "Normal"
          case "0"|"easy"   : COURSE = "Easy"
          case "" : COURSE = "N/A"
          case _  : raise Exception("Course Is Invalid.")
           
        DUAL = None
        StringOfStartType = self.OffsetThingsValue("#START",[self.Song_Begin[UserChosenFumen],self.Song_Begin[UserChosenFumen]+1])
        dualstatestr = ""
        for Type in StringOfStartType:
            if(Type=="P" or Type=="1" or Type=="2"): dualstatestr = dualstatestr + Type

        #20250129 更新
        match dualstatestr:
          case "P1" : DUAL = "Player 1"
          case "P2" : DUAL = "Player 2"
          case ""   : pass
          case _    : raise Exception(f"Not a vaild player command. ({dualstatestr})")

        BRANCH = None
        match UserChosenBranchDirection:
           case 0: BRANCH = "普通譜面"
           case 1: BRANCH = "玄人譜面"
           case 2: BRANCH = "達人譜面"

        self.TITLE = TITLE
        self.COURSE = COURSE
        self.LevelStar = LevelStar
        self.DUAL = DUAL
        self.BRANCH = BRANCH
    
    def Get_RollInformation(self):
      RollLoaction = []

      IsDurningRoll = False
      RollType = None
      RollLocation = [None, None]

      EveryBarWithoutComma = self.DeleteCommmaInfo(self.EveryBar)

      for i in range(len(EveryBarWithoutComma)):
        for j in range(len(EveryBarWithoutComma[i])):

          Notes = EveryBarWithoutComma[i][j]
          if(not IsDurningRoll):
            if(Notes=="5" or Notes=="6" or Notes=="7" or Notes=="9"):
              RollType = int(Notes)
              RollLocation[0] = [i,j]
              IsDurningRoll = True
          else:
            if(Notes=="8" or Notes=="1" or Notes=="2" or Notes=="3" or Notes=="4"):
              RollLocation[1] = [i,j]
              IsDurningRoll = False

          if(RollType!=None and RollLocation[0]!=None and RollLocation[1]!=None):
            RollLoaction.append([RollType, RollLocation])
            RollType = None
            RollLocation = [None, None]

      return RollLoaction
    
    def Duration(self, x=[0, 0], y=None):
         EveryBar = self.EveryBar
         DelaySet = self.DelaySet
         BeatsToMeasureSet = self.BeatsToMeasureSet
         BPMValueSet = self.BPMValueSet

         if(y==None):
            y=[len(EveryBar)-1, len(EveryBar[-1])-1]
         OverallDuration = 0
         DELAYinProcess = 0
         ProcessDirectionElement = 1

         if(x[0]>y[0] or (x[0]==y[0] and x[1]>y[1])):
              Temp = [x, y]
              x = Temp[1]
              y = Temp[0]
              ProcessDirectionElement = -1
              del Temp

         #起頭點部分的DELAY不應該被記入
         OverallDuration = OverallDuration - DelaySet[x[0]][x[1]]
         DELAYinProcess = DELAYinProcess - DelaySet[x[0]][x[1]]

         for j in range(x[0],y[0]+1):
              if len(EveryBar[j])==1:
                   MeasureBeat, MeasureForm = BeatsToMeasureSet[j][0]

                   #可能與真正樂理上的算法有出入，這邊以太鼓次郎的判定作計算
                   OverallDuration = OverallDuration + 60 / BPMValueSet[j][0] * 4 * ( MeasureBeat / MeasureForm )
              else:
                   if(x[0]==y[0]):
                        a = x[1]
                        b = y[1]
                   else:
                        if(j==x[0]):
                             a = x[1]
                             b = len(EveryBar[j]) - 1 #小節資訊的最後一個是逗號，因此考慮實際譜面要-1，其他地方以此類推
                        elif(j==y[0]):
                             a = 0
                             b = y[1]
                        else:
                             a = 0
                             b = len(EveryBar[j]) - 1

                   for i in range(a,b):
                        MeasureBeat, MeasureForm = BeatsToMeasureSet[j][i]
                        OverallDuration = OverallDuration + DelaySet[j][i] + 60 / BPMValueSet[j][i] * 4 * ( MeasureBeat / MeasureForm ) / ( len(EveryBar[j]) - 1 )
                        DELAYinProcess = DELAYinProcess + DelaySet[j][i]

              #由於每個小節尾端(也就是逗號所在位置)也能夠加上指令，故須考慮
              if(x[0]!=y[0] and j!=y[0]):
                  OverallDuration = OverallDuration + DelaySet[j][-1]
                  DELAYinProcess = DELAYinProcess + DelaySet[j][-1]

         #最後點所屬的部份的DELAY應該被考慮
         OverallDuration = OverallDuration + DelaySet[y[0]][y[1]]
         DELAYinProcess = DELAYinProcess + DelaySet[y[0]][y[1]]

         return OverallDuration * ProcessDirectionElement, DELAYinProcess * ProcessDirectionElement