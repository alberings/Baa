(function() {
  const apiKey = '51b95ae5-e0cd-4ec9-a4b3-8e1f7d3ae724';

  const sendEvent = (eventData) => {
    const endpoint = 'http://127.0.0.1:8000/api/events';
    fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'API-Key': apiKey
      },
      body: JSON.stringify(eventData),
      keepalive: true
    }).then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    }).then(data => {
      console.log('Success:', data);
    }).catch(error => {
      console.error('Error sending event:', error);
    });
  };

  // Page View and Visit Duration
  sendEvent({ type: 'pageview', path: window.location.href });
  window.addEventListener('unload', () => {
    sendEvent({
      type: 'duration',
      path: window.location.href,
      duration: Date.now() - performance.timing.navigationStart
    });
  });

  // Click Tracking
  document.addEventListener('click', (e) => {
    sendEvent({ type: 'click', path: window.location.href, target: e.target.tagName });
  });

  // Scroll Depth
  window.addEventListener('scroll', () => {
    const scrolledPercentage = ((window.scrollY + window.innerHeight) / document.documentElement.scrollHeight) * 100;
    sendEvent({ type: 'scroll', path: window.location.href, depth: scrolledPercentage.toFixed(2) });
  });

  // Form Interactions - Simplified Example
  document.addEventListener('submit', (e) => {
    sendEvent({ type: 'form_submit', path: window.location.href, formId: e.target.id });
  });

  document.addEventListener('mouseenter', (event) => {
    if (event.target.classList.contains('hover-sensitive')) {
      sendEvent({
        type: 'hover',
        path: window.location.href,
        target: event.target.tagName
      });
    }
  }, true);
})();
