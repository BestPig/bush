#!/bin/bash

TEMP_DIR=$(mktemp -d)
SERVER_DIR=$(pwd)/server/

function cleanup {
    rm -f $SERVER_DIR/data/*
}

cd "$TEMP_DIR" > /dev/null

cleanup

echo "ff" > file1.txt
mkdir dir
echo "ff" > dir/file2.txt

function test1 {
    echo "Checking simple upload without specifing tag"
    bush up file1.txt

    sqlite3 "$SERVER_DIR"/data/files.sqlite 'select * from files' | wc -l | grep -e '^1$'

    if [[ $? -ne 0 ]] ; then
	echo "Fail test1."
	exit 1
    fi

    cleanup
}

function test2 {
    echo "Checking simple upload with tag"
    bush up file1.txt thetag

    sqlite3 "$SERVER_DIR"/data/files.sqlite 'select * from files where tag = "thetag"' | wc -l | grep -e '^1$'

    if [[ $? -ne 0 ]] ; then
	echo "Fail test2."
	exit 1
    fi

    cleanup
}

function test3 {
    echo "Checking multiple files upload with tag"
    bush up file1.txt dir/file2.txt filestag

    sqlite3 "$SERVER_DIR"/data/files.sqlite 'select * from files where tag = "filestag"' | wc -l | grep -e '^1$'

    if [[ $? -ne 0 ]] ; then
	echo "Fail test3."
	exit 1
    fi

    cleanup
}

function test4 {
    echo "Checking directory upload without tag"
    bush up $TEMP_DIR

    sqlite3 "$SERVER_DIR"/data/files.sqlite 'select * from files' | wc -l | grep -e '^1$'

    if [[ $? -ne 0 ]] ; then
	echo "Fail test4."
	exit 1
    fi

    cleanup
}

function test5 {
    echo "Checking directory upload without tag (Ending / in dirname)"
    bush up $TEMP_DIR/

    sqlite3 "$SERVER_DIR"/data/files.sqlite 'select * from files' | wc -l | grep -e '^1$'

    if [[ $? -ne 0 ]] ; then
	echo "Fail test5."
	exit 1
    fi

    cleanup
}


function test6 {
    echo "Checking directory upload with tag"
    bush up $TEMP_DIR/ dirtag

    sqlite3 "$SERVER_DIR"/data/files.sqlite 'select * from files where tag = "dirtag"' | wc -l | grep -e '^1$'

    if [[ $? -ne 0 ]] ; then
	echo "Fail test6."
	exit 1
    fi

    cleanup
}

test1
test2
test3
test4
test5
test6

rm -rf "$TEMP_DIR"
