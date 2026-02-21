// Netlify Serverless Function - CORS Proxy for Radio Streams
// Handles audio streaming with proper CORS headers

exports.handler = async (event, context) => {
  // Get URL from query parameter
  const url = event.queryStringParameters.url;
  
  if (!url) {
    return {
      statusCode: 400,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({ error: 'No URL provided' })
    };
  }

  // Validate URL (basic security)
  const decodedUrl = decodeURIComponent(url);
  const allowedPatterns = [
    /\.mp3/i, /\.aac/i, /\.ogg/i,
    /stream/i, /icecast/i, /shoutcast/i,
    /radio/i, /audio/i
  ];
  
  const isValid = allowedPatterns.some(pattern => pattern.test(decodedUrl));
  
  if (!isValid) {
    return {
      statusCode: 403,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({ error: 'URL not allowed', url: decodedUrl })
    };
  }

  try {
    // Fetch the stream
    const response = await fetch(decodedUrl, {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Radio Agnostic)',
        'Accept': 'audio/mpeg, audio/aac, audio/ogg, */*',
        'Icy-Metadata': '1'
      }
    });

    if (!response.ok) {
      return {
        statusCode: 502,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        body: JSON.stringify({ 
          error: 'Stream error', 
          status: response.status,
          url: decodedUrl 
        })
      };
    }

    // Get the response body as arrayBuffer for binary data
    const arrayBuffer = await response.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    // Get content type from original response
    const contentType = response.headers.get('content-type') || 'audio/mpeg';
    
    // Pass through icy metadata headers if present
    const icyName = response.headers.get('icy-name');
    const icyMetaInt = response.headers.get('icy-metaint');
    const icyBr = response.headers.get('icy-br');

    // Build response headers
    const headers = {
      'Content-Type': contentType,
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': '*'
    };

    if (icyName) headers['icy-name'] = icyName;
    if (icyMetaInt) headers['icy-metaint'] = icyMetaInt;
    if (icyBr) headers['icy-br'] = icyBr;

    return {
      statusCode: 200,
      headers: headers,
      body: buffer.toString('base64'),
      isBase64Encoded: true
    };

  } catch (error) {
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({ 
        error: 'Proxy error', 
        message: error.message,
        url: decodedUrl 
      })
    };
  }
};
