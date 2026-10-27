// SPDX-License-Identifier: AGPL-3.0-only
// Projection only: no controller references, mutations, hidden targets or raw history.
const modes=['classic','finisher','milker','shortener','headplay','ultimate','ruin'];
const goals=['tease','survival','edgetrain','oracle','calibrate','nnn'];
const integer=(n,min,max)=>{
    if(!Number.isFinite(n)||n<min||n>max)throw new Error('Invalid observation');
    return Math.round(n);
};
export class Capture {
    constructor({uuid=()=>crypto.randomUUID(),now=()=>Date.now()}={}) {
        this.uuid=uuid;this.now=now;this.sessionId=uuid();this.previous=null;this.samples=[];this.lastHrTimestamp=null;
    }
    project(state,devices) {
        if(!modes.includes(state.teaseMode)||!goals.includes(state.gameMode||'tease')||
            ![...modes,'survival','oracle','edgetrain','calibrate'].includes(state.activeMode)||
            !['IDLE','RUNNING','PAUSED','RAMPDOWN'].includes(state.sessionStatus))throw new Error('Unknown upstream state');
        const now=this.now();
        const hr=devices.hr_ready&&Number.isFinite(state.sensorHr)&&state.sensorHr>=35&&state.sensorHr<=250?Math.round(state.sensorHr):null;
        if(hr!==null&&state.lastHrTimestamp!==this.lastHrTimestamp) {
            this.lastHrTimestamp=state.lastHrTimestamp;this.samples.push({at:now,bpm:hr});
            if(this.samples.length>12)this.samples.shift();
        }
        this.samples=this.samples.filter(s=>now-s.at<=15000);
        let trend='unknown';
        if(this.samples.length>=3&&this.samples.at(-1).at-this.samples[0].at>=2000) {
            const delta=this.samples.at(-1).bpm-this.samples[0].bpm;
            trend=delta>=3?'rising':delta<=-3?'falling':'steady';
        }
        if(this.previous?.status==='IDLE'&&state.sessionStatus==='RUNNING')this.sessionId=this.uuid();
        const signal=!devices.hr_ready?'missing':state.simEngaged?'ok':state.hrSignalState;
        const safety={signal,no_contact:Boolean(state.hrNoContact),watchdog_paused:Boolean(state.hrSignalPaused),
            fault:state.hrNoContact?'no_contact':signal==='stale'?'signal_lost':!devices.toy_ready?'device_unready':'none'};
        const snapshot={session_id:this.sessionId,status:state.sessionStatus,seconds:integer(state.sessionSeconds,0,31536000),
            experience:state.teaseMode,active_mode:state.activeMode,goal:state.gameMode||'tease',hr,
            effective_max:integer(state.effectiveMaxHr,30,400),pullback:integer(state.edgeTriggerHr??state.effectiveMaxHr,1,400),
            trend,edges:integer(state.edges,0,1000000),intensity:integer(50+state.intensityValue,50,150),
            movement:{primary:integer(state.strokerSpeed,0,100),secondary:integer(state.prostateSpeed,0,100),
                stroke_min:integer(state.strokeMin,0,100),stroke_max:integer(state.strokeMax,0,100)},
            devices:Object.fromEntries(['simulated_hr','hr_ready','toy_ready','ble','handy','intiface','tcode','vacuglide'].map(k=>[k,Boolean(devices[k])])),safety};
        const p=this.previous,kinds=[];
        if(p) {
            if(snapshot.status!==p.status)kinds.push(snapshot.status==='IDLE'?'stop':snapshot.status==='PAUSED'?'pause':p.status==='IDLE'?'session_started':'session_resumed');
            if(snapshot.edges>p.edges)kinds.push('edge');
            if(snapshot.experience!==p.experience||snapshot.goal!==p.goal)kinds.push('mode_changed');
            if(signal!==p.safety.signal)kinds.push(signal==='stale'?'signal_lost':p.safety.signal==='stale'?'signal_restored':null);
            if(safety.no_contact&&!p.safety.no_contact)kinds.push('no_contact');
            if(JSON.stringify(snapshot.devices)!==JSON.stringify(p.devices))kinds.push('device_changed');
            if(snapshot.seconds>=300&&Math.floor(snapshot.seconds/300)>Math.floor(p.seconds/300))kinds.push('milestone');
        }
        this.previous=snapshot;
        return {snapshot,events:kinds.filter(Boolean).map(kind=>({id:this.uuid(),kind}))};
    }
}
