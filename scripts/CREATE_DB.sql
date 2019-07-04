DROP DATABASE SPONGE;
DROP DATABASE SPONGE;
CREATE DATABASE SPONGE;
CREATE TABLE Dataset(
dataset_ID int NOT NULL AUTO_INCREMENT,
disease_name varchar(255),
data_origin varchar(255),
disease_type varchar(255),
download_url varchar(255),
PRIMARY KEY(dataset_ID)
);
CREATE TABLE Run(
run_ID int NOT NULL AUTO_INCREMENT,
dataset_ID int NOT NULL,
variance_cutoff int,
gene_expr_file varchar(255),
miRNA_expr_file varchar(255),
f_test boolean,
f_test_p_adj_threshold decimal(10,8),
coefficient_threshold decimal(10,8),
coefficient_direction varchar(255),
parallel_chunks_step1 int,
min_corr decimal(10,8),
parallel_chunks_step2 int,
number_of_datasets int,
number_of_samples int,
ks varchar(255),
m_max int,
log_level varchar(255),
PRIMARY KEY(run_ID),
FOREIGN KEY(dataset_ID) REFERENCES Dataset(dataset_ID)
);
CREATE TABLE Target_databases (
td_ID int NOT NULL AUTO_INCREMENT,
run_ID int NOT NULL,
db_used varchar(255),
version varchar(255),
url varchar(255),
PRIMARY KEY(td_ID),
FOREIGN KEY(run_ID) REFERENCES Run(run_ID)
);
CREATE TABLE Gene(
gene_ID int NOT NULL AUTO_INCREMENT,
description varchar(255),
gene_symbol varchar(255),
ensg_number varchar(255),
chromosome_name varchar(255),
start_pos int,
end_pos int,
gene_type varchar(255),
PRIMARY KEY(gene_ID)
);
CREATE TABLE Expression_data_gene(
expr_ID int NOT NULL AUTO_INCREMENT,
run_ID int NOT NULL,
gene_ID int NOT NULL,
exp_value decimal(10,8),
sample_ID varchar(255),
PRIMARY KEY(expr_ID),
FOREIGN KEY(run_ID) REFERENCES Run(run_ID),
FOREIGN KEY(gene_ID) REFERENCES Gene(gene_ID)
);
CREATE TABLE Selected_genes(
selected_genes_ID int NOT NULL AUTO_INCREMENT,
run_ID int NOT NULL,
gene_ID int NOT NULL,
PRIMARY KEY(selected_genes_ID),
FOREIGN KEY(run_ID) REFERENCES Run(run_ID),
FOREIGN KEY(gene_ID) REFERENCES Gene(gene_ID)
);
CREATE TABLE miRNA(
miRNA_ID int NOT NULL AUTO_INCREMENT,
id_type varchar(255),
mir_ID varchar(255),
seq varchar(999),
hs_nr varchar(255),
PRIMARY KEY(miRNA_ID)
);
CREATE TABLE Expression_data_miRNA(
expr_ID int NOT NULL AUTO_INCREMENT,
run_ID int NOT NULL,
miRNA_ID int NOT NULL,
expr_value decimal(10,8),
sample_ID varchar(255),
PRIMARY KEY(expr_ID),
FOREIGN KEY(run_ID) REFERENCES Run(run_ID),
FOREIGN KEY MiRNA(miRNA_ID) REFERENCES MiRNA(miRNA_ID)
);
CREATE TABLE Interactions_genegene(
interactions_genegene_ID int NOT NULL AUTO_INCREMENT,
run_ID int NOT NULL,
gene_ID1 int NOT NULL,
gene_ID2 int NOT NULL,
p_value decimal(10,8),
mscore decimal(10,8),
correlation decimal(10,8),
PRIMARY KEY(interactions_genegene_ID),
FOREIGN KEY(run_ID) REFERENCES Run(run_ID),
FOREIGN KEY(gene_ID1) REFERENCES Gene(gene_ID),
FOREIGN KEY(gene_ID2) REFERENCES Gene(gene_ID)
);
CREATE TABLE Interacting_miRNAs(
interacting_miRNAs_ID int NOT NULL AUTO_INCREMENT,
interactions_genegene_ID int NOT NULL,
miRNA_ID int NOT NULL,
PRIMARY KEY(interacting_miRNAs_ID),
FOREIGN KEY(interactions_genegene_ID) REFERENCES Interactions_genegene(interactions_genegene_ID),
FOREIGN KEY(miRNA_ID) REFERENCES MiRNA(miRNA_ID)
);
CREATE TABLE Survival_rate(
survival_ID int NOT NULL AUTO_INCREMENT,
gene_ID int NOT NULL,
dataset_ID int NOT NULL,
time_of_survival int,
probability decimal(10,8),
PRIMARY KEY(survival_ID),
FOREIGN KEY(gene_ID) REFERENCES Gene(gene_ID),
FOREIGN KEY(dataset_ID) REFERENCES Dataset(dataset_ID)
);
CREATE TABLE Network_analysis(
network_analysis_ID int NOT NULL AUTO_INCREMENT,
gene_ID int NOT NULL,
run_ID int NOT NULL,
eigenvektor decimal(65,8),
betweeness decimal(65,8),
node_degree decimal(65,8),
PRIMARY KEY(network_analysis_ID),
FOREIGN KEY(gene_ID) REFERENCES Gene(gene_ID),
FOREIGN KEY(run_ID) REFERENCES Run(run_ID)
);

