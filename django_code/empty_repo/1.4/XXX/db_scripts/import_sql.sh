#!/bin/bash
CDIR=`dirname $0`
source $CDIR/../db/config.sh

function drop_all_tables() {
    DB=$1
    ALL_TABLES=`echo "show tables;" | mysql -u$USERNAME -p$PASSWORD $DB`
    for tb in ${ALL_TABLES[*]}; do  
        echo "SET FOREIGN_KEY_CHECKS = 0; DROP TABLE IF EXISTS \`$tb\`; SET FOREIGN_KEY_CHECKS = 1;" | mysql -u$USERNAME -p$PASSWORD $DB 
    done
}

function import_db() {
    DB=$1
    drop_all_tables $DB 
    mysql -u$USERNAME -p$PASSWORD $DB < $2
}

if [ $# -eq 1 ]; then
    if [ -e $1 ]; then 
        import_db $WWW_DB $1 #其他表在后
        echo "$WWW_DB 导入成功"
    else
        echo "The file doesn't exsist"
    fi  
else
    echo 'The number of the args is not right'
fi
