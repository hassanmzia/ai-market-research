'use strict';

/**
 * Global error-handling middleware.
 * Must be registered AFTER all routes (Express identifies error handlers by
 * their 4-parameter signature).
 */
function errorHandler(err, req, res, _next) {
  // Default to 500 if no status has been set
  const statusCode = err.statusCode || err.status || 500;

  const errorResponse = {
    success: false,
    error: {
      code: err.code || 'INTERNAL_ERROR',
      message: statusCode === 500 ? 'An internal server error occurred' : err.message || 'Unknown error',
    },
  };

  // Include stack trace only in development
  if (process.env.NODE_ENV !== 'production') {
    errorResponse.error.details = err.message;
    errorResponse.error.stack = err.stack;
  }

  // Log the error
  console.error(`[Error] ${req.method} ${req.originalUrl} -> ${statusCode}`, {
    message: err.message,
    code: err.code,
    stack: process.env.NODE_ENV !== 'production' ? err.stack : undefined,
  });

  res.status(statusCode).json(errorResponse);
}

/**
 * 404 handler for unknown routes. Register BEFORE errorHandler.
 */
function notFoundHandler(req, res) {
  res.status(404).json({
    success: false,
    error: {
      code: 'NOT_FOUND',
      message: `Route ${req.method} ${req.originalUrl} not found`,
    },
  });
}

module.exports = { errorHandler, notFoundHandler };
