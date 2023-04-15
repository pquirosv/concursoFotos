const express = require('express');
const morgan = require('morgan');
const app = express();

//Settings

//Middlewares
app.use(morgan('dev'));

//Routes


app.listen(3001, () => {
	console.log('Server on port 3001');
});
