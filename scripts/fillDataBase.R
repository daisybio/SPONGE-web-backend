#script will fill up gene-gene-interaction table in database
library(dbConnect)
library(RMySQL)

#connect to database
drv <- dbDriver("MySQL")
con = dbConnect(drv, user = 'root', password= "Pfiffi.kus14", dbname = 'sponge',host='localhost')

#list all tables in database
dbListTables(con)

#load id_ensg_map
load("C:\\Users\\Elly\\Documents\\GitHub\\SPONGE-web-backend\\resources\\table_interactions_genegene\\id_ensg_map.RData")

#load sponge_result data
load("C:\\Users\\Elly\\Uni\\NEAP\\data\\results_markus\\bladder urothelial carcinoma_sponge_results.RData")

#set run_id (the same for one sponge_result file) = "file number" = run_id as foreign key in database
run <- 1;

#expand sponge_result to fit table definition
run_Id <- rep(run, each = length(sponge_effects$geneA))
gene_ID1 <- geneIdEnsgMap$gene_id[match(sponge_effects$geneA, geneIdEnsgMap$ensg_number)]
gene_ID2 <- geneIdEnsgMap$gene_id[match(sponge_effects$geneB, geneIdEnsgMap$ensg_number)]

data <- data.frame(run_Id, gene_ID1, gene_ID2, sponge_effects$p.adj, sponge_effects$mscor, sponge_effects$cor)
colnames(data) <- c("run_id", "gene_ID1", "gene_ID2", "p_value", "mscore", "correlation")

#insert data into database
dbWriteTable(con, name = "interactions_genegene", value = data[1:10,], overwrite = FALSE, append = TRUE, row.names = FALSE)

#disconnect from db
dbDisconnect(con)