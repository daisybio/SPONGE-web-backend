# Optional variables for a backup script
MYSQL_USER="root"
MYSQL_PASS="a6/4qpQYx]QA"
MYSQL_HOST="10.162.163.20"
BACKUP_DIR=./$(date +%Y-%m-%dT%H_%M_%S);

test -d "$BACKUP_DIR" || mkdir -p "$BACKUP_DIR"
# Get the database list, exclude information_schema
echo mysql -u $MYSQL_USER --password=$MYSQL_PASS -h $MYSQL_HOST sponge -e 'show tables'
for table in $(mysql -u $MYSQL_USER --password=$MYSQL_PASS -h $MYSQL_HOST sponge -e 'show tables' | grep -v information_schema)
do
  $table = "gene_ontology"
  # dump each table in a separate file
  docker exec sponge-mysql-2 mysqldump -u $MYSQL_USER --password=$MYSQL_PASS sponge $table --single-transaction --quick --lock-tables=false | gzip > "$BACKUP_DIR/$table.sql.gz"
  break
done