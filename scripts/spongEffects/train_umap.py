import pandas as pd
import numpy as np
import umap
import joblib
import json
import os
from sklearn.preprocessing import StandardScaler

def process_level(level, out_dir):
    csv_path = os.path.join(out_dir, f"tcga_{level}_training.csv")
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return
        
    print(f"Loading {csv_path}...")
    df = pd.read_csv(csv_path, index_col=0)
    
    # Look for label column
    outcome_col = [col for col in df.columns if col == '.outcome' or col == 'Class']
    if outcome_col:
        classes = df[outcome_col[0]]
        features = df.drop(columns=outcome_col)
    else:
        classes = pd.Series(["Unknown"] * len(df), index=df.index)
        features = df
        
    # Scale features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    
    # Train UMAP model
    print(f"Training UMAP for {level} with shape {features.shape}...")
    reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, metric='euclidean', random_state=42)
    embedding = reducer.fit_transform(scaled_features)
    
    # Save scaler, reducer, and feature names
    model_save_path = os.path.join(out_dir, f"umap_{level}_model.joblib")
    joblib.dump({
        'scaler': scaler,
        'reducer': reducer,
        'feature_names': list(features.columns)
    }, model_save_path)
    print(f"Saved UMAP model to: {model_save_path}")
    
    # Save coordinates dictionary
    embedding_dict = {}
    for idx, (patient, row) in enumerate(df.iterrows()):
        embedding_dict[patient] = {
            'x': float(embedding[idx, 0]),
            'y': float(embedding[idx, 1]),
            'class': str(classes.iloc[idx])
        }
        
    json_save_path = os.path.join(out_dir, f"umap_{level}_tcga_coords.json")
    with open(json_save_path, 'w') as f:
        json.dump(embedding_dict, f)
    print(f"Saved coordinates to: {json_save_path}")

if __name__ == "__main__":
    out_dir = "/Users/lena/Projects/SPONGE/SPONGE-web-backend/umap_data"
    for lvl in ["gene", "transcript"]:
        process_level(lvl, out_dir)
print("UMAP Training script finished.")
