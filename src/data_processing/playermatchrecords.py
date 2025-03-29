#Global scrapping
import json
import csv
import os
from collections import defaultdict
import pandas as pd

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
        elif 5 <= economy <= 5.99:
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
        'overs': 0
    })
    fielding_stats = defaultdict(lambda: {"catches": 0, "stumps": 0, "direct_runouts": 0, "indirect_runouts": 0})
    
    # dict to capture the batting entry order
    batting_entry = {}

    with open(json_file, 'r') as f:
        match = json.load(f)
    info = match.get("info", {})
    if info.get('gender','male') == "female":
        return None         
    balls_per_over = match.get("info", {}).get("balls_per_over", 6) # just 6
    
    for inning in match.get("innings", []):
        entry_counter = 0
        for over_index, over in enumerate(inning.get("overs", [])):
            legal_balls_in_over = 0
            over_runs = 0
            current_bowler = None
            for delivery in over.get("deliveries", []):
                batter = delivery.get("batter")
                non_striker = delivery.get("non_striker")
                if batter and batter not in batting_entry:
                    entry_counter += 1
                    batting_entry[batter] = entry_counter
                if non_striker and non_striker not in batting_entry:
                    entry_counter += 1
                    batting_entry[non_striker] = entry_counter
                bowler = delivery.get("bowler")
                extras = delivery.get("extras", {})
                extras_int = {k: int(v) for k, v in extras.items()}
                runs = delivery.get("runs", {})
                batter_runs = runs.get("batter", 0)
                total_runs = runs.get("total", 0)
                
                # Update batting stats (ignoring wides and no-balls for ball count)
                is_wide = 'wides' in extras
                is_noball = 'noballs' in extras
                if not is_wide and not is_noball:
                    batting_stats[batter]["balls"] += 1 # check for valid batter conceded balls 
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
                if not is_wide and not is_noball:
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
                                                           extras_int.get("penalty", 0))
                #correctly implemented as per T_20 the rules 
                
                if not is_wide and not is_noball and total_runs == 0: # incorrect check if not correct
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
                            elif kind == "bowled":
                                bowling_stats[bowler]["bowled"] += 1
                            elif kind in ['caught','caught and bowled']:
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
        stats["overs"] = round(stats["legal_balls"] / balls_per_over,3) if stats["legal_balls"] else 0.0  
    return match,batting_stats,bowling_stats,fielding_stats,batting_entry


def build_player_feature_map(json_file):
    # Reset global stats by processing the match freshly
    if process_match(json_file) is None:
        return None
    match, batting_stats, bowling_stats, fielding_stats,batting_entry = process_match(json_file)
    
    # Extract batting order from info.players (order reflects batting order)
    batting_order = {}
    players_info = match.get("info", {}).get("players", {})
    for team,players in players_info.items():
        idx = 1
        for player, order in batting_entry.items():
            if player in players:
                batting_order[player] = order
                idx += 1            
        for player in players:
            if player not in batting_order:
                batting_order[player] = idx
                idx += 1 
    registry = match.get("info", {}).get("registry", {}).get("people", {})
    team_rosters = match.get("info",{}).get('players',{})
    all_players = set()
    for team,players in team_rosters.items():
        if isinstance(players,list):
            for player in players:
                all_players.add((player,team))
    # make sure correct use of 11 lineup 
    final_stats = {}
    for player,team in all_players:
        #Batting stats 
        bat = batting_stats.get(player,{"runs": 0, "balls": 0, "fours": 0, "sixes": 0,'is_dismissed':False})
        runs = bat["runs"]
        balls_faced = bat["balls"] #make use ball_faced are logically-correct 
        fours = bat["fours"]
        sixes = bat["sixes"]
        is_dismissed = bat['is_dismissed'] #do we need it here
        batting_fp = compute_batting_fp(runs,fours,sixes,balls_faced,is_dismissed) # TODO include the strike_rate point 
        strike_rate = round((runs/balls_faced * 100),2) if balls_faced > 0 else 0.0 # why don't encapsulate it's fp in batting _fp
        
        #Bowling stats
        bowl = bowling_stats.get(player,{
            "legal_balls": 0, "dot_balls": 0, "maidens": 0, "runs_conceded": 0,
            "fours_conceded": 0, "sixes_conceded": 0, "wickets": 0, "overs": 0.0,
            "lbw": 0, "bowled": 0, "wides": 0, "noballs": 0, "overs_bowled": set(),
            #"hit_wicket": 0, "caught_bowled": 0,
        })
        overs = bowl["overs"]
        economy_rate = round(bowl['runs_conceded'] / overs,2) if overs > 0 else 0.0 # check for correct logic
        
        bowling_fp = compute_bowling_fp(
            bowl["wickets"], bowl["dot_balls"], bowl["maidens"],
            bowl["lbw"], bowl["bowled"], bowl["legal_balls"], bowl["runs_conceded"], overs
        )
        # make sure correct 
        
        #fielding stats
        field = fielding_stats.get(player,{"catches": 0, "stumps": 0, "direct_runouts": 0, "indirect_runouts": 0})
        fielding_fp = compute_fielding_fp(field["catches"], field["stumps"], field["direct_runouts"], field["indirect_runouts"])
        
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
         
        final_stats[player] = {
            "Team":team,
            "name": player,
            "player_id": registry.get(player, ""),
            "batting_position": batting_order.get(player, 0),
            # Batting features
            "runs": runs,
            "balls": balls_faced,
            "fours": fours,
            "sixes": sixes,
            "strike_rate": strike_rate,
            # Bowling features
            "overs_bowled": sorted(list(bowl.get("overs_bowled", set()))),
            "overs" : bowl.get("overs",0.0),
            "total_balls": bowl.get("legal_balls", 0),
            "dots": bowl.get("dot_balls", 0),
            "maidens": bowl.get("maidens", 0),
            "conceded": bowl.get("runs_conceded", 0),
            "fours_conceded": bowl.get("fours_conceded", 0),
            "sixes_conceded": bowl.get("sixes_conceded", 0),
            "wickets": bowl.get("wickets", 0),
            "LBW": bowl.get("lbw", 0),
            "Bowled": bowl.get("bowled", 0),
            "noballs": bowl.get("noballs", 0),
            "wides": bowl.get("wides", 0),
            "economy_rate": economy_rate,
            # Fielding features
            "catches": field.get("catches", 0),
            "stumping": field.get("stumps", 0),
            "direct_hit": field.get("direct_runouts", 0),
            "indirect_hit": field.get("indirect_runouts", 0),
            # fantasy points
            "strike_rate_fp":strike_rate_fp,
            "batting_fp": batting_fp,
            "bowling_fp": bowling_fp,
            "fielding_fp": fielding_fp,
            "total_fp": batting_fp + bowling_fp + fielding_fp            
        }
    return match,final_stats

def process_all_matches(global_folder):
    player_records = defaultdict(list)
    
    # Loop through each subfolder in the Global folder.
    for folder_name in os.listdir(global_folder):
        folder_path = os.path.join(global_folder, folder_name)
        if os.path.isdir(folder_path):
            # Loop through each file in the subfolder.
            for filename in os.listdir(folder_path):
                if filename.endswith(".json"):
                    json_file = os.path.join(folder_path, filename)
                    try:
                        match, feature_map = build_player_feature_map(json_file)
                    except Exception as e:
                        print(f"Error processing {json_file}: {e}")
                        continue
                    
                    match_date = match.get("info", {}).get("dates", 'NA')
                    event = match.get("info", {}).get("event", {}).get("name", 'NA')
                    match_id = os.path.splitext(filename)[0]
                    
                    for player, record in feature_map.items():
                        record_with_match = {
                            "date": match_date,
                            "event": event,
                            "match_id": match_id,
                            "teamname": record.get("Team", ""),
                            "batting_position": record.get("batting_position", 0),
                            "runs": record.get("runs", 0),
                            "balls": record.get("balls", 0),
                            "fours": record.get("fours", 0),
                            "sixes": record.get("sixes", 0),
                            "strike_rate": record.get("strike_rate", 0.0),
                            "overs_bowled": ",".join(map(str, record.get("overs_bowled", []))),
                            "overs": record.get("overs", 0.0),
                            "total_balls": record.get("total_balls", 0),
                            "dots": record.get("dots", 0),
                            "maidens": record.get("maidens", 0),
                            "conceded": record.get("conceded", 0),
                            "fours_conceded": record.get("fours_conceded", 0),
                            "sixes_conceded": record.get("sixes_conceded", 0),
                            "wickets": record.get("wickets", 0),
                            "LBW": record.get("LBW", 0),
                            "Bowled": record.get("Bowled", 0),
                            "noballs": record.get("noballs", 0),
                            "wides": record.get("wides", 0),
                            "economy_rate": record.get("economy_rate", 0.0),
                            "catches": record.get("catches", 0),
                            "stumping": record.get("stumping", 0),
                            "direct_hit": record.get("direct_hit", 0),
                            "indirect_hit": record.get("indirect_hit", 0),
                            "strike_rate_fp": record.get("strike_rate_fp", 0),
                            "batting_fp": record.get("batting_fp", 0),
                            "bowling_fp": record.get("bowling_fp", 0),
                            "fielding_fp": record.get("fielding_fp", 0),
                            "total_fp": record.get("total_fp", 0)
                        }
                        player_id = record.get("player_id")
                        if player_id:
                            player_records[player_id].append(record_with_match)
    
    # Sort the records for each player by date in descending order.
    for player_id, records in player_records.items():
        records.sort(key=lambda x: x["date"], reverse=True)
    return player_records

def write_player_csv(player_id, records, output_folder):
    # Define the columns in the desired order.
    columns = [
        "date", "event", "match_id", "teamname", "batting_position", "runs", "balls", "fours", "sixes",
        "strike_rate", "overs_bowled", "overs", "total_balls", "dots", "maidens", "conceded",
        "fours_conceded", "sixes_conceded", "wickets", "LBW", "Bowled", "noballs", "wides",
        "economy_rate", "catches", "stumping", "direct_hit", "indirect_hit", "strike_rate_fp",
        "batting_fp", "bowling_fp", "fielding_fp", "total_fp"
    ]
    output_csv = os.path.join(output_folder, f"{player_id}.csv")
    with open(output_csv, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        for record in records:
            writer.writerow(record)
    print(f"Written CSV for player {player_id} to {output_csv}")

if __name__ == "__main__":
    global_folder = r"C:\Users\kumar\IPL_Fantasy_Score_Prediction\src\Global"  # Path to your Global folder containing subfolders.
    output_folder = r"C:\Users\kumar\IPL_Fantasy_Score_Prediction\src\data_processing\Global_player_csvs"  # Folder to save individual player CSV files.
    os.makedirs(output_folder, exist_ok=True)
    
    player_records = process_all_matches(global_folder)
    
    # Write a CSV file for each player.
    for player_id, records in player_records.items():
        write_player_csv(player_id, records, output_folder)

