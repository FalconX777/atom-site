# atom-site

The static website "index.html" is stored and deployed on AWSAmplify.
The URL is https://dev810.d3hs2jwmllmwv9.amplifyapp.com

The backend service is deployed through AWSLambda, using "atom-counter.py".
The algorithm convert the molecule expression into a tree, and then count the atoms with a depth search.

This layer is linked with a database from DynamoDB, although it isn't used yet.

The interface between the user and AWSLambda is done using a REST API.
