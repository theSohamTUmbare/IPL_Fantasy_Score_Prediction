#!/usr/bin/env python3
"""
inference.py
Standalone script to perform fantasy-score inference
"""
import os
import warnings
import math
import argparse
import torch
import numpy as np
import pandas as pd
from dataclasses import dataclass
from torch.utils.data import Dataset
import torch.nn as nn
import torch.nn.functional as F

# ---------------- Configuration ----------------
@dataclass
class Config:
    PLAYERS_SIZE: int = 0
    CONTEXT_LEN: int = 16  # fixed, not user-changeable
    PERFORMANCE_INPUT_DIM: int = 23
    PERFORMANCE_EMBD_DIM: int = 64
    PLAYER_INPUT_DIM: int = 25
    MATCH_INPUT_EMBD: int = 14
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# ---------------- Dataset ----------------
class PlayerMatchDataset(Dataset):
    def __init__(self, universal_player_csv, player_matches_dir,
                 match_players_dir, match_info_csv, transform=None):
        self.context_len = Config.CONTEXT_LEN
        self.transform = transform
        self.univ_df = pd.read_csv(universal_player_csv)
        self.univ_df.set_index('player_id', inplace=True)
        self.univ_features = self.univ_df.drop(columns=['cricinfo_id'], errors='ignore')
        self.player_matches_dir = player_matches_dir
        self.player_ids = []
        self.player_match_data = {}
        for pid in self.univ_features.index:
            fp = os.path.join(player_matches_dir, f"{pid}.csv")
            if os.path.exists(fp):
                dfp = pd.read_csv(fp)
                if len(dfp) >= (self.context_len + 1):
                    self.player_ids.append(pid)
                    self.player_match_data[pid] = dfp
        self.match_players_dir = match_players_dir
        self.match_info_df = pd.read_csv(match_info_csv)
        self.match_info_df.set_index('match_id', inplace=True)

    def __len__(self):
        return len(self.player_ids)

    def __getitem__(self, idx):
        pid = self.player_ids[idx]
        df = self.player_match_data[pid]
        univ = self.univ_features.loc[pid].values.astype(float)
        context = df.tail(self.context_len + 1)
        exclude = ['teamname','match_id','strike_rate_fp','batting_fp',
                   'bowling_fp','fielding_fp','total_fp']
        perf_feats = context.drop(columns=exclude, errors='ignore').values.astype(float)
        perf_tensor = torch.tensor(perf_feats, dtype=torch.float32)
        keys = list(self.match_info_df.columns)
        team1_list, team2_list, info_list = [], [], []
        for _, row in context.iterrows():
            mid = int(row['match_id'])
            mp_path = os.path.join(self.match_players_dir, f"{mid}.csv")
            mp = pd.read_csv(mp_path)
            t1 = row['teamname']
            ids1 = mp.loc[mp['Team']==t1, 'player_id'].tolist()
            ids2 = mp.loc[mp['Team']!=t1, 'player_id'].tolist()
            f1 = self.univ_features.reindex(ids1).dropna().values.astype(float)
            f2 = self.univ_features.reindex(ids2).dropna().values.astype(float)
            team1_list.append(f1)
            team2_list.append(f2)
            info = self.match_info_df.loc[mid].to_dict() if mid in self.match_info_df.index else {}
            info_list.append([info.get(k,0.0) for k in keys])
        def pad_stack(arrs):
            if not arrs: return torch.empty((0,0,0))
            mx = max(a.shape[0] for a in arrs)
            fd = arrs[0].shape[1]
            padded = [np.pad(a, ((0,mx-a.shape[0]), (0,0)), mode='constant') for a in arrs]
            return torch.tensor(np.stack(padded), dtype=torch.float32)
        team1_tensor = pad_stack(team1_list)
        team2_tensor = pad_stack(team2_list)
        info_tensor = torch.tensor(np.array(info_list, dtype=float), dtype=torch.float32)
        return {
            'player_id': pid,
            'univ_features': torch.tensor(univ, dtype=torch.float32),
            'context_matches': perf_tensor,
            'team1_players': team1_tensor[:, :11, :],
            'team2_players': team2_tensor[:, :11, :],
            'match_info': info_tensor
        }

# ---------------- Model Components ----------------
class PlayerEmbedding(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.proj = nn.Linear(in_channels, out_channels)
    def forward(self, x): return self.proj(x)

class MatchEmbedding(nn.Module):
    def __init__(self, player_embedding_module, in_channels, out_channels):
        super().__init__()
        self.player = player_embedding_module
        self.proj = nn.Linear(in_channels, out_channels)
    def forward(self, team1, team2, info):
        B,T,n1,_ = team1.shape
        t1_flat = team1.reshape(B*T, n1, -1)
        e1 = self.player(t1_flat).sum(dim=1).reshape(B,T,-1)
        B,T,n2,_ = team2.shape
        t2_flat = team2.reshape(B*T, n2, -1)
        e2 = self.player(t2_flat).sum(dim=1).reshape(B,T,-1)
        fused = torch.cat([e1, e2, info], dim=-1)
        return self.proj(fused)

class PerformanceEmbedding(nn.Module):
    def __init__(self, player_emb_mod, match_emb_mod, in_dim, emb_dim):
        super().__init__()
        self.player = player_emb_mod
        self.match = match_emb_mod
        self.proj = nn.Linear(3*emb_dim, emb_dim)
        self.performance_proj = nn.Linear(in_dim + emb_dim, emb_dim)
    def forward(self, p_in, t1, t2, info):
        B,T,_ = p_in.shape
        pe = self.player(p_in.reshape(B*T,-1)).reshape(B,T,-1)
        mp = self.match(t1, t2, info)
        combined = torch.cat([pe, mp, pe], dim=-1)
        return self.proj(combined)

class SelfAttention(nn.Module):
    def __init__(self, n_heads, d_embed):
        super().__init__()
        self.in_proj = nn.Linear(d_embed, 3*d_embed)
        self.out_proj = nn.Linear(d_embed, d_embed)
        self.n_heads = n_heads
        self.d_head = d_embed // n_heads
    def forward(self, x, causal_mask=False):
        B,S,D = x.shape
        qkv = self.in_proj(x).reshape(B, S, 3, self.n_heads, self.d_head)
        q, k, v = qkv[:,:,0], qkv[:,:,1], qkv[:,:,2]
        q = q.transpose(1,2)
        att = (q @ k.transpose(-2, -1)) / math.sqrt(self.d_head)
        if causal_mask:
            mask = torch.triu(torch.ones(S,S), 1).bool()
            att.masked_fill_(mask, float('-inf'))
        w = torch.softmax(att, dim=-1)
        out = (w @ v).transpose(1,2).reshape(B, S, D)
        return self.out_proj(out)

class a_layer(nn.Module):
    def __init__(self, n_head, n_embd):
        super().__init__()
        self.layernorm_1 = nn.LayerNorm(n_embd)
        self.attention = SelfAttention(n_head, n_embd)
        self.layernorm_2 = nn.LayerNorm(n_embd)
        self.linear_1 = nn.Linear(n_embd, 4*n_embd)
        self.linear_2 = nn.Linear(4*n_embd, n_embd)
    def forward(self, x):
        res = x
        x = self.layernorm_1(x)
        x = self.attention(x)
        x += res
        res = x
        x = self.layernorm_2(x)
        x = self.linear_1(x)
        x = x * torch.sigmoid(1.702 * x)
        x = self.linear_2(x)
        x += res
        return x

class FantasyScorePrediction(nn.Module):
    def __init__(self, embedding_dim):
        super().__init__()
        D = embedding_dim
        self.proj1, self.drop1 = nn.Linear(3*D, 512), nn.Dropout(0.2)
        self.proj2, self.drop2 = nn.Linear(512, 256), nn.Dropout(0.2)
        self.proj3, self.drop3 = nn.Linear(256, 256), nn.Dropout(0.2)
        self.proj4, self.drop4 = nn.Linear(256, 128), nn.Dropout(0.2)
        self.proj5, self.drop5 = nn.Linear(128, 128), nn.Dropout(0.2)
        self.proj6 = nn.Linear(128, 1)
    def forward(self, x, player_emb, match_emb):
        x = torch.cat([x, player_emb, match_emb], dim=-1)
        x = F.gelu(self.proj1(x)); x = self.drop1(x)
        x = F.gelu(self.proj2(x)); x = self.drop2(x)
        x = F.gelu(self.proj3(x)); x = self.drop3(x)
        x = F.gelu(self.proj4(x)); x = self.drop4(x)
        x = F.gelu(self.proj5(x)); x = self.drop5(x)
        return self.proj6(x)

class NextFormPredictor(nn.Module):
    def __init__(self, player_emb_mod, match_emb_mod, fs_pred_mod, custom_loss_fn,
                 embedding_dim, num_layers, n_head):
        super().__init__()
        self.player_embedding_module = player_emb_mod
        self.match_embedding = match_emb_mod(player_emb_mod,
                                             2*embedding_dim + Config.MATCH_INPUT_EMBD,
                                             embedding_dim)
        self.fantasy_score_prediction_module = fs_pred_mod
        self.performance_embedding = PerformanceEmbedding(
            player_emb_mod,
            self.match_embedding,
            Config.PERFORMANCE_INPUT_DIM,
            embedding_dim
        )
        self.layers = nn.ModuleList([a_layer(n_head, embedding_dim)
                                     for _ in range(num_layers)])
        self.custom_loss = custom_loss_fn
    def forward(self, player_input, team1, team2, match_info, target=None):
        B,T,_ = player_input.shape
        perf_emb = self.performance_embedding(player_input, team1, team2, match_info)
        for layer in self.layers:
            perf_emb = layer(perf_emb)
        return (perf_emb, None) if target is None else (perf_emb, None)

# ---------------- Loss & Checkpoint ----------------
def custom_asymmetric_loss(pred, target, delta=5.0, penalty=2.0, extra_factor=1.5):
    err = pred - target
    abs_err = torch.abs(err)
    loss_small = 0.5 * err * err
    base_large = delta * abs_err - 0.5 * delta * delta
    loss_large = torch.where(err < 0,
                             penalty * base_large,
                             extra_factor * base_large)
    return torch.where(abs_err <= delta, loss_small, loss_large).mean()

def load_checkpoint(model, checkpoint_path):
    checkpoint = torch.load(checkpoint_path, map_location=Config.DEVICE)
    model.load_state_dict(checkpoint['model_state_dict'])
    print(f"Loaded model from {checkpoint_path}")
    return model









