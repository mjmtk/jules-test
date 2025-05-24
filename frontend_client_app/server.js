// frontend_client_app/server.js
const jsonServer = require('json-server');
const server = jsonServer.create();
const router = jsonServer.router('db.json'); // Path to your db.json
const middlewares = jsonServer.defaults();
const path = require('path'); // Import path module

server.use(middlewares);

// Custom route for soft deleting a client
server.delete('/api/v1/clients/:id', (req, res, next) => {
  const db = router.db; // lowdb instance
  const clientId = req.params.id;
  const client = db.get('clients').find({ id: clientId }).value();

  if (client) {
    // Update the status_code to 'deleted' and set deleted_at
    db.get('clients')
      .find({ id: clientId })
      .assign({ status_code: 'deleted', deleted_at: new Date().toISOString() })
      .write(); // Persist changes to db.json
    
    // Send a 204 No Content response, as per the API spec
    res.sendStatus(204);
  } else {
    res.status(404).jsonp({ error: 'CLIENT_NOT_FOUND' });
  }
});

// To make routes.json work with programmatic server:
const routes = require('./routes.json'); // Load routes
server.use(jsonServer.rewriter(routes)); // Apply rewriter

server.use(router); // This should come after all custom routes and rewriter

server.listen(3001, () => {
  console.log('JSON Server with custom soft delete is running on port 3001');
});
