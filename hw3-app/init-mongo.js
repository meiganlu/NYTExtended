// First create and switch to the hw3 database
db = db.getSiblingDB('hw3');

// Create the MongoDB user that will be used by your Flask app
db.createUser({
    user: 'hw3user',
    pwd: 'hw3pass',  
    roles: [{ role: 'readWrite', db: 'hw3' }]
});

// Create a collection and add a sample user
db.createCollection('users');
db.users.find().count() === 0 && db.users.insertOne({
    email: 'alice@example.com',
    hash: '$2a$10$CwTycUXWue0Thq9StjUM0uJ8DPLKXt1FYlwYpQW2G3cAwjKoh2WZK',
    username: 'alice',
    userID: '123'
});

// Create the comments collection
db.createCollection('comments');