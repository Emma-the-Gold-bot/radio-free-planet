<?php
declare(strict_types=1);

// IONOS-friendly stream proxy. Keeps CORS open while preventing open-proxy abuse.

header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Icy-Metadata');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

$target = $_GET['url'] ?? '';
if (!$target) {
    http_response_code(400);
    echo 'Missing required query parameter: url';
    exit;
}

$parts = parse_url($target);
if ($parts === false || !isset($parts['scheme'], $parts['host'])) {
    http_response_code(400);
    echo 'Invalid URL';
    exit;
}

if (!in_array($parts['scheme'], ['http', 'https'], true)) {
    http_response_code(400);
    echo 'Only http/https stream URLs are allowed';
    exit;
}

$host = strtolower($parts['host']);
$allowedHosts = [
    'streamguys1.com',
    'wmse.streamguys1.com',
    'npr-ice.streamguys1.com',
    'stream.cjsw.com',
    'floyd.wcbn.org',
    'wrfl.fm',
    'stream0.wfmu.org',
    'fm939.wnyc.org',
    'stream.wqxr.org',
    'q2stream.wqxr.org',
    'opera-stream.wqxr.org',
    'streams.kut.org',
    'kzsu-streams.stanford.edu',
    'stream.kalx.berkeley.edu',
    'somafm.com',
    'radiofrance.fr',
];

$allowed = false;
foreach ($allowedHosts as $candidate) {
    if ($host === $candidate || str_ends_with($host, '.' . $candidate)) {
        $allowed = true;
        break;
    }
}

if (!$allowed) {
    http_response_code(403);
    echo 'Host is not allowed';
    exit;
}

$ch = curl_init($target);
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => false,
    CURLOPT_FOLLOWLOCATION => true,
    CURLOPT_CONNECTTIMEOUT => 8,
    CURLOPT_TIMEOUT => 0,
    CURLOPT_BUFFERSIZE => 16384,
    CURLOPT_USERAGENT => 'RadioAgnostic/0.7 (+php-proxy)',
    CURLOPT_HTTPHEADER => ['Accept: audio/mpeg,audio/aac,audio/ogg,*/*', 'Icy-Metadata: 1'],
    CURLOPT_HEADERFUNCTION => function ($curl, $headerLine) {
        $trimmed = trim($headerLine);
        if ($trimmed === '' || str_starts_with($trimmed, 'HTTP/')) {
            return strlen($headerLine);
        }
        [$name, $value] = array_pad(explode(':', $trimmed, 2), 2, '');
        $name = strtolower(trim($name));
        $value = trim($value);
        $forward = ['content-type', 'icy-name', 'icy-genre', 'icy-br', 'icy-metaint', 'cache-control'];
        if (in_array($name, $forward, true)) {
            header($name . ': ' . $value, true);
        }
        return strlen($headerLine);
    },
]);

$ok = curl_exec($ch);
if ($ok === false) {
    $error = curl_error($ch);
    curl_close($ch);
    http_response_code(502);
    echo 'Upstream request failed: ' . $error;
    exit;
}

$status = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
if ($status < 200 || $status >= 300) {
    curl_close($ch);
    http_response_code(502);
    echo 'Upstream stream unavailable';
    exit;
}

curl_close($ch);
