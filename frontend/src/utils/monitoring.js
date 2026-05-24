/**
 * Frontend monitoring with Sentry integration.
 */
import * as Sentry from '@sentry/react';

/**
 * Initialize Sentry SDK for error tracking.
 * 
 * @param {Object} options - Configuration options
 * @param {string} options.dsn - Sentry DSN
 * @param {number} options.tracesSampleRate - Percentage of traces to send (0.0 to 1.0)
 * @param {string} options.environment - Environment name
 */
export function initSentry({ 
  dsn = import.meta.env.VITE_SENTRY_DSN,
  tracesSampleRate = parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || '0.1'),
  environment = import.meta.env.VITE_ENVIRONMENT || 'development'
} = {}) {
  if (!dsn) {
    console.log('Sentry DSN not configured, skipping initialization');
    return;
  }

  Sentry.init({
    dsn,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
    
    // Performance Monitoring
    tracesSampleRate,
    
    // Session Replay
    replaysSessionSampleRate: 0.1, // Sample 10% of sessions
    replaysOnErrorSampleRate: 1.0, // Sample 100% of sessions with errors
    
    environment,
    
    // Filter sensitive data
    beforeSend(event, hint) {
      // Remove sensitive data from URLs
      if (event.request && event.request.url) {
        event.request.url = event.request.url.replace(/([?&])(token|password|api_key)=[^&]*/gi, '$1$2=[Filtered]');
      }
      
      // Remove sensitive data from breadcrumbs
      if (event.breadcrumbs) {
        event.breadcrumbs = event.breadcrumbs.map(breadcrumb => {
          if (breadcrumb.data) {
            const filtered = { ...breadcrumb.data };
            ['password', 'token', 'api_key', 'secret'].forEach(key => {
              if (key in filtered) {
                filtered[key] = '[Filtered]';
              }
            });
            return { ...breadcrumb, data: filtered };
          }
          return breadcrumb;
        });
      }
      
      return event;
    },
  });

  console.log('Sentry initialized successfully');
}

/**
 * Capture an exception and send it to Sentry.
 * 
 * @param {Error} error - The error to capture
 * @param {Object} context - Additional context
 */
export function captureException(error, context = {}) {
  Sentry.withScope((scope) => {
    // Add context
    Object.keys(context).forEach(key => {
      scope.setContext(key, context[key]);
    });
    
    // Capture exception
    Sentry.captureException(error);
  });
}

/**
 * Capture a message and send it to Sentry.
 * 
 * @param {string} message - The message to capture
 * @param {string} level - Message level (debug, info, warning, error, fatal)
 * @param {Object} context - Additional context
 */
export function captureMessage(message, level = 'info', context = {}) {
  Sentry.withScope((scope) => {
    // Add context
    Object.keys(context).forEach(key => {
      scope.setContext(key, context[key]);
    });
    
    // Capture message
    Sentry.captureMessage(message, level);
  });
}

/**
 * Set user context for Sentry events.
 * 
 * @param {Object} user - User information
 * @param {string} user.id - User ID
 * @param {string} user.email - User email
 * @param {string} user.username - Username
 */
export function setUser(user) {
  if (user) {
    Sentry.setUser({
      id: user.id,
      email: user.email,
      username: user.username,
    });
  } else {
    // Clear user context
    Sentry.setUser(null);
  }
}

/**
 * Add breadcrumb for debugging.
 * 
 * @param {Object} breadcrumb - Breadcrumb data
 * @param {string} breadcrumb.message - Breadcrumb message
 * @param {string} breadcrumb.category - Breadcrumb category
 * @param {string} breadcrumb.level - Breadcrumb level
 * @param {Object} breadcrumb.data - Additional data
 */
export function addBreadcrumb({ message, category = 'custom', level = 'info', data = {} }) {
  Sentry.addBreadcrumb({
    message,
    category,
    level,
    data,
  });
}

export default {
  initSentry,
  captureException,
  captureMessage,
  setUser,
  addBreadcrumb,
};
