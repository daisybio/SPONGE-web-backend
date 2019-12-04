library(dbConnect)
library(RMySQL)

#connect to database
drv <- dbDriver("MySQL")
con = dbConnect(drv, user = 'root', password= "Pfiffi.kus14", dbname = 'sponge',host='localhost')

#list all tables in database
dbListTables(con)

#inserting data into mysql table
#test_df <- data.frame("a" = c(1:10), "b" = letters[1:10])
dbWriteTable(con, name = "dataset", value = data, overwrite = FALSE, append = TRUE, row.names = FALSE)

#disconnect from db
dbDisconnect(con)

