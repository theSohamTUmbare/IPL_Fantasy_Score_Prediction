import json
import csv
import os
from collections import defaultdict
import pandas as pd 
import math
from espncricinfo.match import Match
from espncricinfo.player import Player

def overs_to_balls(overs_str):
    """Convert overs (e.g., '3.4') to total balls bowled."""
    # print(overs_str)
    if '.' in overs_str:
        overs, balls = overs_str.split('.')
        return int(overs) * 6 + int(balls)
    return int(overs_str) * 6

def str_to_float(overs_str):
    """Convert overs to a float value (e.g., '3.4' -> 3.6667)."""
    if '.' in overs_str:
        overs, balls = overs_str.split('.')
        return int(overs) + int(balls) / 6
    return float(overs_str)

def compute_batting_fp(runs, fours, sixes, balls, is_duck):
    """
    T20 Fantasy Cricket Batting Points:
      - Run: +1 per run
      - Boundary Bonus: +4 per four hit
      - Six Bonus: +6 per six hit
      - 25 Run Bonus: +4 if runs >= 25 (and below 50)
      - Half-Century Bonus: +8 if runs >= 50 (and below 75)
      - 75 Run Bonus: +12 if runs >= 75 (and below 100)
      - Century Bonus: +16 if runs >= 100 (no additional bonus applied)
      - Duck penalty: if player faced >=1 ball and scored 0, -2.
    """
    
    fp = runs + (fours * 4) + (sixes * 6)
    if runs >= 100:
        fp += 16
    elif runs >= 75:
        fp += 12
    elif runs >= 50:
        fp += 8
    elif runs >= 25:
        fp += 4
    if is_duck and balls > 0 and runs == 0:
        fp -= 2
    #strike rate
    #!!! struke rate bounus/ panelty are only aplicable for the strictly non-bowlers (strict - bowlers are exempt from st.rate criteria)  
    
    return fp


def compute_bowling_fp(wickets, dot_balls, maidens, lbw, bowled, legal_balls, runs_conceded, overs):
    """
    T20 Fantasy Cricket Bowling Points:
      - Wicket (excluding run out): +25 per wicket.
      - Bonus for LBW, Bowled, Hit wicket, and Caught and Bowled: +8 each.
      - Wicket haul bonus: if wickets>=3: +4; >=4: +8; >=5: +12.
      - Dot Ball: +1 per legal dot ball.
      - Maiden Over: +12 per maiden over.
      - Economy bonus (if legal_balls >= 12):
          * economy < 5: +6
          * 5 <= economy < 6: +4
          * 6 <= economy < 7: +2
          * 10 <= economy <= 11: -2
          * 11.01 <= economy <= 12: -4
          * economy > 12: -6
    """
    fp = wickets * 25
    fp += (lbw + bowled) * 8
    if wickets >= 5:
        fp += 12
    elif wickets >= 4:
        fp += 8
    elif wickets >= 3:
        fp += 4
    fp += dot_balls
    fp += maidens * 12
    if legal_balls >= 12 and overs > 1:
        economy = runs_conceded / overs
        if economy < 5:
            fp += 6
        elif 5 <= economy < 6:
            fp += 4
        elif 6 <= economy <= 7:
            fp += 2
        elif 10 <= economy <= 11:
            fp -= 2
        elif 11.01 <= economy <= 12:
            fp -= 4
        elif economy > 12:
            fp -= 6
    return fp


def compute_fielding_fp(catches, stumps, direct_runouts, indirect_runouts):
    """
    T20 Fantasy Cricket Fielding Points:
      - Catch: +8 per catch.
      - Additionally, if catches >= 3, add one bonus of +4 (only once).
      - Stumping: +12 per stumping.
      - Run out (Direct hit): +12 per direct run out.
      - Run out (Indirect): +6 per indirect run out.
    """
    fp = catches * 8
    if catches >= 3:
        fp += 4
    fp += stumps * 12
    fp += direct_runouts * 12
    fp += indirect_runouts * 6
    return fp

def process_match(json_file):
    # Reset global aggregators for each match processing
    batting_stats = defaultdict(lambda: {"runs": 0, "balls": 0, "fours": 0, "sixes": 0,"is_dismissed":False})
    bowling_stats = defaultdict(lambda: {
        "legal_balls": 0, "dot_balls": 0, "maidens": 0, "runs_conceded": 0,
        "fours_conceded": 0, "sixes_conceded": 0, "wickets": 0,
        "lbw": 0, "bowled": 0,"wides": 0, "noballs": 0, "overs_bowled": set(),
        'overs': 0, 
    })
    fielding_stats = defaultdict(lambda: {"catches": 0, "stumps": 0, "direct_runouts": 0, "indirect_runouts": 0})
    
    with open(json_file, 'r') as f:
        match = json.load(f)
    
    balls_per_over = match.get("info", {}).get("balls_per_over", 6) # just 6
    
    for inning in match.get("innings", []):
        for over_index, over in enumerate(inning.get("overs", [])):
            legal_balls_in_over = 0
            over_runs = 0
            current_bowler = None
            for delivery in over.get("deliveries", []):
                batter = delivery.get("batter")
                bowler = delivery.get("bowler")
                    
                extras = delivery.get("extras", {})
                extras_int = {k: int(v) for k, v in extras.items()}
                runs = delivery.get("runs", {})
                batter_runs = runs.get("batter", 0)
                total_runs = runs.get("total", 0)
                
                # Update batting stats (ignoring wides and no-balls for ball count)
                is_wide = 'wides' in extras
                is_noball = 'noballs' in extras
                is_bye = 'byes' in extras
                    
                is_legbye = 'legbyes' in extras 
                if not is_wide and not is_noball:
                    batting_stats[batter]["balls"] += 1 # check for valid batter conceded balls 
                if batting_stats[batter]['runs'] < 50 and batting_stats[batter]['runs'] + batter_runs >= 50:
                    batting_stats[batter]['half_centuries'] = True
                if batting_stats[batter]['runs'] < 100 and batting_stats[batter]['runs'] + batter_runs >= 100:
                    batting_stats[batter]['centuries'] = True
                
                batting_stats[batter]["runs"] += batter_runs
                # bounderies 
                if batter_runs == 4:
                    batting_stats[batter]["fours"] += 1
                if batter_runs == 6:
                    batting_stats[batter]["sixes"] += 1
                
                # batting correct features implementation 
                
                # Update bowling stats
                if current_bowler is None:
                    current_bowler = bowler
                if not is_wide and not is_noball :
                    bowling_stats[bowler]["legal_balls"] += 1
                    legal_balls_in_over += 1
                    
                if is_wide:
                    bowling_stats[bowler]["wides"] += extras_int.get("wides", 0)
                if is_noball:
                    bowling_stats[bowler]["noballs"] += extras_int.get("noballs", 0)
                
                
                #runs conceded
                bowling_stats[bowler]["runs_conceded"] += (batter_runs +
                                                           extras_int.get("wides", 0) +
                                                           extras_int.get("noballs", 0) +
                                                           extras_int.get("penalty", 0) +
                                                           extras_int.get("legbyes", 0))
                #correctly implemented as per T_20 the rules 
                
                
                if (not is_wide and not is_noball and total_runs == 0) or is_bye or is_legbye: # incorrect check if not correct
                    bowling_stats[bowler]["dot_balls"] += 1

                    
                if batter_runs == 4:
                    bowling_stats[bowler]["fours_conceded"] += 1
                if batter_runs == 6:
                    bowling_stats[bowler]["sixes_conceded"] += 1
                
                # if not is_wide and not is_noball:
                over_runs += total_runs #ALL runs including extras are covered by over_runs
                
                #Wicket info

                if 'wickets' in delivery:
                    for wicket_info in delivery['wickets']: #wicket is a list handle it in that way
                        kind = wicket_info.get("kind","").lower()
                        batsman = wicket_info.get("player_out","")
                        if kind not in ["run out","retired hurt",'retired out','obstructing the field']:
                            batting_stats[batsman]['is_dismissed'] = True                            
                            bowling_stats[bowler]["wickets"] += 1
                            if kind == "lbw":
                                bowling_stats[bowler]["lbw"] += 1
                                # lbw += 1
                            elif kind == "bowled":
                                bowling_stats[bowler]["bowled"] += 1
                                # bowled += 1
                            elif kind in ['caught','caught and bowled']:
                                # caught += 1
                                if kind == 'caught and bowled':
                                    fielding_stats[bowler]["catches"] += 1   # count of bowler catch is incremented
                                    # bowling_stats[bowler]["caught_bowled"] += 1   # should we count it here or in the fielding cuz it's a caught
                                else:
                                    for fielder in wicket_info.get("fielders",[]):
                                        fname = fielder.get("name")
                                        if fname:
                                            fielding_stats[fname]["catches"] += 1
                            elif kind == 'stumped':
                                for fielder in wicket_info.get("fielders",[]):
                                    fname = fielder.get("name")
                                    if fname:
                                        fielding_stats[fname]["stumps"] += 1
                        elif kind == "run out":
                            fielders = [f.get('name') for f in wicket_info.get('fielders',[]) if f.get('name')]
                            if len(fielders) == 1:
                                fielding_stats[fielders[0]]["direct_runouts"] += 1 
                            elif len(fielders) >= 2:
                                for f in fielders[-2:]:
                                    fielding_stats[f]["indirect_runouts"] += 1 #last 2 player will be rewarded 
                                
                            # wickets are taken care of some rare wickets like - retired hurt, retired out or obstructing the fields are ignored (wait last one should be credited to the fielder shouldn't)
            #end of over : check for madien over (insort no inc in team-total for that over)
            if legal_balls_in_over == balls_per_over and over_runs == 0 and current_bowler:
                 bowling_stats[current_bowler]["maidens"] += 1
            # now it's fine and correctly implemented 
            if current_bowler:
                bowling_stats[current_bowler]["overs_bowled"].add(over_index + 1) # using 1indexed over numbers
                
    # # Compute overs using the actual balls_per_over value
        
    for bowler, stats in bowling_stats.items():
        stats["overs"] = math.floor(stats["legal_balls"] / balls_per_over) + ((stats['legal_balls'] % balls_per_over)/10.0) if stats["legal_balls"] else 0.0  
    return match, batting_stats, bowling_stats, fielding_stats

def build_venue_features(venue_id, venue_name, venue_latitude, venue_longitude, total_runs, wickets, bowled, caught, lbw):
    venue = {
        "venue_id": venue_id,        
        "venue_latitude": venue_latitude,
        "venue_longitude": venue_longitude,
        "venue_name": venue_name,
        "total_runs": total_runs,
        "wickets": wickets,
        "bowled": bowled,
        "caught": caught,
        "lbw": lbw,
    }
    return venue    

def get_player_performance(json_file):
    # Reset global stats by processing the match freshly
    match, batting_stats, bowling_stats, fielding_stats = process_match(json_file)
    # outcome = match.get("info", {}).get("outcome", {})
    # winner = outcome['winner']
    # print(winner)
    # toss = match.get("info", {}).get("toss", {})
    # venue_winner = 'bat' if else 'bowl'
    # venue_id = match_data['match']['ground_id']
    # venue_name = match_data['match']['ground_name']
    # venue_longitude = match_data['match']['ground_longitude']
    # venue_latitude = match_data['match']['ground_latitude']
    # Extract batting order from info.players (order reflects batting order)
    # print(match, '\\n\n')
    batting_order = {}
    total_runs = 0
    players_info = match.get("info", {}).get("players", {})
    
    # exit()
    # print("players_info", players_info)
    for team,players in players_info.items():
        for pos,player in enumerate(players,start=1):
            if player not in batting_order:
                batting_order[player] = pos
    # print("batting_order", batting_order)        
    registry = match.get("info", {}).get("registry", {}).get("people", {})
    team_rosters = match.get("info",{}).get('players',{})
    all_players = set()
    
    for team,players in team_rosters.items():
        # if isinstance(players,list):
        for player in players:
            all_players.add((player,team))
    # print("all_players")
    # for player, team in all_players:
        # print(player,team)
    
    # make sure correct use of 11 lineup 
    final_stats = {}
    wickets = 0
    bowled = 0
    caught = 0
    lbw = 0
    total_runs = 0
    for player,team in all_players:
        #Batting stats 
        # half_centuries, centuries = False, False
        bat = batting_stats.get(player,{"runs": 0, "balls": 0, "fours": 0, "sixes": 0,'is_dismissed':False})
        runs = bat["runs"]
        # if runs > 50:
        #     half_centuries = True
        # if runs > 100:  
        #     centuries = True
        total_runs += runs
        # print(batting_stats)
        # print(player, team, bat)
        
        balls_faced = bat["balls"] #make use ball_faced are logically-correct 
        fours = bat["fours"]
        sixes = bat["sixes"]
        is_dismissed = bat['is_dismissed'] #do we need it here
        batting_fp = compute_batting_fp(runs,fours,sixes,balls_faced,is_dismissed) # TODO include the strike_rate point 
        strike_rate = round((runs/balls_faced * 100),2) if balls_faced > 0 else None # why don't encapsulate it's fp in batting _fp
        # print(balls_faced, fours, sixes, strike_rate, is_dismissed, batting_fp)
        #Bowling stats
        bowl = bowling_stats.get(player,{
            "legal_balls": 0, "dot_balls": 0, "maidens": 0, "runs_conceded": 0,
            "fours_conceded": 0, "sixes_conceded": 0, "wickets": 0, "overs": 0.0,
            "lbw": 0, "bowled": 0, "caught": 0, "wides": 0, "noballs": 0, "overs_bowled": set(),
        })
        overs = bowl["overs"]
        # if player == 'Shahbaz Ahmed':
        #     print(bowl['runs_conceded'],  (overs_to_balls(str(overs))/6))
        economy_rate = round(bowl['runs_conceded'] / (overs_to_balls(str(overs))/6), 2) if overs > 0 else 0.0 # check for correct logic
        
        bowling_fp = compute_bowling_fp(
            bowl["wickets"], bowl["dot_balls"], bowl["maidens"],
            bowl["lbw"], bowl["bowled"], bowl["legal_balls"], bowl["runs_conceded"], overs
        )
        # make sure correct 
        # print(bowling_stats)
        # print(player, bowl, economy_rate)
        wickets += bowl["wickets"]
        bowled += bowl["bowled"]
        lbw += bowl["lbw"]
        # return 'a', 'b'
        #fielding stats
        field = fielding_stats.get(player,{"catches": 0, "stumps": 0, "direct_runouts": 0, "indirect_runouts": 0})
        fielding_fp = compute_fielding_fp(field["catches"], field["stumps"], field["direct_runouts"], field["indirect_runouts"])
        # print(field)
        caught += field["catches"]
        wickets += field["stumps"]
        wickets += field["direct_runouts"]
        wickets += field["indirect_runouts"]/2 # since 2 players are involved in each runout
        #strike rate ponits for batters (only if player did not bowl and faced atleast 10 balls )
        strike_rate_points = 0
        if balls_faced >= 10: # it should only apply to a non-blowler striclty (!isbowler)
            sr = (runs / balls_faced) * 100
            if sr > 170:
                strike_rate_points = 6
            elif 150.01 <= sr <= 170:
                strike_rate_points = 4
            elif 130 <= sr < 150:
                strike_rate_points = 2
            elif 60 <= sr <= 70:
                strike_rate_points = -2
            elif 50 <= sr < 60:
                strike_rate_points = -4
            elif sr < 50:
                strike_rate_points = -6
        strike_rate_fp = strike_rate_points
        batting_fp += strike_rate_fp # we have to deal it later for allrounders since they are eligible for st.rate 
        player_id = registry.get(player,"")
        final_stats[player_id] = {
            "player_id": player_id,
            "team": team,
            "name": player,
            "batting_position": batting_order.get(player, 0),
            # Batting features
            "runs": runs,
            "balls": balls_faced,
            "fours": fours,
            "sixes": sixes,
            "strike_rate": strike_rate,
            
            # Bowling features
            "overs_bowled": sorted(list(bowl.get("overs_bowled", set()))),
            "overs" : str(bowl.get("overs",0.0)),
            "total_balls": bowl.get("legal_balls", 0),
            "dot_balls": bowl.get("dot_balls", 0),
            "maidens": bowl.get("maidens", 0),
            "conceded": bowl.get("runs_conceded", 0),
            "fours_conceded": bowl.get("fours_conceded", 0),
            "sixes_conceded": bowl.get("sixes_conceded", 0),
            "wickets": bowl.get("wickets", 0),
            "lbw": bowl.get("lbw", 0),
            "bowled": bowl.get("bowled", 0),
            "noballs": bowl.get("noballs", 0),
            "wides": bowl.get("wides", 0),
            "economy_rate": economy_rate,
            # Fielding features
            "catches": field.get("catches", 0),
            "stumps": field.get("stumps", 0),
            "direct_hit": field.get("direct_runouts", 0),
            "indirect_hit": field.get("indirect_runouts", 0),
            # fantasy points
            "strike_rate_fp":strike_rate_fp,
            "batting_fp": batting_fp,
            "bowling_fp": bowling_fp,
            "fielding_fp": fielding_fp,
            "total_fp": batting_fp + bowling_fp + fielding_fp            
        }
    # wickets = int(wickets)   
    # venue_features = build_venue_features(venue_id, venue_name, venue_latitude, venue_longitude, total_runs, wickets, bowled, caught, lbw)
    # print(final_stats['Abdul Samad'])
    return final_stats

# def build_player_feature_map(json_file, players, venues, match_data):
#     # Reset global stats by processing the match freshly
#     match, batting_stats, bowling_stats, fielding_stats = process_match(json_file)
#     # outcome = match.get("info", {}).get("outcome", {})
#     # winner = outcome['winner']
#     # print(winner)
#     # toss = match.get("info", {}).get("toss", {})
#     # venue_winner = 'bat' if else 'bowl'
#     venue_id = match_data['match']['ground_id']
#     venue_name = match_data['match']['ground_name']
#     venue_longitude = match_data['match']['ground_longitude']
#     venue_latitude = match_data['match']['ground_latitude']
#     # Extract batting order from info.players (order reflects batting order)
#     # print(match, '\\n\n')
#     batting_order = {}
#     total_runs = 0
#     players_info = match.get("info", {}).get("players", {})
    
#     # exit()
#     # print("players_info", players_info)
#     for team,players in players_info.items():
#         for pos,player in enumerate(players,start=1):
#             if player not in batting_order:
#                 batting_order[player] = pos
#     # print("batting_order", batting_order)        
#     registry = match.get("info", {}).get("registry", {}).get("people", {})
#     team_rosters = match.get("info",{}).get('players',{})
#     all_players = set()
    
#     for team,players in team_rosters.items():
#         if isinstance(players,list):
#             for player in players:
#                 all_players.add((player,team))
#     # print("all_players")
#     # for player, team in all_players:
#         # print(player,team)
    
#     # make sure correct use of 11 lineup 
#     final_stats = {}
#     wickets = 0
#     bowled = 0
#     caught = 0
#     lbw = 0
#     total_runs = 0
#     for player,team in all_players:
#         #Batting stats 
#         # half_centuries, centuries = False, False
#         bat = batting_stats.get(player,{"runs": 0, "balls": 0, "fours": 0, "sixes": 0,'is_dismissed':False})
#         runs = bat["runs"]
#         # if runs > 50:
#         #     half_centuries = True
#         # if runs > 100:  
#         #     centuries = True
#         total_runs += runs
#         # print(batting_stats)
#         # print(player, team, bat)
        
#         balls_faced = bat["balls"] #make use ball_faced are logically-correct 
#         fours = bat["fours"]
#         sixes = bat["sixes"]
#         is_dismissed = bat['is_dismissed'] #do we need it here
#         batting_fp = compute_batting_fp(runs,fours,sixes,balls_faced,is_dismissed) # TODO include the strike_rate point 
#         strike_rate = round((runs/balls_faced * 100),2) if balls_faced > 0 else None # why don't encapsulate it's fp in batting _fp
#         # print(balls_faced, fours, sixes, strike_rate, is_dismissed, batting_fp)
#         #Bowling stats
#         bowl = bowling_stats.get(player,{
#             "legal_balls": 0, "dot_balls": 0, "maidens": 0, "runs_conceded": 0,
#             "fours_conceded": 0, "sixes_conceded": 0, "wickets": 0, "overs": 0.0,
#             "lbw": 0, "bowled": 0, "caught": 0, "wides": 0, "noballs": 0, "overs_bowled": set(),
#         })
#         overs = bowl["overs"]
#         # if player == 'Shahbaz Ahmed':
#         #     print(bowl['runs_conceded'],  (overs_to_balls(str(overs))/6))
#         economy_rate = round(bowl['runs_conceded'] / (overs_to_balls(str(overs))/6), 2) if overs > 0 else 0.0 # check for correct logic
        
#         bowling_fp = compute_bowling_fp(
#             bowl["wickets"], bowl["dot_balls"], bowl["maidens"],
#             bowl["lbw"], bowl["bowled"], bowl["legal_balls"], bowl["runs_conceded"], overs
#         )
#         # make sure correct 
#         # print(bowling_stats)
#         # print(player, bowl, economy_rate)
#         wickets += bowl["wickets"]
#         bowled += bowl["bowled"]
#         lbw += bowl["lbw"]
#         # return 'a', 'b'
#         #fielding stats
#         field = fielding_stats.get(player,{"catches": 0, "stumps": 0, "direct_runouts": 0, "indirect_runouts": 0})
#         fielding_fp = compute_fielding_fp(field["catches"], field["stumps"], field["direct_runouts"], field["indirect_runouts"])
#         # print(field)
#         caught += field["catches"]
#         wickets += field["stumps"]
#         wickets += field["direct_runouts"]
#         wickets += field["indirect_runouts"]/2 # since 2 players are involved in each runout
#         #strike rate ponits for batters (only if player did not bowl and faced atleast 10 balls )
#         strike_rate_points = 0
#         if balls_faced >= 10: # it should only apply to a non-blowler striclty (!isbowler)
#             sr = (runs / balls_faced) * 100
#             if sr > 170:
#                 strike_rate_points = 6
#             elif 150.01 <= sr <= 170:
#                 strike_rate_points = 4
#             elif 130 <= sr < 150:
#                 strike_rate_points = 2
#             elif 60 <= sr <= 70:
#                 strike_rate_points = -2
#             elif 50 <= sr < 60:
#                 strike_rate_points = -4
#             elif sr < 50:
#                 strike_rate_points = -6
#         strike_rate_fp = strike_rate_points
#         batting_fp += strike_rate_fp # we have to deal it later for allrounders since they are eligible for st.rate 
#         player_id = registry.get(player,"")
#         final_stats[player_id] = {
#             "player_id": player_id,
#             "team": team,
#             "name": player,
#             "batting_position": batting_order.get(player, 0),
#             # Batting features
#             "runs": runs,
#             "balls": balls_faced,
#             "fours": fours,
#             "sixes": sixes,
#             "strike_rate": strike_rate,
            
#             # Bowling features
#             "overs_bowled": sorted(list(bowl.get("overs_bowled", set()))),
#             "overs" : str(bowl.get("overs",0.0)),
#             "total_balls": bowl.get("legal_balls", 0),
#             "dot_balls": bowl.get("dot_balls", 0),
#             "maidens": bowl.get("maidens", 0),
#             "conceded": bowl.get("runs_conceded", 0),
#             "fours_conceded": bowl.get("fours_conceded", 0),
#             "sixes_conceded": bowl.get("sixes_conceded", 0),
#             "wickets": bowl.get("wickets", 0),
#             "lbw": bowl.get("lbw", 0),
#             "bowled": bowl.get("bowled", 0),
#             "noballs": bowl.get("noballs", 0),
#             "wides": bowl.get("wides", 0),
#             "economy_rate": economy_rate,
#             # Fielding features
#             "catches": field.get("catches", 0),
#             "stumps": field.get("stumps", 0),
#             "direct_hit": field.get("direct_runouts", 0),
#             "indirect_hit": field.get("indirect_runouts", 0),
#             # fantasy points
#             "strike_rate_fp":strike_rate_fp,
#             "batting_fp": batting_fp,
#             "bowling_fp": bowling_fp,
#             "fielding_fp": fielding_fp,
#             "total_fp": batting_fp + bowling_fp + fielding_fp            
#         }
#     wickets = int(wickets)   
#     venue_features = build_venue_features(venue_id, venue_name, venue_latitude, venue_longitude, total_runs, wickets, bowled, caught, lbw)
#     # print(final_stats['Abdul Samad'])
#     return final_stats, venue_features, 

def write_features_to_csv(dict, output_csv):
    df = pd.DataFrame.from_dict(dict, orient='index')
    # df.reset_index(inplace=True)  # Move player_id from index to a column
    # df.rename(columns={'index': 'player_id'}, inplace=True)  # Rename the column
    # print(df.head())
    # print(df.cols())
    # print("Columns in the dataframe: ", df.columns)
    if output_csv == 'players.csv':
        df.drop(columns=['Strike rate denominator', 'Average Economy Rate Denominator'], inplace=True)

    # Save to a CSV file
    df.to_csv(output_csv, index=False)

    print("Player data saved to", output_csv)

# if __name__ == "_main_":
# json_file_path = r'C:\Users\kumar\IPL\ipl_json\1359475.json'
folder_paths = ["C:\\Users\\bitso\\OneDrive\\Desktop\\ipl hackathon\\IPL_Fantasy_Score_Prediction\\t20_json", "C:\\Users\\bitso\\OneDrive\\Desktop\\ipl hackathon\\IPL_Fantasy_Score_Prediction\\ipl_json", "C:\\Users\\bitso\\OneDrive\\Desktop\\ipl hackathon\\IPL_Fantasy_Score_Prediction\\sma_json", "C:\\Users\\bitso\\OneDrive\\Desktop\\ipl hackathon\\IPL_Fantasy_Score_Prediction\\bbl_json", "C:\\Users\\bitso\\OneDrive\\Desktop\\ipl hackathon\\IPL_Fantasy_Score_Prediction\\bpl_json", "C:\\Users\\bitso\\OneDrive\\Desktop\\ipl hackathon\\IPL_Fantasy_Score_Prediction\\cpl_json", "C:\\Users\\bitso\\OneDrive\\Desktop\\ipl hackathon\\IPL_Fantasy_Score_Prediction\\ctc_json", "C:\\Users\\bitso\\OneDrive\\Desktop\\ipl hackathon\\IPL_Fantasy_Score_Prediction\\it20s_json","C:\\Users\\bitso\\OneDrive\\Desktop\\ipl hackathon\\IPL_Fantasy_Score_Prediction\\ntb_json"] 
# print(len(filenames))
# exit()
players = {}
venues = {}
# filenames = ['1426312.json', '1426311.json']
import json
types = ['T20I', 'IPL', 'SMA', 'BBL', 'BPL', 'CPL', 'CTC', 'IT20S', 'NTB']
load = True
if load:
    with open('save_matches\matches.json', 'r') as file:
        matches = json.load(file)
    with open('save_matches\save_point.json', 'r') as file:
        save_point = json.load(file)
else:
    matches = {}
    save_point = None
for folder_idx in range(len(folder_paths)):
    print('folder_idx', folder_idx)
    if save_point:
        if folder_idx < save_point['folder_idx']:
            print(folder_idx, save_point['folder_idx'])
            continue
    folder_path = folder_paths[folder_idx]
    type = types[folder_idx] # os.path.basename(os.path.dirname(folder_paths, types))
    filenames = os.listdir(folder_path)  # List all files and folders in the directory 
    for file_idx in range(len(filenames)):
        if save_point and folder_idx == save_point['folder_idx']:
            if file_idx <= save_point['file_idx']:
                continue       
        print('file_idx', file_idx)
        filename = filenames[file_idx]
        if filename.endswith(".json"):
            match_id = filename.split(".")[0]
            print("Processing match: ", match_id, type)
            # with open(os.path.join(folder_path, filename), 'r') as f:
            #     match_data.json = json.load(f)
            match_data = Match(match_id).get_json()
            json_file_path = os.path.join(folder_path, filename)
            match_id = filename.split(".")[0]
            match_id = str(match_id) + " " + type
            matches[match_id] = {'match_data': None, 'venue_data': None}
            match_features, venue_features= build_player_feature_map(json_file_path, players, venues, match_data)
            # break
            matches[match_id]['match_data'] = match_features
            # if event_info and event_info['name'] == 'Indian Premier League':
            # if type == 'IPL':
            matches[match_id]['venue_data'] = venue_features
            # else:
                # matches[match_id]['venue_data'] = None
                
            print(len(matches))
            
            if (len(matches) % 50) == 0:
                save_point = {'file_idx': file_idx, 'folder_idx': folder_idx}
                with open('save_matches\save_point.json', 'w') as file:
                    json.dump(save_point, file)
                with open(f'IPL_Fantasy_Score_Prediction\save_matches\matches.json', 'w') as file:
                    json.dump(matches, file)
                print("Saving checkpoint at", save_point)
# exit()
print("done")
players = {}
venues = {}
for match_id, data in matches.items():
    match_features = data['match_data']
    # print(match_id)
    venue_data = data['venue_data']
    for player_id, data in match_features.items():
        # player_id = str(player_id)
        # print(type(data['runs']))
        # break
        # print(player_id, data['name'], data['runs'], type(data['runs']))
        
        # if data['name'] == 'Shahbaz Ahmed':
        #     print(data['overs'])
        balls_bowled = overs_to_balls(data['overs'])
        # if data['name'] == 'Shahbaz Ahmed':
        #     print(balls_bowled)
        if player_id in players:

            # print("heloo")
            players[player_id]['matches'] += 1
            players[player_id]['Strike rate denominator'] += 1 if data['balls'] > 0 else 0
            if data['balls'] > 0 and players[player_id]['strike rate in all matches combined']:
                players[player_id]['strike rate in all matches combined'] = round(((players[player_id]['strike rate in all matches combined'] * (players[player_id]['Strike rate denominator'] -1)) + data['strike_rate']) / players[player_id]['Strike rate denominator'], 3)
            # print(type(players[player_id]['Total Runs Scored in all matches combined']), type(data['runs']))
            # print(players[player_id]['Total Runs Scored in all matches combined'], data['runs'])
            players[player_id]['Total Runs Scored in all matches combined'] += data['runs']
            # print(players[player_id]['Total Runs Scored in all matches combined'])
            players[player_id]['no. of fours'] += data['fours']
            players[player_id]['no. of sixes'] += data['sixes']
            players[player_id]['highest runs scored in a match'] = max(players[player_id]['highest runs scored in a match'], data['runs'])
            players[player_id]['Balls Played till now'] += data['balls']
            players[player_id]['no. of dot_balls'] += data['dot_balls'] # bowler
            players[player_id]['maiden_overs'] += data['maidens']
            players[player_id]['run conceded'] += data['conceded']
            players[player_id]['Average Economy Rate Denominator'] += 1 if balls_bowled > 0 else 0
            if balls_bowled > 0 and players[player_id]['Average Economy Rate']:
                # if players[player_id]['name'] == 'Shahbaz Ahmed':
                #     print(players[player_id]['Average Economy Rate'], data['economy_rate'], players[player_id]['Average Economy Rate Denominator']) 
                players[player_id]['Average Economy Rate'] = round((data['economy_rate'] + ((players[player_id]['Average Economy Rate Denominator']-1) * players[player_id]['Average Economy Rate'])) / players[player_id]['Average Economy Rate Denominator'], 3)
                # if players[player_id]['name'] == 'Shahbaz Ahmed':
                #     print(players[player_id]['Average Economy Rate'], data['economy_rate']) 
            
            players[player_id]['no. of wickets'] += data['wickets']
            players[player_id]['no. of balls thrown'] += balls_bowled
            players[player_id]['highest wickets taken in a match'] = max(players[player_id]['highest wickets taken in a match'], data['wickets'])
            players[player_id]['total centuries'] += 1 if data['runs'] >= 100 else 0
            players[player_id]['total halfcenturies'] += 1 if data['runs'] >= 50 else 0
            players[player_id]['total catches'] += data['catches']
            players[player_id]['total stumps'] += data['stumps']
            players[player_id]['total direct_runouts'] += data['direct_hit']
            players[player_id]['total indirect_runouts'] += data['indirect_hit']  
            players[player_id]['total avg fp'] = round((data['total_fp'] + (players[player_id]['total avg fp'] * (players[player_id]['matches']-1))) / players[player_id]['matches'], 3)
        else:
            players[player_id] = {
                'player_id': player_id,
                'name': data['name'],
                'matches': 1,
                'strike rate in all matches combined': round(data['strike_rate'], 3) if data['strike_rate'] is not None else None,
                'Strike rate denominator': 1 if data['balls'] > 0 else 0,
                'Total Runs Scored in all matches combined': int(data['runs']),
                'no. of fours': data['fours'],
                'no. of sixes': data['sixes'],
                'highest runs scored in a match': data['runs'],
                'Balls Played till now': data['balls'],
                'no. of dot_balls': data['dot_balls'],
                'maiden_overs': data['maidens'],
                'run conceded': data['conceded'],
                'Average Economy Rate Denominator': 1 if balls_bowled > 0 else 0,
                'Average Economy Rate': round(data['economy_rate'], 3) if data['economy_rate'] is not None else None,
                'no. of wickets': data['wickets'],
                'no. of balls thrown': balls_bowled,
                'highest wickets taken in a match': data['wickets'],
                'total centuries': 1 if data['runs'] >= 100 else 0,
                'total halfcenturies': 1 if data['runs'] >= 50 else 0,
                'total catches': data['catches'],
                'total stumps': data['stumps'],
                'total direct_runouts': data['direct_hit'],
                'total indirect_runouts': data['indirect_hit'],  
                'total avg fp': round(data['total_fp'], 3) 
            }



        # floor_overs_bowled = np.floor(total_overs_bowled)
        # maiden_over_rate = total_maidens / floor_overs_bowled if floor_overs_bowled > 0 else 0
        # avg_runs_conceded = total_runs_conceded / total_balls_bowled if total_balls_bowled > 0 else 0
        # wickets_taken = total_wickets / total_balls_bowled if total_balls_bowled > 0 else 0

   
# # Compute venue features
# venue_features = []
    # for venue_id, data in venue_features.items():
    if venue_data is None: 
        continue
    
    venue_id = venue_data['venue_id']
    if venue_id not in venues:
        venues[venue_id] = {
            'venue_id': venue_id,
            'venue_long': venue_data['venue_longitude'],
            'venue_lat': venue_data['venue_latitude'],
            'venue_name': venue_data['venue_name'],
            'matches': 1,
            'total_runs': venue_data['total_runs'] // 2,
            'total_wickets': venue_data['wickets'],
            'bowled_wickets': venue_data['bowled'],
            'caught_wickets': venue_data['caught'],
            'lbw_wickets': venue_data['lbw']
        }
    else: 
     
        # venues[venue_name]['name'] = venue_name
        venues[venue_id]['matches'] += 1
        venues[venue_id]['total_runs'] += venue_data['total_runs'] // 2
        venues[venue_id]['total_wickets'] += venue_data['wickets']
        venues[venue_id]['bowled_wickets'] += venue_data['bowled']
        venues[venue_id]['caught_wickets'] += venue_data['caught']
        venues[venue_id]['lbw_wickets'] += venue_data['lbw']
        


# exit()
# # write csv output 
players 
output_csv = "players.csv"
write_features_to_csv(players, output_csv)
write_features_to_csv(venues, "venue_features.csv")