from fastapi import FastAPI

app = FastAPI(title="Observation Service", version="0.0.1")

@app.get("/")
def root():
    return {"message": "Hello, Observation Service"}

@app.get("/health")
def health():
    return {"ok": True, "service": "observation", "version": "0.0.1"}
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import List, Optional
import json, os

# your existing app = FastAPI(...) and routes stay above

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schemas", "prestart.schema.json")

class Check(BaseModel):
    area: str
    item: str
    status: str              # "Compliant" | "Non-compliant" | "N/A"
    note: Optional[str] = None
    photoUrl: Optional[str] = None

class Tyre(BaseModel):
    position: str            # e.g., "Front Left"
    treadDepthMm: Optional[float] = None
    condition: Optional[str] = None      # "OK" | "Damage" | "Needs Attention"
    pressureCheck: Optional[str] = None  # "Pass" | "Fail"

class Defect(BaseModel):
    natureOfFault: str
    workCarriedOutBy: Optional[str] = None
    dateWorkCompleted: Optional[str] = None  # ISO date
    comments: Optional[str] = None

class GeneralInfo(BaseModel):
    plantNumber: str
    date: str               # ISO date
    completedBy: str
    registrationDue: Optional[str] = None
    cofWofDue: Optional[str] = None
    hubKmReading: Optional[float] = None
    speedoReading: Optional[float] = None

class Prestart(BaseModel):
    generalInfo: GeneralInfo
    checks: List[Check]
    tyres: List[Tyre]
    defects: Optional[List[Defect]] = []

    @field_validator("checks")
    @classmethod
    def at_least_one_check(cls, v):
        if not v or len(v) < 1:
            raise ValueError("At least one check item is required")
        return v

PRESTART_STORE: List[Prestart] = []  # temp memory store (swap to DB later)

@app.get("/prestart/schema")
def get_prestart_schema():
    if not os.path.exists(SCHEMA_PATH):
        raise HTTPException(status_code=500, detail="Schema not found on server")
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)

@app.get("/prestart/example")
def prestart_example():
    return {
        "generalInfo": {
            "plantNumber": "TRK-4502",
            "date": "2025-08-29",
            "completedBy": "K. James",
            "registrationDue": "2025-12-01",
            "cofWofDue": "2025-10-15",
            "speedoReading": 65723
        },
        "checks": [
            {"area":"In cab","item":"Seat Belts","status":"Compliant"},
            {"area":"Vehicle exterior","item":"Lights/Indicators","status":"Non-compliant","note":"LH indicator cracked"}
        ],
        "tyres": [
            {"position":"Front Left","treadDepthMm":6.0,"condition":"OK","pressureCheck":"Pass"},
            {"position":"Front Right","treadDepthMm":2.5,"condition":"Needs Attention","pressureCheck":"Fail"}
        ],
        "defects": [
            {"natureOfFault":"Cracked LH indicator lens","comments":"Replace ASAP"}
        ]
    }

@app.post("/prestart")
def submit_prestart(payload: Prestart):
    PRESTART_STORE.append(payload)
    return {"status": "stored", "count": len(PRESTART_STORE)}
from fastapi.responses import HTMLResponse

FORM_HTML = r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>HSW Pre-Start</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body { font-family: system-ui, sans-serif; margin: 24px; }
    h1 { margin-bottom: 4px; }
    .row{ display:flex; gap:12px; flex-wrap:wrap; }
    .card{ border:1px solid #ddd; border-radius:12px; padding:16px; margin:12px 0; }
    label{ display:block; font-size:14px; margin:6px 0 2px; }
    input, select, textarea{ width:100%; padding:8px; border:1px solid #ccc; border-radius:8px; }
    .grid{ display:grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap:12px; }
    .btn{ padding:10px 14px; border:0; border-radius:10px; background:#111; color:#fff; cursor:pointer; }
    .pill{ display:inline-block;padding:4px 8px;border-radius:999px;background:#eee;margin-right:6px;font-size:12px }
    .ok{ background:#e7f7ee }
    .warn{ background:#fff2cc }
    .crit{ background:#ffe6e6 }
    .muted{ color:#666; font-size:12px }
    .inline{ display:flex; align-items:center; gap:8px }
  </style>
</head>
<body>
  <h1>Vehicle Pre-Start</h1>
  <div class="muted">This simple form renders from <code>/prestart/schema</code>.</div>

  <div id="app"></div>

  <script>
  const CHECK_ITEMS = [
    "Cab/Doors/Guards","Gauges","Lights/Indicators","Windshield/Wipers","Suspension",
    "Wheels/Rims/Wheel Nuts","Battery Box Secure","Alternator/Fan","Fuel Tank Secure",
    "Coolant Level","Mirrors Setup","Exhaust Secure","Brakes/Handbrakes","Guards Secure",
    "Load Secure","Seat Belts","Towing Connection Secure","Legal Weight/Dimensions",
    "Greased","Draw Bar Stand Secure","No Loose Items in Cab","Air/Electrical Lines Secure"
  ];
  const TYRE_POS = ["Front Left","Front Right","Rear Left Inner","Rear Left Outer","Rear Right Inner","Rear Right Outer"];

  const el = (tag, attrs={}, children=[])=>{
    const e = document.createElement(tag);
    Object.entries(attrs).forEach(([k,v])=> {
      if(k==="class") e.className=v;
      else if(k==="html") e.innerHTML=v;
      else e.setAttribute(k,v);
    });
    (Array.isArray(children)?children:[children]).filter(Boolean).forEach(c=>{
      if(typeof c==="string") e.appendChild(document.createTextNode(c));
      else e.appendChild(c);
    });
    return e;
  };

  async function main(){
    const schema = await fetch("/prestart/schema").then(r=>r.json());
    const root = document.getElementById("app");

    // GENERAL INFO
    const g = el("div",{class:"card"});
    g.appendChild(el("h3",{html:"General information"}));
    const fields = [
      ["plantNumber","Plant Number","text"],
      ["date","Date","date"],
      ["completedBy","Completed By","text"],
      ["registrationDue","Registration Due","date"],
      ["cofWofDue","COF/WOF Due","date"],
      ["hubKmReading","Hub/Km Reading","number"],
      ["speedoReading","Speedo Reading","number"],
    ];
    const ggrid = el("div",{class:"grid"});
    fields.forEach(([name,label,type])=>{
      const wrap = el("div");
      wrap.appendChild(el("label",{html:label, for:name}));
      wrap.appendChild(el("input",{id:name, name, type}));
      ggrid.appendChild(wrap);
    });
    g.appendChild(ggrid);

    // CHECKS
    const checksCard = el("div",{class:"card"});
    checksCard.appendChild(el("h3",{html:"Checks"}));
    const areas = ["Engine running","In cab","Vehicle exterior"];
    const checksWrap = el("div",{class:"grid"});
    areas.forEach(area=>{
      CHECK_ITEMS.forEach(item=>{
        const wrap = el("div",{class:"card"});
        wrap.appendChild(el("div",{class:"muted", html:`${area} · ${item}`}));
        const sel = el("select",{name:`check:${area}:${item}`},[
          el("option",{value:"Compliant",html:"Compliant ✅"}),
          el("option",{value:"Non-compliant",html:"Non-compliant ❌"}),
          el("option",{value:"N/A",html:"N/A"})
        ]);
        wrap.appendChild(sel);
        wrap.appendChild(el("label",{html:"Note"}));
        wrap.appendChild(el("input",{name:`note:${area}:${item}`,type:"text",placeholder:"Optional note"}));
        checksWrap.appendChild(wrap);
      });
    });
    checksCard.appendChild(checksWrap);

    // TYRES
    const tyres = el("div",{class:"card"});
    tyres.appendChild(el("h3",{html:"Tyres"}));
    const tgrid = el("div",{class:"grid"});
    TYRE_POS.forEach(pos=>{
      const w = el("div",{class:"card"});
      w.appendChild(el("div",{class:"muted",html:pos}));
      w.appendChild(el("label",{html:"Tread depth (mm)"}));
      w.appendChild(el("input",{name:`tyre:tread:${pos}`,type:"number",step:"0.1"}));
      w.appendChild(el("label",{html:"Condition"}));
      const cond = el("select",{name:`tyre:cond:${pos}`},[
        el("option",{value:"",html:"(select)"}),
        el("option",{value:"OK",html:"OK"}),
        el("option",{value:"Damage",html:"Damage"}),
        el("option",{value:"Needs Attention",html:"Needs Attention"})
      ]);
      w.appendChild(cond);
      w.appendChild(el("label",{html:"Pressure check"}));
      const pres = el("select",{name:`tyre:press:${pos}`},[
        el("option",{value:"",html:"(select)"}),
        el("option",{value:"Pass",html:"Pass"}),
        el("option",{value:"Fail",html:"Fail"})
      ]);
      w.appendChild(pres);
      tgrid.appendChild(w);
    });
    tyres.appendChild(tgrid);

    // DEFECTS (simple textbox for v1)
    const defects = el("div",{class:"card"});
    defects.appendChild(el("h3",{html:"Defects"}));
    defects.appendChild(el("textarea",{id:"defectsText",rows:"5",placeholder:"List any defects, one per line"}));

    // SUBMIT
    const submit = el("button",{class:"btn"}, "Submit Pre-Start");
    const result = el("div",{class:"card"});
    const alertsBox = el("div",{class:"card"});

    submit.onclick = async()=>{
      submit.disabled = true;
      result.innerHTML = "Submitting…";

      // Build payload
      const payload = {
        generalInfo: Object.fromEntries(fields.map(([name])=>[name, document.getElementById(name).value]).map(([k,v])=>{
          // coerce numbers
          if(["hubKmReading","speedoReading"].includes(k) && v!=="") return [k, Number(v)];
          return [k,v||null];
        })),
        checks: [],
        tyres: [],
        defects: []
      };

      // Collect checks
      areas.forEach(area=>{
        CHECK_ITEMS.forEach(item=>{
          const status = document.querySelector(`select[name="check:${area}:${item}"]`).value;
          const note = document.querySelector(`input[name="note:${area}:${item}"]`).value;
          // Only store if explicitly set or noted to keep payload smaller
          if (status || note){
            payload.checks.push({ area, item, status: status||"N/A", note: note||null });
          }
        });
      });

      // Collect tyres
      TYRE_POS.forEach(pos=>{
        const td = document.querySelector(`input[name="tyre:tread:${pos}"]`).value;
        const cond = document.querySelector(`select[name="tyre:cond:${pos}"]`).value;
        const pr = document.querySelector(`select[name="tyre:press:${pos}"]`).value;
        payload.tyres.push({
          position: pos,
          treadDepthMm: td===""? null: Number(td),
          condition: cond || null,
          pressureCheck: pr || null
        });
      });

      // Defects (one per line)
      const lines = document.getElementById("defectsText").value.split("\n").map(s=>s.trim()).filter(Boolean);
      payload.defects = lines.map(n => ({natureOfFault:n}));

      // Submit to backend
      const store = await fetch("/prestart", {
        method:"POST",
        headers:{ "content-type":"application/json" },
        body: JSON.stringify(payload)
      }).then(r=>r.json()).catch(e=>({error:String(e)}));

      result.innerHTML = "<b>Store result</b>: " + JSON.stringify(store);

      // Try evaluation if available
      try{
        const evalRes = await fetch("/prestart/evaluate",{
          method:"POST",
          headers:{ "content-type":"application/json" },
          body: JSON.stringify(payload)
        }).then(r=>r.json());

        alertsBox.innerHTML = "<h3>Alerts</h3>";
        if (!evalRes.alerts || evalRes.alerts.length===0){
          alertsBox.appendChild(el("div",{class:"pill ok"},"No alerts"));
        } else {
          evalRes.alerts.forEach(a=>{
            const cls = a.severity==="critical"?"crit":(a.severity==="warn"?"warn":"ok");
            const d = el("div",{class:`card ${cls}`},[
              el("div",{html:`<b>${a.severity.toUpperCase()}</b> · ${a.area} · ${a.item}`}),
              el("div",{class:"muted",html:a.recommendedAction || ""})
            ]);
            alertsBox.appendChild(d);
          });
        }
      }catch(e){
        alertsBox.innerHTML = "<div class='muted'>No evaluation endpoint found (optional).</div>";
      }

      submit.disabled = false;
      window.scrollTo({top: document.body.scrollHeight, behavior:"smooth"});
    };

    root.appendChild(g);
    root.appendChild(checksCard);
    root.appendChild(tyres);
    root.appendChild(defects);
    root.appendChild(el("div",{class:"inline"},[submit, el("div",{class:"muted",html:"&nbsp;Posts to /prestart then calls /prestart/evaluate"})]));
    root.appendChild(result);
    root.appendChild(alertsBox);
  }

  main().catch(err=>{
    document.getElementById("app").innerHTML = "<div class='card crit'>Failed to load schema. Is /prestart/schema live?</div>";
    console.error(err);
  });
  </script>
</body>
</html>
"""

@app.get("/form")
def form_ui():
    return HTMLResponse(FORM_HTML)
