// init-mongo.js  (replace the current file)

db = db.getSiblingDB('hw3');             // <── match the name in your MONGO_URL

// 1. bootstrap the application user *once*
db.getUsers().length === 0 && db.createUser({
  user:  'hw3user',
  pwd:   'hw3pass',
  roles: [{ role: 'readWrite', db: 'hw3' }]
});

// 2. OPTIONAL – if you still want the sample 'alice' doc used in slides
db.createCollection('users');
db.users.insertOne({
  email: 'alice@example.com',
  hash:  '$2a$10$CwTycUXWue0Thq9StjUM0uJ8DPLKXt1FYlwYpQW2G3cAwjKoh2WZK',
  username: 'alice',
  userID: '123'
});
