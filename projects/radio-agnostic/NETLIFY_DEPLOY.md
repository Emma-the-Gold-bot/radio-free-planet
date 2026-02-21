# Netlify Deployment - Radio Agnostic

## Files to Deploy

```
radio-agnostic/
├── netlify.toml          # Netlify configuration
├── netlify/
│   └── functions/
│       └── proxy.js      # CORS proxy serverless function
├── static/               # Your frontend files
│   ├── index.html
│   ├── app.js           # Updated with Netlify proxy URL
│   ├── styles.css
│   ├── scheduler.css
│   ├── manifest.json
│   └── data/
│       ├── stations.json    # All 50 stations
│       └── schedules.json   # All 50 schedules
```

## Deployment Steps

### 1. Sign up for Netlify
- Go to https://www.netlify.com
- Sign up with GitHub or email

### 2. Deploy
**Option A: Drag & Drop**
1. Zip the entire project folder
2. Go to https://app.netlify.com/drop
3. Drag and drop the zip file

**Option B: Git-based (recommended)**
1. Push code to GitHub
2. Connect repo in Netlify
3. Build settings:
   - Build command: (leave empty)
   - Publish directory: `static`

### 3. Domain Setup (optional)
- Add custom domain in Netlify settings
- Update DNS at IONOS to point to Netlify
- Or keep the free netlify.app subdomain

## How It Works

**Netlify Function URL:**
```
https://your-site.netlify.app/.netlify/functions/proxy?url=STREAM_URL
```

**All 50 stations will work** because:
- ✅ Netlify Functions support query strings
- ✅ No CORS restrictions
- ✅ Server-side proxy (bypasses browser blocks)
- ✅ Works with HTTP and HTTPS streams

## Testing

After deploy, test:
```
https://your-site.netlify.app/.netlify/functions/proxy?url=https://wmse.streamguys1.com/wmse128mp3
```

Should stream audio immediately.

## Free Tier Limits

- 125,000 function invocations/month
- 100 hours runtime/month
- For radio streaming: ~10,000 hours of listening

More than enough for personal use!
