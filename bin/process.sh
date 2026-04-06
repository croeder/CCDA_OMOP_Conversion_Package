#!/usr/bin/env bash


# prep directories
mkdir logs 2> /dev/null
mkdir output 2> /dev/null
rm -f logs/*
rm -f output/*

# run unit tests
### python3 -m  unittest src.ccda_to_omop.test.test_value_transformations_concat

# run the main conversion and compare
cd src
#python3 -m ccda_to_omop.layer_datasets -d resources -c
python3 -m ccda_to_omop.data_driven_parse -d ../resources 

# load into DuckDB for constraint errors
## python3 -m omop.setup_omop

