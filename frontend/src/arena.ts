import '@babylonjs/core/Lights/Shadows/shadowGeneratorSceneComponent';
import { Color3, Color4 } from '@babylonjs/core/Maths/math.color';
import { DefaultRenderingPipeline } from '@babylonjs/core/PostProcesses/RenderPipeline/Pipelines/defaultRenderingPipeline';
import { DirectionalLight } from '@babylonjs/core/Lights/directionalLight';
import { Engine } from '@babylonjs/core/Engines/engine';
import { FreeCamera } from '@babylonjs/core/Cameras/freeCamera';
import { HemisphericLight } from '@babylonjs/core/Lights/hemisphericLight';
import { ImageProcessingConfiguration } from '@babylonjs/core/Materials/imageProcessingConfiguration';
import { Mesh } from '@babylonjs/core/Meshes/mesh';
import { MeshBuilder } from '@babylonjs/core/Meshes/meshBuilder';
import { Scene } from '@babylonjs/core/scene';
import { ShaderMaterial } from '@babylonjs/core/Materials/shaderMaterial';
import { ShadowGenerator } from '@babylonjs/core/Lights/Shadows/shadowGenerator';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import { Cricketer, material } from './actor';
import { buildStadium } from './stadium';
import type { Delivery, Match } from './types';

export type CameraMode = 'director'|'end-on'|'aerial';
export interface Frame {index:number;completed:number;time:number;playing:boolean;finished:boolean;event:Delivery|null;fps:number;progress:number}
const clamp=(x:number,a=0,b=1)=>Math.max(a,Math.min(b,x));
const smooth=(x:number)=>{x=clamp(x);return x*x*(3-2*x);};
const v=(a:number[])=>Vector3.FromArray(a);

export class Arena {
  engine:Engine;
  scene:Scene;
  camera:FreeCamera;
  private batter:Cricketer;
  private bowler:Cricketer;
  private partner:Cricketer;
  private fielders:Cricketer[]=[];
  private homes:Vector3[]=[];
  private ball:Mesh;
  private ballShadow:Mesh;
  private stadium:ReturnType<typeof buildStadium>;
  private shadow:ShadowGenerator;
  private match:Match|null=null;
  private current=0;
  private time=0;
  private playing=false;
  private finished=false;
  private hasStarted=false;
  private lastFrame=0;
  private frames=0;
  private speed=1;
  private mode:CameraMode='director';
  private previousScore='';
  private frameTimes:number[]=[];
  private quality='balanced';
  private software=false;
  private pipeline:DefaultRenderingPipeline;
  private onFrame:(frame:Frame)=>void;
  private sound=false;
  private audio:AudioContext|null=null;
  private struck=false;
  private resize:ResizeObserver;
  private cameraPosition=new Vector3(29,19,34);
  private cameraTarget=new Vector3(0,1,-5);

  constructor(canvas:HTMLCanvasElement,onFrame:(frame:Frame)=>void) {
    this.onFrame=onFrame;
    this.engine=new Engine(canvas,true,{preserveDrawingBuffer:true,stencil:true,powerPreference:'high-performance'},false);
    this.software=/swiftshader|llvmpipe|software/i.test(this.engine.getGlInfo().renderer);
    this.engine.setHardwareScalingLevel(this.software?2:1/Math.min(window.devicePixelRatio,1.25));
    this.scene=new Scene(this.engine);this.scene.clearColor=new Color4(.035,.065,.09,1);
    this.scene.fogMode=Scene.FOGMODE_EXP2;this.scene.fogDensity=.0024;this.scene.fogColor=new Color3(.16,.22,.26);
    this.scene.imageProcessingConfiguration.toneMappingEnabled=true;this.scene.imageProcessingConfiguration.toneMappingType=ImageProcessingConfiguration.TONEMAPPING_ACES;
    this.scene.imageProcessingConfiguration.exposure=1.35;this.scene.imageProcessingConfiguration.contrast=1.12;
    this.camera=new FreeCamera('broadcast-camera',this.cameraPosition.clone(),this.scene);this.camera.minZ=.1;this.camera.maxZ=600;this.camera.fov=.83;this.camera.setTarget(this.cameraTarget);
    const ambient=new HemisphericLight('stadium-ambient',new Vector3(0,1,0),this.scene);ambient.intensity=.85;ambient.diffuse=new Color3(.78,.86,1);ambient.groundColor=new Color3(.18,.23,.2);
    const key=new DirectionalLight('floodlight-key',new Vector3(.45,-1,.3),this.scene);key.position=new Vector3(-30,48,-25);key.intensity=2.5;key.diffuse=new Color3(1,.9,.74);key.shadowMinZ=1;key.shadowMaxZ=160;key.orthoLeft=-32;key.orthoRight=32;key.orthoTop=32;key.orthoBottom=-32;
    this.shadow=new ShadowGenerator(1024,key);this.shadow.usePercentageCloserFiltering=!this.software;this.shadow.filteringQuality=ShadowGenerator.QUALITY_LOW;this.shadow.bias=.0005;this.shadow.normalBias=.015;this.shadow.darkness=.35;
    const fill=new DirectionalLight('stadium-fill',new Vector3(-.5,-1,-.2),this.scene);fill.intensity=.5;fill.diffuse=new Color3(.7,.85,1);
    this.sky();
    this.stadium=buildStadium(this.scene);
    this.batter=new Cricketer(this.scene,'batter','#427c80','17',true);this.batter.root.position.set(-.48,0,9.2);
    this.bowler=new Cricketer(this.scene,'bowler','#c38c55','09');this.bowler.root.rotation.y=Math.PI;this.bowler.root.position.set(.2,0,-24);
    this.partner=new Cricketer(this.scene,'non-striker','#427c80','08',true);this.partner.root.position.set(1.2,0,-8.5);this.partner.root.rotation.y=Math.PI;
    const positions=[[-5,13],[9,12],[20,0],[38,-18],[-28,-5],[-42,-25],[-11,-39],[21,-43],[45,8]];
    positions.forEach((p,i)=>{const f=new Cricketer(this.scene,'fielder-'+i,'#c38c55',String(12+i));f.root.position.set(p[0],0,p[1]);f.root.rotation.y=Math.atan2(-p[0],-p[1])+Math.PI;this.fielders.push(f);this.homes.push(f.root.position.clone());});
    const keeper=new Cricketer(this.scene,'keeper','#c38c55','01');keeper.root.position.set(0,-.12,13);keeper.root.scaling.y=.92;
    const umpire=new Cricketer(this.scene,'umpire','#e2dfcc','');umpire.root.position.set(-.5,0,-12.5);umpire.root.rotation.y=Math.PI;
    for(const actor of [this.batter,this.bowler,this.partner,keeper,umpire])for(const mesh of actor.meshes)this.shadow.addShadowCaster(mesh);
    this.ball=MeshBuilder.CreateSphere('cricket-ball',{diameter:.11,segments:16},this.scene);this.ball.material=material(this.scene,'ball-red','#c93035',.15);this.shadow.addShadowCaster(this.ball);
    const seam=MeshBuilder.CreateTorus('ball-seam',{diameter:.112,thickness:.008,tessellation:24},this.scene);seam.material=material(this.scene,'ball-seam-white','#ecbd9c');seam.parent=this.ball;seam.rotation.z=.6;
    this.ballShadow=MeshBuilder.CreateDisc('ball-ground-marker',{radius:.12,tessellation:16,sideOrientation:Mesh.DOUBLESIDE},this.scene);this.ballShadow.rotation.x=Math.PI/2;
    const shadowMat=material(this.scene,'ball-shadow','#07110d');shadowMat.alpha=.34;this.ballShadow.material=shadowMat;
    const pipeline=this.pipeline=new DefaultRenderingPipeline('broadcast-grade',true,this.scene,[this.camera]);pipeline.fxaaEnabled=true;pipeline.samples=1;pipeline.bloomEnabled=!this.software;pipeline.bloomThreshold=1.6;pipeline.bloomWeight=.14;pipeline.bloomKernel=32;pipeline.bloomScale=.35;
    this.resize=new ResizeObserver(()=>this.engine.resize());this.resize.observe(canvas);
    this.engine.runRenderLoop(()=>this.render());
  }

  private sky() {
    const sky=MeshBuilder.CreateSphere('dusk-sky',{diameter:500,segments:24,sideOrientation:Mesh.BACKSIDE},this.scene);
    const shader=new ShaderMaterial('dusk-gradient',this.scene,{
      vertexSource:'precision highp float; attribute vec3 position; uniform mat4 worldViewProjection; varying vec3 p; void main(){p=position;gl_Position=worldViewProjection*vec4(position,1.0);}',
      fragmentSource:'precision highp float; varying vec3 p; void main(){vec3 n=normalize(p);float h=clamp(n.y*2.2,0.0,1.0);vec3 color=mix(vec3(0.13,0.19,0.23),vec3(0.012,0.032,0.075),pow(h,0.55));float sun=pow(max(0.0,dot(n,normalize(vec3(-1.0,0.12,-0.7)))),14.0);color+=vec3(0.12,0.055,0.022)*sun;gl_FragColor=vec4(color,1.0);}'
    },{attributes:['position'],uniforms:['worldViewProjection']});shader.backFaceCulling=false;shader.disableDepthWrite=true;sky.material=shader;sky.infiniteDistance=true;sky.isPickable=false;
  }

  load(match:Match) {this.match=match;this.current=0;this.time=0;this.playing=false;this.finished=false;this.hasStarted=false;this.struck=false;this.previousScore='';this.resetActors();}
  toggle() {if(!this.match)return;if(this.finished)this.load(this.match);this.playing=!this.playing;if(this.playing)this.hasStarted=true;return this.playing;}
  replay() {if(this.match){this.load(this.match);this.playing=true;this.hasStarted=true;}}
  seek(index:number) {if(!this.match)return;this.current=clamp(index,0,this.match.events.length-1);this.time=0;this.finished=false;this.hasStarted=true;this.struck=false;this.resetActors();}
  setCamera(mode:CameraMode){this.mode=mode;}
  setSpeed(speed:number){this.speed=speed;}
  setQuality(high:boolean){this.quality=high?'high':'balanced';this.engine.setHardwareScalingLevel(high?1/Math.min(window.devicePixelRatio,2):this.software?2:1/Math.min(window.devicePixelRatio,1.25));this.shadow.filteringQuality=high?ShadowGenerator.QUALITY_MEDIUM:ShadowGenerator.QUALITY_LOW;this.shadow.usePercentageCloserFiltering=high||!this.software;this.pipeline.bloomEnabled=high||!this.software;}
  setSound(enabled:boolean){this.sound=enabled;if(enabled){this.audio??=new AudioContext();void this.audio.resume();}}

  private resetActors(){
    this.batter.root.position.set(-.48,0,9.2);this.batter.root.rotation.y=0;this.partner.root.position.set(1.2,0,-8.5);this.partner.root.rotation.y=Math.PI;
    this.fielders.forEach((f,i)=>f.root.position.copyFrom(this.homes[i]));
    this.scene.meshes.filter(m=>m.metadata?.bail).forEach(m=>{m.position.copyFrom(m.metadata.home);m.rotation.z=Math.PI/2;});
  }

  private hitSound() {
    if(!this.sound||!this.audio)return;
    const audio=this.audio,osc=audio.createOscillator(),gain=audio.createGain();osc.type='triangle';osc.frequency.setValueAtTime(520,audio.currentTime);osc.frequency.exponentialRampToValueAtTime(120,audio.currentTime+.06);gain.gain.setValueAtTime(.16,audio.currentTime);gain.gain.exponentialRampToValueAtTime(.001,audio.currentTime+.12);osc.connect(gain);gain.connect(audio.destination);osc.start();osc.stop(audio.currentTime+.13);
  }

  private animate(event:Delivery,t:number) {
    const release=2.55,bounce=3.02,contact=3.34;
    const run=clamp(t/release);
    this.bowler.root.position.set(.2,0,-23+run*13.6+clamp((t-release)/1.2)*2.8);
    this.bowler.pose(t<release?1:.25,t*10,t, t>1.8&&t<3.4?(t-release)*6:undefined);
    const swing=t<2.7?-.12:t<3.18?-.12-smooth((t-2.7)/.48)*1.5:t<3.6?-1.62+smooth((t-3.18)/.42)*3.3:1.68-smooth((t-4)/1.5)*1.8;
    this.batter.pose(0,0,swing);this.partner.pose(0,0,-.12);
    const trajectory=event.trajectory;
    if(t<release){this.ball.position.set(.2,1.1,this.bowler.root.position.z+.1);this.ball.setEnabled(t>1.6);}
    else if(t<bounce){const u=(t-release)/(bounce-release);this.ball.position.copyFrom(Vector3.Lerp(v(trajectory.release),v(trajectory.bounce),u));this.ball.position.y+=.35*Math.sin(u*Math.PI);this.ball.setEnabled(true);}
    else if(t<contact){const u=(t-bounce)/(contact-bounce);this.ball.position.copyFrom(Vector3.Lerp(v(trajectory.bounce),v(trajectory.contact),u));this.ball.position.y+=.16*Math.sin(u*Math.PI);}
    else {
      if(!this.struck){this.struck=true;if(event.wicket_type!=='bowled')this.hitSound();}
      const u=clamp((t-contact)/(event.runs>=4?3:2.2));
      if(event.wicket_type==='bowled') {
        this.ball.position.copyFrom(Vector3.Lerp(v(trajectory.contact),new Vector3(.03,.2,13.4),clamp((t-contact)/.28)));
        if(t>contact+.08)this.scene.meshes.filter(m=>m.metadata?.bail).forEach((m,i)=>{const k=clamp((t-contact-.08)/.7);m.position.copyFrom(m.metadata.home.add(new Vector3((i?1:-1)*k*.7,Math.sin(k*Math.PI)*.5-k*.65,k*1.4)));m.rotation.z=k*8;});
      } else {
        this.ball.position.copyFrom(Vector3.Lerp(v(trajectory.contact),v(trajectory.end),u));this.ball.position.y+=Math.sin(u*Math.PI)*trajectory.arc;
        const end=v(trajectory.end),nearest=this.homes.reduce((a,p,i)=>Vector3.DistanceSquared(p,end)<Vector3.DistanceSquared(this.homes[a],end)?i:a,0);
        if(event.runs<4){const f=this.fielders[nearest],progress=smooth((t-contact-.3)/3);f.root.position.copyFrom(Vector3.Lerp(this.homes[nearest],new Vector3(end.x,0,end.z),progress));f.root.rotation.y=Math.atan2(end.x-this.homes[nearest].x,end.z-this.homes[nearest].z)+Math.PI;f.pose(progress<1?.65:0,t*9,0);}
        if(event.runs>0&&event.runs<4&&!event.out&&t>4.15){
          const total=clamp((t-4.15)/(event.duration-4.6))*event.runs,leg=Math.min(event.runs-1,Math.floor(total)),part=total-leg,progress=leg%2?1-part:part;
          this.batter.root.position.set(-.65,0,9.2-progress*18);this.partner.root.position.set(1.2,0,-8.8+progress*18);
          this.batter.root.rotation.y=leg%2?Math.PI:0;this.partner.root.rotation.y=leg%2?0:Math.PI;
          this.batter.pose(.9,t*12,-.2);this.partner.pose(.9,t*12,-.2);
        }
      }
    }
    this.ball.rotation.x=t*26;this.ball.rotation.z=t*17;this.ballShadow.setEnabled(this.ball.isEnabled());this.ballShadow.position.set(this.ball.position.x,.042,this.ball.position.z);
    this.ballShadow.scaling.setAll(1+Math.max(0,this.ball.position.y)*.1);
    const hit=t>contact&&t<6.9&&event.wicket_type!=='bowled';
    if(this.mode==='aerial'){this.cameraPosition.set(18,58,22);this.cameraTarget.set(0,0,-2);this.camera.fov=.98;}
    else if(this.mode==='end-on'){this.cameraPosition.set(.4,4.5,27);this.cameraTarget.set(0,1,-5);this.camera.fov=.7;}
    else if(!this.hasStarted){this.cameraPosition.set(28,18,32);this.cameraTarget.set(0,2,-7);this.camera.fov=.85;}
    else if(hit){this.cameraPosition.set(-15,13,24);this.cameraTarget.copyFrom(Vector3.Lerp(new Vector3(0,1,0),this.ball.position,.58));this.camera.fov=1.02;}
    else {this.cameraPosition.set(1.3,5.3,28);this.cameraTarget.set(0,1,-5);this.camera.fov=.78;}
  }

  private render(){
    const now=performance.now(),elapsed=this.lastFrame?(now-this.lastFrame)/1000:0,delta=document.hidden?0:Math.min(elapsed,1);this.lastFrame=now;
    if(delta>0){this.frameTimes.push(elapsed*1000);if(this.frameTimes.length>1800)this.frameTimes.shift();}
    if(this.match){
      if(this.playing){this.time+=delta*this.speed;const event=this.match.events[this.current];if(this.time>=event.duration){if(this.current<this.match.events.length-1){this.time-=event.duration;this.current++;this.struck=false;this.resetActors();}else{this.time=event.duration;this.playing=false;this.finished=true;}}}
      const event=this.match.events[this.current];this.animate(event,this.time);
      const completed=this.finished?this.match.events.length:this.current;
      const score=completed?this.match.events[completed-1].score:0,wickets=this.finished?this.match.wickets:0,key=`${score}/${wickets}-${completed}`;
      if(key!==this.previousScore){this.previousScore=key;this.stadium.updateScreen(`${score} / ${wickets}`,`${Math.floor(completed/6)}.${completed%6} OVERS`);}
      this.onFrame({index:this.current,completed,time:this.time,playing:this.playing,finished:this.finished,event,fps:this.engine.getFps(),progress:(this.current+this.time/event.duration)/this.match.events.length});
    }
    const blend=1-Math.exp(-delta*4);this.camera.position.copyFrom(Vector3.Lerp(this.camera.position,this.cameraPosition,blend));
    const target=Vector3.Lerp(this.camera.getTarget(),this.cameraTarget,blend);this.camera.setTarget(target);
    this.scene.render();this.frames++;
    if(this.frames===3)document.querySelector('canvas')!.dataset.ready='true';
  }

  diagnostics(){const times=[...this.frameTimes].sort((a,b)=>a-b);return {engine:'Babylon.js',rendering:'browser WebGL',quality:this.quality,software_renderer:this.software,active_meshes:this.scene.getActiveMeshes().length,width:this.engine.getRenderWidth(),height:this.engine.getRenderHeight(),renderer:this.engine.getGlInfo().renderer,frames:this.frames,sample_frames:times.length,median_ms:times.length?times[Math.floor(times.length*.5)]:null,p95_ms:times.length?times[Math.floor(times.length*.95)]:null,current_fps:Math.round(this.engine.getFps()),camera:this.mode,ball:this.ball.position.asArray(),batter:this.batter.root.position.asArray(),note:'Measured on this browser. A 60 FPS target is not a guarantee; software-rendered tests do not establish GPU performance.'};}
  dispose(){this.resize.disconnect();this.engine.stopRenderLoop();this.audio?.close();this.scene.dispose();this.engine.dispose();}
}
