import os 
import torch
import pandas as pd
# add path to match_number venue_id mapping
# adding path for player_id to player_name mapping


# loading scalars
def add_match_data():
    pass

def get_pred_fp(player_id, model):
    pass

def get_pred_team(match_number, player_names_team_1, player_names_team_2, playing_or_not):
    match_venue_mapping = pd.read_csv(r"/inference/player_id_mapping.csv")
    player_id_mapping = pd.read_csv(r"/inference/player_id_mapping.csv")
    