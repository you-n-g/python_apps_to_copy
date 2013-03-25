#!/bin/bash
DB_DIR=`dirname $0`
if [ ! -e  $DB_DIR/../db/ ]; then 
    mkdir $DB_DIR/../db/
fi

if [ ! -e  $DB_DIR/../db/backups/ ]; then 
    mkdir $DB_DIR/../db/backups/
fi


if [ ! -e  $DB_DIR/../db/backups/pro/ ]; then 
    mkdir $DB_DIR/../db/backups/pro/
fi

$DB_DIR/export_sql.sh $DB_DIR/../db/backups/pro/`date +%Y-%m-%d.%H-%M-%S.$RANDOM`.sql
