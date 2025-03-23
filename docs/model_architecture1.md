# Complete Model and Workflow

---

## Summary and Key Points of the Model and workflow

### **Input Fusion for Transformer:**
- Project \( v_1 \) and \( v_2 \) to align with \( v_3 \).
- Concatenate and fuse to form \( x_t' \) for each match.
- Add positional encoding to maintain sequence order.

### **Transformer Decoder:**
- Process the sequence \( \{ x_1', \dots, x_T' \} \) using self-attention and FFNs.
- Generate context-rich hidden states \( h_t \).

### **Dual Output Generation:**
- **Next Form Embedding:**
  - \( \hat{v}_3^{t+1} \) is predicted via a dedicated projection layer from \( h_t \).
- **Fantasy Score Prediction:**
  - For match \( t+1 \), fuse \( \hat{v}_3^{t+1} \) with \( v_2^{t+1} \) and \( v_1^{t+1} \), and pass through an MLP to get \( \hat{y}^{t+1} \).

### **Loss and Training:**
- The fantasy score prediction is directly supervised via a loss .
- This loss propagates through the MLP, projection layer, and transformer, training the model end-to-end.
- Separate projection and concatenation layers are used in the MLP to handle the prediction task, distinct from the transformer input fusion layers.

---

## 1. Data Preparation

For each match, you have three types of input embeddings along with the ground truth fantasy score:

- **v1: Player Embedding**
  - Encodes static player universal characteristics.
- **v2: Match Situation Embedding**
  - Encodes match-specific situational context (e.g., opposition, venue, weather) for that player.
- **v3: Form Embedding**
  - Encodes the player’s performance or “form” in the given match.
- **Ground Truth:**
  - The fantasy score for that match.

---

## 2. Transformer Input Processing

### A. Projection & Fusion for Transformer

#### **Projection:**

**v1 and v2 Projection:**
Use learned linear layers to project `v1` and `v2` into the same latent space (dimension) as `v3`.

\(v_1' = W_1 \cdot v_1 + b_1, \quad v_2' = W_2 \cdot v_2 + b_2\)

This aligns all embeddings to a common dimension.

#### **Concatenation & Fusion:**

**Concatenate:**
For each match \(t\), concatenate the projected embeddings with the form embedding:

\(x_t = [ v_3^t ; v_1' ; v_2' ]\)

**Fusion Layer:**
Pass the concatenated vector through a linear layer (optionally with an activation function) to obtain a fused representation \(x_t'\) in the transformer’s model dimension:

\(x_t' = W_{fusion} \cdot x_t + b_{fusion}\)

**Positional Encoding:**
Add positional encodings to \(x_t'\) so the transformer understands the sequential order of matches.

---

## 3. Transformer Decoder Processing

### **Input Sequence:**

The sequence  (each to\(\{ x_1', x_2', \dots, x_T' \}\)ken represents a match) is fed into a stack of transformer decoder blocks.

### **Within Each Transformer Block:**

- **Masked Multi-Head Self-Attention:**
  - Allows each token to attend to previous matches (autoregressive flow).
- **Feed-Forward Network (FFN):**
  - Applies non-linear transformations to enrich the representation.
- **Residual Connections & Layer Normalization:**
  - Ensure stable gradient flow and effective training.

**Hidden State ****************************************************************\(h_t\)****************************************************************:**
After processing, the output \(h_t\) for match \(t\) is a contextually enriched representation that encapsulates historical form, player details, and match context.

---

## 4. Output Generation

### **A. Next Form Embedding Prediction (Autoregressive Output)**

#### **Objective:**

Predict the next match’s form embedding \(\hat{v}_3^{t+1}\) based on the current context \(h_t\).

#### **Projection Layer:**

Apply a dedicated projection layer to \(h_t\) to obtain the predicted form embedding:

\(\hat{v}_3^{t+1} = W_{proj} \cdot h_t + b_{proj}\)


### **B. Fantasy Score Prediction**

#### **Objective:**

Predict the fantasy score for the upcoming match using both the predicted form embedding and the actual match context.

#### **Fusion for Prediction:**

For match \(t+1\), fuse the following:

- The predicted form embedding \(\hat{v}_3^{t+1}\) from the transformer.
- The actual match situation embedding \(v_2^{t+1}\) (which is available at inference/training time).
- The player embedding \(v_1^{t+1}\) (included for consistency, even if largely static).

The fusion can be done via concatenation:

\(z_{t+1} = [ \hat{v}_3^{t+1} ; v_2^{t+1} ; v_1^{t+1} ]\)

#### **MLP Prediction Head:**

Pass \(z_{t+1}\) through an MLP (or simply a linear layer if appropriate) to predict the fantasy score:

\(\hat{y}^{t+1} = MLP(z_{t+1})\)

And finally get the Loss by the Ground Truth fantasy score of the player in that match




