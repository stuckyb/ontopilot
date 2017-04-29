#!/bin/bash

mkdir -p tmp
cd tmp
rm -rf *
cp ../elk-reasoner/elk-distribution/target/elk-distribution-0.5.0-SNAPSHOT-owlapi-library.zip .
unzip elk-distribution-0.5.0-SNAPSHOT-owlapi-library.zip
cd ..
cp tmp/elk-distribution-0.5.0-SNAPSHOT-owlapi-library/elk-owlapi.jar elk-0.5.0-SNAPSHOT-owlapi-datatypes.jar
rm -r tmp

