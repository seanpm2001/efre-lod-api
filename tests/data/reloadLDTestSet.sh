#!/bin/bash
# inject data into elasticsearch


# requirements: 
#  - jq
#  - awk
#  - curl
# optional:
#  - esbulk
# usage:
#  reloadLDTestSet.sh [PATH_TO_LDJ] [ELASTICSEARCH_IP]
set -e

host=http://${2}:9200

# tmp_folder is used for generating jsonl that can be
# feed directly to the elasticsearch Bulk API
tmp_folder="/tmp/lod-reloadLDTestSet"
mkdir -p $tmp_folder

generate_esbulk (){
    # used in case esbulk is not available. This generates jsonl objects
    # that can be used for the bulk API of elasticsearch
    infile="$1"
    index="$2"
    doctype="$3"
    id="$4"

    while read -r line; do
        es_id=`echo "${line}" | jq -r ".[\"$id\"]"`
        if [ "$es_id" == "" ]; then
            echo "id not found: ${line}"
            exit 1
        fi
        echo -e '{ "index": { "_index": "'"${index}"'", "_type": "'"${doctype}"'", "_id": "'"${es_id}"'"}}'"\n${line}\n"
    done < "${infile}"
}

version (){
    # changes version string like "7.6.2" into "70006002000" which is comparable
    # from: https://stackoverflow.com/a/37939589
    #       via https://apple.stackexchange.com/a/123408/11374
    echo "$@" | awk -F. '{ printf("%d%03d%03d%03d\n", $1,$2,$3,$4); }'
}

echo -n "waiting for elasticsearch to start"
while ! curl $host 2>/dev/null ; do 
    sleep 1
    echo -n "…"
done
echo ""

esversion="$(curl $host 2>/dev/null | jq -r '.version.number')"
echo "$esversion"

for i in `ls ${1}/*`; do
    # get the file in the directory $i as index
    index=`echo ${i} | rev |cut -d "/" -f1 | rev`
    string=${host}/${index}
    # curl -XDELETE ${string} 2>/dev/null || true ; echo ""
    if [ "${index}" != "swb-aut" ] && [ "${index}" != "kxp-de14" ]; then
        id="identifier"
        # to be consistentent with es versions > 7 the doctype must be "_doc"
        # doctype="schemaorg"
        doctype="_doc"
    else
        # use MARC field 001 as index
        id="001"
        # doctype="mrc"
        doctype="_doc"
    fi
    if [ $(version $esversion) -lt $(version "7") ]; then
        curl -XPUT ${string} -d '{"mappings":{"'"${doctype}"'":{"date_detection":false}}}' \
                             -H "Content-Type: application/json" 2>/dev/null; echo ""
    elif [ $(version $esversion) -lt $(version "8") ]; then
        # force doctype to be "_doc"
        doctype="_doc"
        curl -XPUT ${string} -d '{"mappings":{"date_detection":false}}' \
                             -H "Content-Type: application/json" 2>/dev/null; echo ""
    fi

    if which esbulk >/dev/null 2>&1; then
        # prefer esbulk for data injection to elasticsearch
        cat "${i}" | esbulk -server ${host} -type ${doctype} -index ${index} -id ${id} -w 1 -verbose
    else
        # alternative to use the bulk-API from elasticsearch
        if [ ! -f ${tmp_folder}/${index}.jsonl ]; then
            generate_esbulk $i $index $doctype $id >> ${tmp_folder}/${index}.jsonl
        fi
        curl -XPOST "${host}/_bulk" \
             -H "Content-Type: application/x-ndjson"  \
             --data-binary "@${tmp_folder}/${index}.jsonl" >/dev/null 2>&1
        curl -XPOST "${host}/${index}/_flush" 2>/dev/null
    fi
done

# remove tmp folder
rm -r ${tmp_folder}
