#!/bin/bash

set -euo pipefail

# Make sure these values are correct for your environment
resourceGroup="dm-api-01"
appName="dm-api-01"
location="WestUS2" 

# Change this if you are using your own github repository
gitSource="https://github.com/Azure-Samples/azure-sql-db-python-rest-api.git"

# Make sure connection string variable is set

if [[ -z "${SQLAZURECONNSTR_WWIF:-}" ]]; then
	echo "Plase export Azure SQL connection string:";
    echo "export SQLAZURECONNSTR_WWIF=\"your-connection-string-here\"";
	exit 1;
fi

echo "Creating Resource Group...";
az group create \
    -n $resourceGroup \
    -l $location

echo "Creating Application Service Plan...";
az appservice plan create \
    -g $resourceGroup \
    -n "linux-plan" \
    --sku B1 \
    --is-linux

echo "Creating Application Insight..."
az resource create \
    -g $resourceGroup \
    -n $appName-ai \
    --resource-type "Microsoft.Insights/components" \
    --properties '{"Application_Type":"web"}'

echo "Reading Application Insight Key..."
aikey=`az resource show -g $resourceGroup -n $appName-ai --resource-type "Microsoft.Insights/components" --query properties.InstrumentationKey -o tsv`

echo "Creating Web Application...";
az webapp create \
    -g $resourceGroup \
    -n $appName \
    --plan "linux-plan" \
    --runtime "PYTHON|3.7" \
    --deployment-source-url $gitSource \
    --deployment-source-branch master

echo "Configuring Connection String...";
az webapp config connection-string set \
    -g $resourceGroup \
    -n $appName \
    --settings WWIF="$SQLAZURECONNSTR_WWIF" \
    --connection-string-type=SQLAzure

echo "Configuring Application Insights...";
az webapp config appsettings set \
    -g $resourceGroup \
    -n $appName \
    --settings APPINSIGHTS_KEY="$aikey"

echo "Done."