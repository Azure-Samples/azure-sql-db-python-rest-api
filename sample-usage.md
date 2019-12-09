# Sample REST API usage with cUrl

## Get a customer

```bash
curl -s -X GET http://localhost:5000/customer/123
```

## Create new customer

```bash
curl -s -X PUT http://localhost:5000/customer -d 'customer={"CustomerName": "John Doe", "PhoneNumber": "123-234-5678", "FaxNumber": "123-234-5678", "WebsiteURL": "http://www.something.com", "Delivery": { "AddressLine1": "One Microsoft Way", "PostalCode": 98052 }}'
```

## Update customer

```bash
curl -s -X PATCH http://localhost:5000/customer/123 -d 'customer={"CustomerName": "Jane Dean", "PhoneNumber": "231-778-5678" }'
```

## Delete a customer

```bash
curl -s -X DELETE http://localhost:5000/customer/123
```
