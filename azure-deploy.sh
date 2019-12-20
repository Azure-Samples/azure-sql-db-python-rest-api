#!/bin/bash

set -euo pipefail

# Make sure these values are correct for your environment
resourceGroup="azure-sql-db-python-rest-api"
appName="azure-sql-db-python-rest-api"
location="WestUS2" 

# Change this if you are using your own github repository
gitSource="https://github.com/yorek/azure-sql-db-python-rest-api.git"

az group create \
    -n $resourceGroup \
    -l $location

az appservice plan create \
    -g $resourceGroup \
    -n "linux-plan" \
    --sku B1 \
    --is-linux

az webapp create \
    -g $resourceGroup \
    -n $appName \
    --plan "linux-plan" \
    --runtime "PYTHON|3.7" \
    --deployment-source-url $gitSource \
    --deployment-source-branch master

az webapp config connection-string set \
    -g $resourceGroup \
    -n $appName \
    --settings WWIF=$SQLAZURECONNSTR_WWIF \
    --connection-string-type=SQLAzure
