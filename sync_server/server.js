const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = Number(process.env.PORT || 8787);
const DATA_DIR = path.resolve(process.env.FENCE_SYNC_DATA || path.join(__dirname, "data"));
const MAX_BODY = 50 * 1024 * 1024;

fs.mkdirSync(DATA_DIR, { recursive: true });

function safeId(id) {
  return /^[a-z0-9-]{12,80}$/i.test(id || "") ? id : null;
}

function json(res, status, body) {
  const raw = Buffer.from(JSON.stringify(body), "utf8");
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": raw.length,
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET,PUT,OPTIONS",
    "access-control-allow-headers": "content-type",
    "cache-control": "no-store",
  });
  res.end(raw);
}

function text(res, status, body, contentType = "text/plain; charset=utf-8") {
  const raw = Buffer.from(body, "utf8");
  res.writeHead(status, {
    "content-type": contentType,
    "content-length": raw.length,
    "access-control-allow-origin": "*",
    "cache-control": "no-store",
  });
  res.end(raw);
}

function dataPath(id) {
  return path.join(DATA_DIR, `${id}.json`);
}

function keyPath(id) {
  return path.join(DATA_DIR, `${id}.key`);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on("data", chunk => {
      size += chunk.length;
      if (size > MAX_BODY) {
        reject(new Error("Payload er for stor."));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

function mobileHtml(syncId) {
  const dataUrl = JSON.stringify(`/api/sync/${syncId}`);
  return `<!doctype html>
<html lang="da">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Fence Planner Mobil</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <style>
    html, body, #map { height: 100%; margin: 0; background: #101613; font-family: Arial, sans-serif; }
    #top, #panel { position: fixed; left: 10px; right: 10px; z-index: 1000; background: rgba(20,30,24,.94); color: white; border-radius: 8px; padding: 10px; box-shadow: 0 8px 26px rgba(0,0,0,.35); }
    #top { top: 10px; display: grid; grid-template-columns: 1fr; gap: 8px; }
    #panel { bottom: 10px; }
    select, button { min-height: 40px; border: 0; border-radius: 6px; padding: 0 10px; color: white; font-size: 15px; font-weight: 700; min-width: 0; }
    select { background: #213126; }
    button { background: #237a42; }
    .row { display: flex; gap: 8px; }
    .row select { flex: 1; }
    .big { font-size: 32px; font-weight: 800; color: #54f27c; line-height: 1.05; }
    .meta { color: #dce7dd; margin-top: 5px; font-size: 13px; }
    .warn { color: #ffcf70; margin-top: 5px; font-size: 13px; }
    .gps { width: 18px; height: 18px; border-radius: 50%; background: #1d7dff; border: 3px solid white; box-shadow: 0 0 0 8px rgba(29,125,255,.24); }
  </style>
</head>
<body>
  <div id="map"></div>
  <div id="top">
    <select id="guideSelect"></select>
    <div class="row"><select id="fenceSelect"></select><button id="gps">GPS</button></div>
  </div>
  <div id="panel">
    <div class="big" id="distance">Ingen GPS</div>
    <div class="meta" id="meta">Henter marker...</div>
    <div class="warn" id="status"></div>
  </div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const DATA_URL = ${dataUrl};
    const R = 6378137;
    let cloud = null, guide = null, selectedFenceIndex = 0, origin = null, watchId = null, lastPosition = null;
    let boundaryLayer = null, fenceLayers = [], stakeLayer = null, gpsMarker = null, accuracyCircle = null;
    const map = L.map("map", { zoomControl: true }).setView([56, 10], 7);
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", { maxZoom: 20, attribution: "Tiles &copy; Esri" }).addTo(map);
    stakeLayer = L.layerGroup().addTo(map);
    function status(t){document.getElementById("status").textContent=t;}
    function toLatLng(p){return [p.lat,p.lon];}
    function toMeters(p){const c=Math.cos(origin.lat*Math.PI/180);return {east:(p.lon-origin.lon)*Math.PI*R*c/180,north:(p.lat-origin.lat)*Math.PI*R/180};}
    function crossTrackMeters(pos,start,end){const p=toMeters(pos),a=toMeters(start),b=toMeters(end);const vx=b.east-a.east,vy=b.north-a.north,len=Math.hypot(vx,vy);if(len<.001)return 0;return ((p.east-a.east)*vy-(p.north-a.north)*vx)/len;}
    async function loadCloud(){try{const r=await fetch(DATA_URL+"?ts="+Date.now(),{cache:"no-store"});cloud=await r.json();if(!r.ok||cloud.error)throw new Error(cloud.error||"Kunne ikke hente data.");if(!cloud.guides||!cloud.guides.length)throw new Error("Ingen marker fundet.");fillGuides();selectGuide(0);}catch(e){status("Fejl: "+(e.message||e));}}
    function label(g){return g.field.name+" - "+((g.plan&&g.plan.name)||"hegnsplan");}
    function fillGuides(){const s=document.getElementById("guideSelect");s.innerHTML="";cloud.guides.forEach((g,i)=>{const o=document.createElement("option");o.value=i;o.textContent=label(g);s.appendChild(o);});}
    function selectGuide(i){guide=cloud.guides[i];selectedFenceIndex=0;origin=guide.boundary[0]||guide.fences[0].start;drawGuide();updateDistance();}
    function drawGuide(){if(boundaryLayer)boundaryLayer.remove();fenceLayers.forEach(l=>l.remove());fenceLayers=[];stakeLayer.clearLayers();const fs=document.getElementById("fenceSelect");fs.innerHTML="";guide.fences.forEach((f,i)=>{const o=document.createElement("option");o.value=i;o.textContent=f.name+" · "+f.stakes.length+" pæle";fs.appendChild(o);});const bounds=[];if(guide.boundary.length){const b=guide.boundary.map(toLatLng);boundaryLayer=L.polygon(b,{color:"#47ff78",weight:2,fillColor:"#47ff78",fillOpacity:.12}).addTo(map);bounds.push(...b);}guide.fences.forEach((f,i)=>{const line=[toLatLng(f.start),toLatLng(f.end)];const l=L.polyline(line,{color:i===selectedFenceIndex?"#1d7dff":"#a9d4ff",weight:i===selectedFenceIndex?5:3}).addTo(map);l.bindTooltip(f.name);fenceLayers.push(l);bounds.push(...line);});drawSelectedStakes();if(bounds.length)map.fitBounds(bounds,{paddingTopLeft:[20,96],paddingBottomRight:[20,120],maxZoom:19});updateMeta();}
    function drawSelectedStakes(){stakeLayer.clearLayers();if(!guide)return;guide.fences[selectedFenceIndex].stakes.forEach((s,i)=>L.circleMarker(toLatLng(s),{radius:4,color:"#2d2500",weight:1,fillColor:"#ffd23d",fillOpacity:1}).bindTooltip("Pæl "+(i+1)).addTo(stakeLayer));fenceLayers.forEach((l,i)=>l.setStyle({color:i===selectedFenceIndex?"#1d7dff":"#a9d4ff",weight:i===selectedFenceIndex?5:3}));updateMeta();}
    function updateMeta(){if(!guide)return;const f=guide.fences[selectedFenceIndex];const mode=guide.settings.zone_mode||"Parallel";document.getElementById("meta").textContent=guide.field.name+" · "+mode+" · "+guide.settings.zone_count+" zoner · "+guide.settings.fence_count+" hegn · "+guide.settings.stake_spacing_m+" m pæleafstand · valgt: "+f.name;}
    function updateGps(p){lastPosition=p;const ll=[p.coords.latitude,p.coords.longitude];if(!gpsMarker)gpsMarker=L.marker(ll,{icon:L.divIcon({className:"",html:"<div class='gps'></div>",iconSize:[24,24],iconAnchor:[12,12]})}).addTo(map);else gpsMarker.setLatLng(ll);if(!accuracyCircle)accuracyCircle=L.circle(ll,{radius:p.coords.accuracy||0,color:"#1d7dff",weight:1,fillColor:"#1d7dff",fillOpacity:.12}).addTo(map);else{accuracyCircle.setLatLng(ll);accuracyCircle.setRadius(p.coords.accuracy||0);}updateDistance();}
    function updateDistance(){if(!guide||!lastPosition)return;const f=guide.fences[selectedFenceIndex];const d=crossTrackMeters({lat:lastPosition.coords.latitude,lon:lastPosition.coords.longitude},f.start,f.end);document.getElementById("distance").textContent=Math.abs(d).toFixed(2)+" m "+(d>0?"VENSTRE":"HØJRE");status("GPS nøjagtighed ca. "+Math.round(lastPosition.coords.accuracy||0)+" m");}
    function startGps(){if(!navigator.geolocation){status("Denne browser understøtter ikke GPS.");return;}if(watchId!==null)return;status(window.isSecureContext?"Venter på GPS-tilladelse...":"GPS kræver normalt HTTPS på mobilen.");watchId=navigator.geolocation.watchPosition(updateGps,e=>{watchId=null;status(e.code===1?"GPS blev afvist. Tillad placering for browseren.":"GPS-fejl: "+e.message);},{enableHighAccuracy:true,maximumAge:500,timeout:15000});}
    document.getElementById("guideSelect").addEventListener("change",e=>selectGuide(Number(e.target.value)));
    document.getElementById("fenceSelect").addEventListener("change",e=>{selectedFenceIndex=Number(e.target.value);drawSelectedStakes();updateDistance();});
    document.getElementById("gps").addEventListener("click",startGps);
    loadCloud(); startGps();
  </script>
</body>
</html>`;
}

async function handle(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  if (req.method === "OPTIONS") return json(res, 204, {});
  if (url.pathname === "/") return text(res, 200, "Fence Planner Sync Server\n");
  const mobile = url.pathname.match(/^\/s\/([a-z0-9-]+)$/i);
  if (req.method === "GET" && mobile) {
    const id = safeId(mobile[1]);
    if (!id) return text(res, 400, "Ugyldig sync-id");
    return text(res, 200, mobileHtml(id), "text/html; charset=utf-8");
  }
  const api = url.pathname.match(/^\/api\/sync\/([a-z0-9-]+)$/i);
  if (!api) return json(res, 404, { error: "Ikke fundet" });
  const id = safeId(api[1]);
  if (!id) return json(res, 400, { error: "Ugyldig sync-id" });

  if (req.method === "GET") {
    const file = dataPath(id);
    if (!fs.existsSync(file)) return json(res, 404, { error: "Der er ikke uploadet data til denne sync-kode endnu." });
    res.writeHead(200, { "content-type": "application/json; charset=utf-8", "access-control-allow-origin": "*", "cache-control": "no-store" });
    return fs.createReadStream(file).pipe(res);
  }

  if (req.method === "PUT") {
    const key = url.searchParams.get("key") || "";
    if (!key || key.length < 20) return json(res, 403, { error: "Upload-noegle mangler." });
    const kp = keyPath(id);
    if (fs.existsSync(kp) && fs.readFileSync(kp, "utf8") !== key) return json(res, 403, { error: "Forkert upload-noegle." });
    const raw = await readBody(req);
    let payload;
    try { payload = JSON.parse(raw); } catch { return json(res, 400, { error: "Ugyldig JSON." }); }
    if (payload.format !== "FencePlannerCloud" || !Array.isArray(payload.guides)) return json(res, 400, { error: "Ikke FencePlannerCloud data." });
    fs.writeFileSync(kp, key, "utf8");
    fs.writeFileSync(dataPath(id), JSON.stringify(payload), "utf8");
    return json(res, 200, { ok: true, guides: payload.guides.length, url: `/s/${id}` });
  }
  return json(res, 405, { error: "Metode ikke tilladt" });
}

http.createServer((req, res) => {
  handle(req, res).catch(err => json(res, 500, { error: err.message || String(err) }));
}).listen(PORT, () => {
  console.log(`Fence Planner sync server kører på http://127.0.0.1:${PORT}`);
  console.log(`Data: ${DATA_DIR}`);
});
