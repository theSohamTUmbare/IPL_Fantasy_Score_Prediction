# Fantasy Points Prediction Model - Architecture

## Overview
This model is designed to predict the **fantasy points** a player will score in an upcoming match based on **historical performance, contextual match factors, and player form**. The approach involves **embedding-based representations** and a **sequential learning model** using **Transformers**.

## Data Categorization
We categorize the data into two types:

1. **Pre-Match Data (Available Before the Match)**  
   - This includes static and match-specific data known before the game starts.  
   - Used for both **historical** and **upcoming match predictions**.

2. **Post-Match Data (Available Only After the Match Ends)**  
   - Includes performance statistics that are unknown before the match.  
   - this needs to be predicted by our model

---

## Embedding Representations
To structure our data efficiently, we generate **three key embeddings**:

### 1. **Universal Player Embedding** [INPUT Embedding]
   - Represents a player's general career statistics and strengths.
   - Helps in capturing the **inherent skill level** of a player.
   - **Features:**
     - Total Runs Scored
     - Batting Average
     - Strike Rate
     - Total Wickets Taken
     - Bowling Average
     - Economy Rate
     - ... (Other aggregated career stats)

### 2. **Match-Specific Embedding** [INPUT Embedding]
   - Represents match-level contextual information affecting player performance.
   - Helps in capturing **situational advantages/disadvantages**.
   - **Features:**
     - Team 1 ID
     - Team 2 ID
     - Match Importance
     - Venue ID
     - Historical Average Scores at Venue
     - Temperature, Wind Speed
     - Toss Information
     - Team Captain
     - Opponent Players (11 players)

### 3. **Performance Embedding (Dynamic Form Representation)** [OUTPUT model should predict]
   - Represents a player's **recent form** using past performance data.
   - Generated sequentially across past matches.
   - **Features:**
     - Batting Order
     - Runs Scored
     - Balls Faced
     - Strike Rate
     - 4s, 6s
     - Dismissal Type (Categorical)
     - Partnership Contributions
     - % of Team's Total Runs
     - Wickets Taken
     - Economy Rate
     - Dot Balls, Overs Bowled
     - Boundary Conceded, Maiden Overs

### 4. There is one more embedding **Form Embedding**
 - we will have this Form embeddnig of the player on which we perform attention

---

## Model Architecture
The model follows a **sequential prediction approach** using **Transformers**.

### **Step 1: Embedding Generation**
Each player in the match will have:
   - **Universal Player Embedding**
   - **Match-Specific Embedding**
   - **Form Embedding** (initialized as zeros for the first match)

These embeddings are concatenated and processed through a Transformer-based model.

### **Step 2: Transformer for Sequential Form Prediction**
   - We use a Transformer model to predict the **next match's Form embedding** based on the sequence of past `n` matches.
   - Similar to **next-word prediction in NLP**, it learns temporal dependencies in performance trends.
   - Also model will predict the performance of the player (By which we calculate Fantasy Point) **ON this Output will having the LOSS** 

### **Step 3: Fantasy Points Prediction Model**
   - The **predicted performance embedding** match is passed to a smaller regression model.
   - This model outputs the **final fantasy points prediction** for each player.
   - **Loss is applied** to ensure that the predicted score aligns with actual fantasy points.

---

## Training Strategy
- **Sequential Learning:**  
  - The model is trained in a sequential manner using past `n` matches.
  - This ensures that form is captured dynamically.

- **Context-Based Training:**  
  - Matches with similar conditions (same venue, same opposition, etc.) are given priority while training.

- **Loss Function:**  
  - The **final fantasy points prediction** is optimized using **Mean Squared Error (MSE) Loss**.

---

## Summary
- **Universal Player Embedding**: Captures career stats.  
- **Match-Specific Embedding**: Captures match context.  
- **Performance Embedding**: Captures form over sequential matches.  
- **Form Embedding**: We leave it to the model to decide.
- **Transformer Model**: Predicts next match's performance embedding.  
- **Final Prediction Model**: Predicts fantasy points from performance embedding.  

This architecture ensures that the model **dynamically adapts to a player's form, accounts for match context, and generalizes well across different scenarios.** 🚀  
