#load package
library("biomaRt")

#list of the available attributes for a given mart and species
ensembl = useMart("ensembl", dataset = "hsapiens_gene_ensembl", host="uswest.ensembl.org", ensemblRedirect = FALSE)
attributes <- listAttributes(ensembl)

#list of all needed EsNG_Nr. OR gene_symbols
load("C:\\Users\\Elly\\Documents\\GitHub\\SPONGE-Masterpraktikum\\resources\\ensg_uniq.RData")
gene_ensg <- genes
gene_symbol <- c('AC006126', 'PBOV1')
     
#getBM" function allow you to build a BioMart query using a list of mart filters and attributes
#alternative one: search for ENSG-NR
gene_info = getBM(attributes=c('description', 'hgnc_symbol','ensembl_gene_id','chromosome_name','start_position','end_position', 'gene_biotype'), filters = 'ensembl_gene_id', values = gene_ensg[1], mart = ensembl)

for (i in seq(from = 2, to = length(genes), by = 1000)){
  x = i + 999
  info <- getBM(attributes=c('description', 'hgnc_symbol','ensembl_gene_id','chromosome_name','start_position','end_position', 'gene_biotype'), filters = 'ensembl_gene_id', values = gene_ensg[i:x], mart = ensembl)
  gene_info <- rbind(gene_info, info) 
  print(paste("i", i,",x," ,x,",gene_info_size:", length(gene_info[,1])))
}

#alternative two: filter for gene_symbol
gene_info_2 <- getBM(attributes=c('hgnc_symbol','ensembl_gene_id','description','chromosome_name','start_position','end_position', 'gene_biotype'), filters = 'hgnc_symbol', values = gene_symbol, mart = ensembl)
save(gene_info, file = "genes_information.RData")
