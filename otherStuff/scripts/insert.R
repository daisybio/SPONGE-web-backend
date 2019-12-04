library(dbConnect)
library(RMySQL)

#connect to database
drv <- dbDriver("MySQL")
con = dbConnect(drv, user = 'root', password= "in5ri@habboDE", dbname = 'SPONGE2',host='localhost')

data <- read.table("C:\\Users\\Marku\\Dropbox\\UNI\\Semester2\\NEAP\\Database\\cancer_tcga_url.txt", sep="\t", header=FALSE)
colnames(data)<-c("disease_name","data_origin","disease_type","download_url")

#list all tables in database
dbListTables(con)

#inserting data into mysql table
#test_df <- data.frame("a" = c(1:10), "b" = letters[1:10])
dbWriteTable(con, name = "dataset", value = data, overwrite = FALSE, append = TRUE, row.names = FALSE)

#disconnect from db
dbDisconnect(con)

