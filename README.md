---
page_type: sample
languages:
- python
- tsql
- sql
products:
- azure
- vs-code
- azure-sql-database
description: "Creating a modern REST API with Python and Azure SQL, using Flask and Visual Studio Code"
urlFragment: "azure-sql-db-python-rest-api"
---

# Creating a REST API with Python and Azure SQL

<!-- 
Guidelines on README format: https://review.docs.microsoft.com/help/onboard/admin/samples/concepts/readme-template?branch=master

Guidance on onboarding samples to docs.microsoft.com/samples: https://review.docs.microsoft.com/help/onboard/admin/samples/process/onboarding?branch=master

Taxonomies for products and languages: https://review.docs.microsoft.com/new-hope/information-architecture/metadata/taxonomies?branch=master
-->

Thanks to native JSON support, creating a REST API with Azure SQL and Python is really a matter of a few lines of code. Take a look at `app.py` to easy it is!

Wondering what's the magic behind? The sample uses the well known [Flask](https://flask.palletsprojects.com/en/1.1.x/) micro-framework and the [flask-restful](https://flask-restful.readthedocs.io/en/latest/) package to easily implement REST APIs. Beside that the [native JSON support that Azure SQL provides](https://docs.microsoft.com/en-us/azure/sql-database/sql-database-json-features) does all the heavy lifting so sending data back and forth to the database is as easy as sending a JSON message.

## Install Sample Database

In order to run this sample, the WideWorldImporters database is needed. Install WideWorldImporters sample database:

[Restore WideWorldImporters Database](https://github.com/yorek/azure-sql-db-samples#restore-wideworldimporters-database)

## Add Database Objects

Once the sample database has been installed, you need to add some stored procedure that will called from Python. The SQL code is available here:

`./sql/WideWorldImportersUpdates.sql`

If you need any help in executing the SQL script, you can find a Quickstart here: [Quickstart: Use Azure Data Studio to connect and query Azure SQL database](https://docs.microsoft.com/en-us/sql/azure-data-studio/quickstart-sql-database)

## Run sample locally

Make sure you have Python 3.7 installed on your machine. Clone this repo in a directory on our computer and then create a [virtual environment](https://www.youtube.com/watch?v=_eczHOiFMZA&list=PLlrxD0HtieHhS8VzuMCfQD4uJ9yne1mE6&index=34). For example:

```bash
virtualenv venv --python C:\Python37\
```

then activate the created virtual environment. For example, on Windows:

```powershell
.\venv\Scripts\activate
```

and then install all the required packages:

```bash
pip install -r requirements
```

The connections string is not saved in the python code for security reasons, so you need to assign it to an environment variable in order to run the sample successfully. You also want to enable [development environment](https://flask.palletsprojects.com/en/1.1.x/config/#environment-and-debug-features) for Flask:

Linux:

```bash
export FLASK_ENV="development"
export SQLAZURECONNSTR_WWIF="<your-connection-string>"
```

Windows:

```powershell
$Env:FLASK_ENV="development"
$Env:SQLAZURECONNSTR_WWIF="<your-connection-string>"
```

Your connection string is something like:

```
DRIVER={ODBC Driver 17 for SQL Server};SERVER=<your-server-name>.database.windows.net;DATABASE=<your-database-name>;UID=PythonWebApp;PWD=a987REALLY#$%TRONGpa44w0rd
```

Just replace `<your-server-name>` and `<your-database-name>` with the correct values for your environment.

To run and test the Python REST API local, just run

```bash
flask run
```

Python will start the HTTP server and when everything is up and running you'll see something like

```text
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

Using a REST Client (like [Insomnia](https://insomnia.rest/), [Postman](https://www.getpostman.com/) or curl), you can now call your API, for example:

```bash
curl -X GET http://localhost:5000/customer/123
```

and you'll get info on Customer 123:

```json
[
    {
        "CustomerID": 123,
        "CustomerName": "Tailspin Toys (Roe Park, NY)",
        "PhoneNumber": "(212) 555-0100",
        "FaxNumber": "(212) 555-0101",
        "WebsiteURL": "http://www.tailspintoys.com/RoePark",
        "Delivery": {
            "AddressLine1": "Shop 219",
            "AddressLine2": "528 Persson Road",
            "PostalCode": "90775"
        }
    }
]
```

Check out more samples to test all implemented verbs here:

[cUrl Samples](./sample-usage.md)

## Deploy to Azure

Now that your REST API solution is ready, it's time to deploy it on Azure so that anyone can take advantage of it. A detailed article on how you can that that is here:

- [Deploying Python web apps to Azure App Services](https://medium.com/@GeekTrainer/deploying-python-web-apps-to-azure-app-services-413cc16d4d68)
- [Quickstart: Create a Python app in Azure App Service on Linux](https://docs.microsoft.com/en-us/azure/app-service/containers/quickstart-python?tabs=bash)

The only thing you have do in addition to what explained in the above articles is to add the connection string to the Azure Web App configuration. Using AZ CLI, for example:

```bash
appName="azure-sql-db-python-rest-api"
resourceGroup="my-resource-group"

az webapp config connection-string set \
    -g $resourceGroup \
    -n $appName \
    --settings WWIF=$SQLAZURECONNSTR_WWIF \
    --connection-string-type=SQLAzure
```

Just make sure you correctly set `$appName` and `$resourceGroup` to match your environment and also that the variable `$SQLAZURECONNSTR_WWIF` as also been set, as mentioned in section "Run sample locally". An example of a full script that deploy the REST API is available here: `azure-deploy.sh`.

Please note that connection string are accessible as environment variables from Python when running on Azure, *but they are prefixed* as documented here:

https://docs.microsoft.com/en-us/azure/app-service/configure-common#connection-strings

That's why the Python code in the sample look for `SQLAZURECONNSTR_WWIF` but the Shell script write the `WWIF` connection string name.

## Learn more

If you're new to Python and want to learn more, there is a full free Python curse here:

- [Python for Beginners - Videos](https://aka.ms/python-for-beginners)
- [Python for Beginners - GitHub Repo](https://github.com/microsoft/c9-python-getting-started)

It will teach you not only how to use Python, but also how to take advantage the a great editor like Visual Studio Code.

Flask is a very common (and amazing!) framework. Learn how to use it right from Visual Studio Code with this tutorial:

[Flask Tutorial in Visual Studio Code](https://code.visualstudio.com/docs/python/tutorial-flask)

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
