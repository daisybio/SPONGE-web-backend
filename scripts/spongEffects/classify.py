import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import confusion_matrix, accuracy_score
import igraph as ig
from joblib import Parallel, delayed
import argparse
import json

def filter_network(network, mscor_threshold=0.1, padj_threshold=0.01):
    return network[(network['mscor'] > mscor_threshold) & (network['p_adj'] < padj_threshold)]

def combined_centrality(CentralityMeasures):
    CombinedCentrality_Score = []
    for v in range(CentralityMeasures.shape[0]):
        combined_c = 0
        for m in CentralityMeasures.columns:
            max_c = CentralityMeasures[m].max()
            min_c = CentralityMeasures[m].min()
            gene_c = CentralityMeasures.at[v, m]
            combined_c += ((max_c - gene_c) / (max_c - min_c) ** 2)
        CombinedCentrality_Score.append(0.5 * combined_c)
    return CombinedCentrality_Score

def weighted_degree(network, undirected=True, Alpha=1):
    Nodes = pd.DataFrame({
        'Nodes': pd.concat([network['geneA'], network['geneB']]).unique(),
        'Nodes_numeric': range(1, len(pd.concat([network['geneA'], network['geneB']]).unique()) + 1)
    })
    geneA_numeric = Nodes['Nodes_numeric'][network['geneA'].map(Nodes.set_index('Nodes')['Nodes_numeric'])]
    geneB_numeric = Nodes['Nodes_numeric'][network['geneB'].map(Nodes.set_index('Nodes')['Nodes_numeric'])]
    Input_network = pd.DataFrame({'Sender': geneA_numeric, 'Receiver': geneB_numeric, 'Weight': network['mscor']})
    
    if undirected:
        Undirected_net = Input_network.groupby(['Sender', 'Receiver']).sum().reset_index()
        Weighted_degree = Undirected_net.groupby('Sender')['Weight'].apply(lambda x: (x ** Alpha).sum()).reset_index()
        Nodes['Weighted_degree'] = Nodes['Nodes_numeric'].map(Weighted_degree.set_index('Sender')['Weight'])
        return Nodes

def define_modules(network, central_modules=False, remove_central=True, set_parallel=False, module_creation="centrality", param=None):
    if "GeneA" in network.columns:
        network = network.rename(columns={"GeneA": "geneA"})
    if "GeneB" in network.columns:
        network = network.rename(columns={"GeneB": "geneB"})
    
    if module_creation == "louvain":
        graph = ig.Graph.DataFrame(network, directed=False)
        cluster = graph.community_multilevel(weights='Weight', resolution=param)
        Sponge_Modules = {i: cluster[i] for i in range(len(cluster))}
        return Sponge_Modules
    
    # Add other module creation methods here...

    if set_parallel:
        Sponge_Modules = Parallel(n_jobs=-1)(delayed(lambda i: network[(network['geneA'] == central_modules['gene'][i]) | (network['geneB'] == central_modules['gene'][i])]) for i in range(len(central_modules)))
    else:
        Sponge_Modules = []
        for i in range(len(central_modules)):
            Sponge_temp = network[(network['geneA'] == central_modules['gene'][i]) | (network['geneB'] == central_modules['gene'][i])]
            if not Sponge_temp.empty:
                Module_temp = pd.concat([Sponge_temp['geneA'], Sponge_temp['geneB']]).unique()
                Module_temp = Module_temp[Module_temp != central_modules['gene'][i]]
                Sponge_Modules.append(Module_temp)
    
    if remove_central:
        Sponge_Modules_DoubleRemoved = [module[~np.isin(module, central_modules['gene'])] for module in Sponge_Modules]
        return Sponge_Modules_DoubleRemoved
    else:
        return Sponge_Modules

def exact_match_summary(data, lev=None, model=None):
    metric = (data['obs'] == data['pred']).sum() / len(data['obs'])
    return {'Exact_match': metric}

def rf_classifier(Input_object, K, rep, metric="Exact_match", tunegrid=None, set_seed=42):
    np.random.seed(set_seed)
    X = Input_object.drop(columns=['Class'])
    y = Input_object['Class']
    rf_model = RandomForestClassifier()
    scores = cross_val_score(rf_model, X, y, cv=K, scoring=metric)
    rf_model.fit(X, y)
    Confusion_matrix = confusion_matrix(y, rf_model.predict(X))
    return {'Model': rf_model, 'ConfusionMatrix_training': Confusion_matrix, 'Scores': scores}

def main(expr, model_path, output, local, log, mscor, fdr, min_size, max_size, min_expr, method):
    # Load expression data
    expr_data = pd.read_csv(expr, sep='\t')
    
    # Load model
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Filter network
    filtered_network = filter_network(expr_data, mscor_threshold=mscor, padj_threshold=fdr)
    
    # Define modules
    modules = define_modules(filtered_network, module_creation=method)
    
    # Calculate centrality scores
    centrality_scores = combined_centrality(filtered_network)
    
    # Train Random Forest classifier
    rf_model = rf_classifier(filtered_network, K=5, rep=3)
    
    # Save output
    with open(output, 'w') as f:
        json.dump(rf_model, f)
    
    if log:
        print("Classification completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Classify ceRNA network.')
    parser.add_argument('--expr', type=str, required=True, help='Expression data file')
    parser.add_argument('--model_path', type=str, required=True, help='Path to the model file')
    parser.add_argument('--output', type=str, required=True, help='Output file')
    parser.add_argument('--local', action='store_true', help='Run locally')
    parser.add_argument('--log', action='store_true', help='Enable logging')
    parser.add_argument('--mscor', type=float, default=0.1, help='mscor threshold')
    parser.add_argument('--fdr', type=float, default=0.05, help='FDR threshold')
    parser.add_argument('--min_size', type=int, default=100, help='Minimum module size')
    parser.add_argument('--max_size', type=int, default=2000, help='Maximum module size')
    parser.add_argument('--min_expr', type=int, default=10, help='Minimum expression')
    parser.add_argument('--method', type=str, default='gsva', help='Method for module creation')
    
    args = parser.parse_args()
    main(args.expr, args.model_path, args.output, args.local, args.log, args.mscor, args.fdr, args.min_size, args.max_size, args.min_expr, args.method)
