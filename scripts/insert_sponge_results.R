library(dbConnect)
library(RMySQL)

#connect to database
drv <- dbDriver("MySQL")
con = dbConnect(drv, user = 'root', password= "in5ri@habboDE", dbname = 'SPONGE2',host='localhost')

load("D:\\MasterPraktikum_OUTSOURCED\\result_examples\\thymoma_sponge_results.RData")

#list all tables in database
dbListTables(con)

#inserting data into mysql table
#test_df <- data.frame("a" = c(1:10), "b" = letters[1:10])

query<-"SELECT gene_ID FROM gene WHERE "

#paste0("ensg_numer='",sponge_effects$geneA, "'", collapse = " or ")


geneA <-  dbGetQuery(con,paste0(query, "ensg_number ='", sponge_effects$geneA[1], "';"))
for (gene in sponge_effects$geneA[2:length(sponge_effects$geneA)]){
  geneA <- rbind(geneA, dbGetQuery(con,paste0(query, "ensg_number ='", gene, "';")))
}

geneB <-  dbGetQuery(con,paste0(query, "ensg_number ='", sponge_effects$geneB[1], "';"))
for (gene in sponge_effects$geneB[2:length(sponge_effects$geneB)]){
  geneB <- rbind(geneA, dbGetQuery(con,paste0(query, "ensg_number ='", gene, "';")))
}

dbWriteTable(con, name = "dataset", value = data, overwrite = FALSE, append = TRUE, row.names = FALSE)

#disconnect from db
dbDisconnect(con)

