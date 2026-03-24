/**
 * Report a caught error to the monitoring backend.
 * Fails silently — never throws.
 */
export async function reportError(error, errorInfo, componentName = 'unknown') {
  try {
    const payload = {
      message: error?.message || String(error),
      stack: error?.stack || '',
      component_stack: errorInfo?.componentStack || '',
      component_name: componentName,
      timestamp: new Date().toISOString(),
    };

    await fetch('/api/monitoring/errors/frontend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  } catch (fetchError) {
    // eslint-disable-next-line no-console
    console.error('Failed to report error to monitoring backend:', fetchError);
  }
}
