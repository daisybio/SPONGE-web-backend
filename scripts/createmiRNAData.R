library("Biostrings")
library("data.table")

#read fasta file for all miRNA's
fastaFile <- readDNAStringSet("C:\\Users\\Elly\\Uni\\NEAP\\resources\\hsa_all.fa")
seq_name = names(fastaFile)
seq = paste(fastaFile)

#process seq_name
id_type = c()
hs_nr = c()
mir_ID = c()
#split after "\s"
for (s in seq_name){
  split_info <- strsplit(s,"\\s+")
  hs_nr = c(hs_nr,split_info[[1]][1])
  mir_ID = c(mir_ID, split_info[[1]][2])
  if ("stem-loop" %in% split_info[[1]])
    id_type = c(id_type, "stem-loop")
  else
    id_type = c(id_type, "mature")
}

mirna_df <- data.frame(id_type, mir_ID, seq, hs_nr)

for (i in seq(from=1, to = 60, by = 1)){
  if (60 %% i == 0)
    print(i)
}

