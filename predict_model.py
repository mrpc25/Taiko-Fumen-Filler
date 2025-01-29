import torch
import torch.nn as nn
import torch.nn.functional as F

import configparser

def ReadConfig(configpath,SECTION,KEY):
    config = configparser.ConfigParser()
    config.read(configpath, encoding="utf-8")
    return config[SECTION][KEY]

device = "cuda" if torch.cuda.is_available() else "cpu"

ROLL_CONSIDERED = False 
DUAL_CHANNEL = False 
DownSample = False 

ROLL_SIGN = 1 if ROLL_CONSIDERED else 0
CHANNRL = 2 if DUAL_CHANNEL else 1
FREQ_BINS = int(ReadConfig("config.ini","AUDIO","freqency_bin"))
SEGMENT = int(ReadConfig("config.ini","AUDIO","segment"))

C = CHANNRL
ASIDE_NOTE = int(ReadConfig("config.ini","MODEL","surrounding_note"))
SEQ = ASIDE_NOTE*2 + 1

class Attention(nn.Module):
    def __init__(self, dim, n_heads, dropout):
        super().__init__()
        self.n_heads = n_heads
        self.att = torch.nn.MultiheadAttention(embed_dim=dim, num_heads=n_heads, dropout=dropout, batch_first=True)
        self.q = torch.nn.Linear(dim, dim)
        self.k = torch.nn.Linear(dim, dim)
        self.v =torch.nn.Linear(dim, dim)

    def forward(self, x):
        q = self.q(x)
        k = self.k(x)
        v = self.v(x)
        attn_output, attn_output_weights = self.att(q, k, v)
        return attn_output

class PreNorm(nn.Module):
    def __init__(self, dim, fn):
        super().__init__()
        self.norm = nn.LayerNorm(dim)
        self.fn = fn
    def forward(self, x, **kwargs):
        return self.fn(self.norm(x), **kwargs)

class FeedForward(nn.Sequential):
    def __init__(self, dim, hidden_dim, dropout = 0.):
        super().__init__()
        self.feedforward = nn.Sequential \
        (
            nn.Linear(dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, dim),
            nn.Dropout(dropout)
        )
    def forward(self, x):
        return self.feedforward(x)

class ResidualAdd(nn.Module):
    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def forward(self, x, **kwargs):
        res = x
        x = self.fn(x, **kwargs)
        x += res
        return x

class TaikoNoteClassfication(nn.Module):
    def __init__(self, out_dim, C=C, num_patches=SEQ, emb_dim=128, n_layers=6, dropout=0.1, heads=4):
        super(TaikoNoteClassfication, self).__init__()
        self.conv1 = nn.Conv2d(in_channels=C, out_channels=32, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1))
        self.conv2 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1))
        self.conv3 = nn.Conv2d(in_channels=64, out_channels=128, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1))

        self.dropout = nn.Dropout(0.1)
        self.pool = nn.MaxPool2d(kernel_size=(2, 2), stride=(2, 2), padding=(0, 0))

        FREQ_BINS = int(ReadConfig("config.ini","AUDIO","freqency_bin"))
        SEGMENT = int(ReadConfig("config.ini","AUDIO","segment"))
        self.fc = nn.Linear(128 * ((SEGMENT+1)//2//2//2) * (FREQ_BINS//2//2//2), emb_dim)

        self.channels = C
        self.n_layers = n_layers

        self.cls_token = nn.Parameter(torch.rand(1, 1, emb_dim))

        self.layers = nn.ModuleList([])
        for _ in range(n_layers):
            transformer_block = nn.Sequential\
            (
                ResidualAdd(PreNorm(emb_dim, Attention(emb_dim, n_heads = heads, dropout = dropout))),
                ResidualAdd(PreNorm(emb_dim, FeedForward(emb_dim, emb_dim, dropout = dropout)))
            )
            self.layers.append(transformer_block)

        self.head = nn.Sequential(nn.LayerNorm(emb_dim), nn.Linear(emb_dim, out_dim))

        PSE_UNIT = torch.ones(num_patches, emb_dim)
        for pos in range(num_patches):
          for i in range(emb_dim):
            x = i//2
            PSE_UNIT[pos][i] = torch.sin(torch.tensor(pos/1000**(x/emb_dim))) if (i % 2 == 0) else torch.cos(torch.tensor(pos/1000**(x/emb_dim)))
        self.basic_pos_emb_unit = PSE_UNIT.to(device)

        self.final_fc = nn.Linear(out_dim*SEQ, out_dim)

    def forward(self, x):
        batch_size, sequence_length, channels, height, width = x.size()
        x = x.view(batch_size * sequence_length, channels, height, width)

        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))

        x = x.view(batch_size, sequence_length, -1) 
        x = self.fc(x)

        position_encoding = self.basic_pos_emb_unit.repeat(batch_size, 1, 1)
        x = x + position_encoding
        cls_tokens = self.cls_token.repeat(batch_size, 1, 1)
        x = torch.cat([cls_tokens, x], dim=1)

        for i in range(self.n_layers):
            x = self.layers[i](x)
        return self.head(x[:, 0, :])

class TaikoNoteClassfication_240804(nn.Module):
    def __init__(self, out_dim, C=C, num_patches=SEQ, emb_dim=128, n_layers=6, dropout=0.1, heads=4):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels=C, out_channels=32, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1))
        self.conv2 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1))
        self.conv3 = nn.Conv2d(in_channels=64, out_channels=128, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1))

        self.dropout = nn.Dropout(0.1)
        self.pool = nn.MaxPool2d(kernel_size=(2, 2), stride=(2, 2), padding=(0, 0))

        FREQ_BINS = int(ReadConfig("config.ini","AUDIO","freqency_bin"))
        SEGMENT = int(ReadConfig("config.ini","AUDIO","segment"))
        self.fc = nn.Linear(128 * ((SEGMENT+1)//2//2//2) * (FREQ_BINS//2//2//2), emb_dim)

        self.channels = C
        self.n_layers = n_layers

        self.cls_token = nn.Parameter(torch.rand(1, 1, emb_dim))

        self.layers = nn.ModuleList([])
        for _ in range(n_layers):
            transformer_block = nn.Sequential\
            (
                ResidualAdd(PreNorm(emb_dim, Attention(emb_dim, n_heads = heads, dropout = dropout))),
                ResidualAdd(PreNorm(emb_dim, FeedForward(emb_dim, emb_dim, dropout = dropout)))
            )
            self.layers.append(transformer_block)

        self.head = nn.Sequential(nn.LayerNorm(emb_dim), nn.Linear(emb_dim, out_dim))

        PSE_UNIT = torch.ones(num_patches, emb_dim)
        for pos in range(num_patches):
          for i in range(emb_dim):
            x = i//2
            PSE_UNIT[pos][i] = torch.sin(torch.tensor(pos/1000**(x/emb_dim))) if (i % 2 == 0) else torch.cos(torch.tensor(pos/1000**(x/emb_dim)))
        self.basic_pos_emb_unit = PSE_UNIT.to(device)

        self.final_fc = nn.Linear(out_dim*SEQ, out_dim)

    def forward(self, x):
        batch_size, sequence_length, channels, height, width = x.size()
        x = x.view(batch_size * sequence_length, channels, height, width)

        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))

        x = x.view(batch_size, sequence_length, -1) 
        x = self.fc(x)

        position_encoding = self.basic_pos_emb_unit.repeat(batch_size, 1, 1)
        x = x + position_encoding
        cls_tokens = self.cls_token.repeat(batch_size, 1, 1)
        x = torch.cat([cls_tokens, x], dim=1)

        for i in range(self.n_layers):
            x = self.layers[i](x)
        return self.head(x[:, 0, :])

class TaikoNoteClassfication_241025(nn.Module):
    def __init__(self, out_dim, C=C, num_patches=SEQ, emb_dim=128, n_layers=6, dropout=0.1, heads=4):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels=C, out_channels=32, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1))
        self.conv2 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1))
        self.conv3 = nn.Conv2d(in_channels=64, out_channels=128, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1))

        self.dropout = nn.Dropout(0.1)
        self.pool = nn.MaxPool2d(kernel_size=(2, 2), stride=(2, 2), padding=(0, 0))
        
        FREQ_BINS = int(ReadConfig("config.ini","AUDIO","freqency_bin"))
        SEGMENT = int(ReadConfig("config.ini","AUDIO","segment"))
        self.fc = nn.Linear(128 * ((SEGMENT+1)//2//2//2) * (FREQ_BINS//2//2//2), emb_dim)

        self.channels = C
        self.n_layers = n_layers

        self.cls_token = nn.Parameter(torch.rand(1, 1, emb_dim))

        self.layers = nn.ModuleList([])
        for _ in range(n_layers):
            transformer_block = nn.Sequential\
            (
                ResidualAdd(PreNorm(emb_dim, Attention(emb_dim, n_heads = heads, dropout = dropout))),
                ResidualAdd(PreNorm(emb_dim, FeedForward(emb_dim, emb_dim, dropout = dropout)))
            )
            self.layers.append(transformer_block)

        self.head = nn.Sequential(nn.LayerNorm(emb_dim), nn.Linear(emb_dim, out_dim))

        PSE_UNIT = torch.ones(num_patches, emb_dim)
        for pos in range(num_patches):
          for i in range(emb_dim):
            x = i//2
            PSE_UNIT[pos][i] = torch.sin(torch.tensor(pos/1000**(x/emb_dim))) if (i % 2 == 0) else torch.cos(torch.tensor(pos/1000**(x/emb_dim)))
        self.basic_pos_emb_unit = PSE_UNIT.to(device)

    def forward(self, x):
        batch_size, sequence_length, channels, height, width = x.size()
        x = x.view(batch_size * sequence_length, channels, height, width)

        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))

        x = x.view(batch_size, sequence_length, -1) 
        x = self.fc(x)

        position_encoding = self.basic_pos_emb_unit.repeat(batch_size, 1, 1)
        x = x + position_encoding
        cls_tokens = self.cls_token.repeat(batch_size, 1, 1)
        x = torch.cat([cls_tokens, x], dim=1)

        for i in range(self.n_layers):
            x = self.layers[i](x)
        return self.head(x[:, 0, :])

class TaikoNoteClassfication_CNN(nn.Module):
    def __init__(self, n_classes):
        super().__init__()
        self.conv1 = nn.Conv2d(2, 32, (3,3), 1)
        self.conv2 = nn.Conv2d(32, 64, (3,3), 1)
        self.conv3 = nn.Conv2d(64, 128, (3,3), 1)
        self.conv4 = nn.Conv2d(128, 256, (3,3), 1)

        self.relu = nn.ReLU()
        self.max_pool2d = nn.MaxPool2d(kernel_size=(2,2))
        self.flatten = nn.Flatten(start_dim=1, end_dim=-1)

        self.dropout1 = nn.Dropout(0.25)
        self.dropout2 = nn.Dropout(0.5)
        self.pooling = nn.AdaptiveAvgPool2d((8, 8)) # extended

        self.fc1 = nn.Linear(16384, 128)
        self.fc2 = nn.Linear(128, n_classes)

        self.softmax = nn.Softmax(dim=0)

    def forward(self, x):
        x = self.conv1(x)
        x = self.relu(x)
        x = self.conv2(x)
        x = self.relu(x)
        x = self.max_pool2d(x)
        x = self.dropout1(x)

        x = self.conv3(x)
        x = self.relu(x)
        x = self.conv4(x)
        x = self.relu(x)
        x = self.max_pool2d(x)
        x = self.dropout1(x)
        x = self.pooling(x)

        x = self.flatten(x)
        x = self.fc1(x)
        x = self.relu(x)
        x = self.dropout2(x)
        x = self.fc2(x)

        return x

model_set = {}
model_set["240618"] = TaikoNoteClassfication_CNN
model_set["240804"] = TaikoNoteClassfication_240804
model_set["241025"] = TaikoNoteClassfication_241025

if __name__=='__main__':
    print(f"This is not main script of the entire application, if GUI is needed, run \"interface_multi.py\".")