import os
import json
import csv

# Directory where your JSON files are stored.
json_dir = r"C:\Users\kumar\IPL_Fantasy_Score_Prediction\src\Global"  # update this path to your directory

def process_matches(global_folder, output_csv="matches_info.csv"):
# List to hold each match’s info.
    if os.path.exists(output_csv):
        print("Matches are already processed! No further processing needed.")
        return
    
    matches = []
    # Iterate over all JSON files in the directory.
    for subdir in os.listdir(global_folder):
        subdir_path = os.path.join(global_folder, subdir)
        if os.path.isdir(subdir_path):
            for file in os.listdir(subdir_path):
                if file.endswith(".json"):
                    json_file_path = os.path.join(subdir_path, file)
                    match_id = os.path.splitext(file)[0]
                    print(f"Processing match: {match_id}")
                    with open(json_file_path, "r") as f:
                        data = json.load(f)
                    info = data.get('info',{})
                    if info.get('gender','male') == "female": 
                        continue  
                    match_number = info.get("event", {}).get("match_number", "")
                    event = info.get("event", {}).get("name", "")
                    season = info.get("season", "")
                    city = info.get("city", "")
                    teams = info.get("teams", [])
                    team1 = teams[0] if len(teams) > 0 else ""
                    team2 = teams[1] if len(teams) > 1 else ""
                    toss = info.get("toss", {})
                    toss_winner = toss.get("winner", "")
                    toss_decision = toss.get("decision", "")
                    venue = info.get("venue", "")
                    winner = info.get("outcome", {}).get("winner", "")
                    player_of_match_list = info.get("player_of_match", [])
                    player_of_match = player_of_match_list[0] if player_of_match_list else ""
                    matches.append({
                        "match_id": match_id,
                        "event": event,
                        "season": season,
                        "match_number": match_number,
                        "city": city,
                        "team1": team1,
                        "team2": team2,
                        "toss_winner": toss_winner,
                        "toss_decision": toss_decision,
                        "venue": venue,
                        "winner": winner,
                        "player_of_match": player_of_match
                    })
    with open(output_csv,'w',newline='') as csvfile:
        fieldnames = ["match_id", "event", "season","match_number", "city", "team1", "team2", 
                      "toss_winner", "toss_decision", "venue", "winner", "player_of_match"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for match in matches:
            writer.writerow(match)
    print(f"CSV file '{output_csv}' created with {len(matches)} matches.")
           
if __name__ == "__main__":
    global_folder = r"C:\Users\kumar\IPL_Fantasy_Score_Prediction\src\Global"  
    process_matches(global_folder)
    
