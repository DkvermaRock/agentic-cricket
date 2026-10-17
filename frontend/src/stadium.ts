import '@babylonjs/core/Meshes/thinInstanceMesh';
import { Color3 } from '@babylonjs/core/Maths/math.color';
import { DynamicTexture } from '@babylonjs/core/Materials/Textures/dynamicTexture';
import { Matrix, Vector3 } from '@babylonjs/core/Maths/math.vector';
import { Mesh } from '@babylonjs/core/Meshes/mesh';
import { MeshBuilder } from '@babylonjs/core/Meshes/meshBuilder';
import { Scene } from '@babylonjs/core/scene';
import { StandardMaterial } from '@babylonjs/core/Materials/standardMaterial';
import { VertexData } from '@babylonjs/core/Meshes/mesh.vertexData';
import { material } from './actor';

function sector(scene:Scene, name:string, r0:number, r1:number, y0:number, y1:number, a0:number, a1:number, mat:StandardMaterial) {
  const point=(r:number,y:number,a:number)=>[Math.sin(a)*r,y,Math.cos(a)*r];
  const positions=[...point(r0,y0,a0),...point(r0,y0,a1),...point(r1,y1,a1),...point(r1,y1,a0)];
  const indices=[0,1,2,0,2,3]; const normals:number[]=[]; VertexData.ComputeNormals(positions,indices,normals);
  const data=new VertexData(); data.positions=positions; data.indices=indices; data.normals=normals; data.uvs=[0,0,1,0,1,1,0,1];
  const mesh=new Mesh(name,scene); data.applyToMesh(mesh); mesh.material=mat; mat.backFaceCulling=false; mesh.scaling.x=1.08; mesh.freezeWorldMatrix(); return mesh;
}

function grass(scene:Scene) {
  const texture=new DynamicTexture('mown-grass',{width:1024,height:1024},scene,false);
  const ctx=(texture.getContext() as CanvasRenderingContext2D), pixels=ctx.createImageData(1024,1024);
  let seed=477;
  for(let y=0;y<1024;y++) for(let x=0;x<1024;x++) {
    seed=(Math.imul(seed,1664525)+1013904223)|0;
    const noise=(seed>>>24)/255*10, stripe=Math.floor(y/75)%2?9:0, i=(y*1024+x)*4;
    pixels.data[i]=36+noise+stripe; pixels.data[i+1]=76+noise+stripe; pixels.data[i+2]=42+noise+stripe; pixels.data[i+3]=255;
  }
  ctx.putImageData(pixels,0,0); texture.update(); texture.anisotropicFilteringLevel=8;
  const mat=material(scene,'turf','#ffffff'); mat.diffuseTexture=texture; mat.specularColor.set(.025,.035,.025); return mat;
}

export function buildStadium(scene:Scene) {
  const turf=MeshBuilder.CreateDisc('oval-outfield',{radius:61,tessellation:144,sideOrientation:Mesh.DOUBLESIDE},scene); turf.rotation.x=Math.PI/2; turf.scaling.x=1.08; turf.material=grass(scene); turf.receiveShadows=true;
  const apron=MeshBuilder.CreateDisc('ground-apron',{radius:100,tessellation:96,sideOrientation:Mesh.DOUBLESIDE},scene); apron.rotation.x=Math.PI/2; apron.position.y=-.12; apron.scaling.x=1.08; apron.material=material(scene,'apron','#1d292a');
  const pitch=MeshBuilder.CreateGround('pitch',{width:3.05,height:22.1},scene); pitch.position.y=.025; pitch.receiveShadows=true;
  const pitchTexture=new DynamicTexture('pitch-grain',{width:256,height:1024},scene,false), ctx=(pitchTexture.getContext() as CanvasRenderingContext2D);
  ctx.fillStyle='#b0a17b'; ctx.fillRect(0,0,256,1024);
  let rand=97; const random=()=>{rand=(Math.imul(rand,1664525)+1013904223)|0;return(rand>>>0)/4294967296;};
  for(let i=0;i<11000;i++){ctx.fillStyle=i%3?'rgba(65,51,27,.08)':'rgba(248,231,178,.12)';ctx.fillRect(random()*256,random()*1024,random()*2+1,random()*8+1);}
  ctx.strokeStyle='rgba(73,58,30,.14)';ctx.lineWidth=.8;
  for(let i=0;i<55;i++){const x=random()*256,y=random()*1024;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+random()*12,y+random()*30);ctx.lineTo(x-5,y+random()*60);ctx.stroke();}pitchTexture.update();
  const wicketMat=material(scene,'clay-pitch','#ffffff');wicketMat.diffuseTexture=pitchTexture;pitch.material=wicketMat;
  const chalk=material(scene,'crease-white','#f0efdc'), rope=material(scene,'boundary-rope','#e5dcc0');
  for(const sign of [-1,1]) {
    const crease=MeshBuilder.CreateGround('popping-crease',{width:3.66,height:.055},scene);crease.position.set(0,.034,sign*8.84);crease.material=chalk;
    const bowling=MeshBuilder.CreateGround('bowling-crease',{width:2.64,height:.045},scene);bowling.position.set(0,.035,sign*10.06);bowling.material=chalk;
    for(const x of [-1.32,1.32]) {const line=MeshBuilder.CreateGround('return-crease',{width:.045,height:2.5},scene);line.position.set(x,.036,sign*9.7);line.material=chalk;}
    for(const x of [-.114,0,.114]){const stump=MeshBuilder.CreateCylinder('stump',{height:.711,diameter:.038,tessellation:12},scene);stump.position.set(x,.38,sign*10.06);stump.material=chalk;}
    for(const x of [-.057,.057]){const bail=MeshBuilder.CreateCylinder('bail',{height:.12,diameter:.025,tessellation:8},scene);bail.rotation.z=Math.PI/2;bail.position.set(x,.75,sign*10.06);bail.material=rope;if(sign===1)bail.metadata={bail:true,home:bail.position.clone()};}
  }
  const path=Array.from({length:181},(_,i)=>new Vector3(Math.sin(i/180*Math.PI*2)*60.3*1.08,.055,Math.cos(i/180*Math.PI*2)*60.3));
  const boundary=MeshBuilder.CreateTube('boundary-rope',{path,radius:.055,tessellation:6},scene);boundary.material=rope;
  const stands=material(scene,'stand-concrete','#3a4949'), risers=material(scene,'stand-risers','#243737'), roof=material(scene,'roof-canopy','#273638'), steel=material(scene,'structural-steel','#384c50');
  const seatMat=material(scene,'seat-colors','#ffffff');seatMat.specularColor.set(0,0,0);
  const seat=MeshBuilder.CreateBox('seats',{width:.56,height:.31,depth:.49},scene);seat.material=seatMat;
  const spectator=MeshBuilder.CreateCapsule('crowd',{height:.65,radius:.16,tessellation:5,subdivisions:1},scene);spectator.material=seatMat;
  const seatMatrices:number[]=[],crowdMatrices:number[]=[],seatColors:number[]=[],crowdColors:number[]=[];
  const palette=['#a5a69d','#4a6b76','#a4936b','#405962','#64786a','#b7a99b'].map(Color3.FromHexString);
  const sectors=28;
  for(let s=0;s<sectors;s++) {
    const a0=s/sectors*Math.PI*2+.012,a1=(s+1)/sectors*Math.PI*2-.012;
    for(let row=0;row<12;row++) {
      const r=66+row*1.7, y=.75+row*.69;
      sector(scene,'terrace',r,r+1.7,y,y,a0,a1,stands);
      sector(scene,'riser',r+1.7,r+1.7,y,y+.69,a0,a1,risers);
      for(let j=0;j<16;j++) {
        const a=a0+(a1-a0)*(j+.5)/16, p=new Vector3(Math.sin(a)*(r+.9)*1.08,y+.25,Math.cos(a)*(r+.9));
        seatMatrices.push(...Matrix.Compose(Vector3.One(),QuaternionY(a),p).toArray());
        const c=Color3.FromHexString((row+s)%5===0?'#96856b':'#3c6267');seatColors.push(c.r,c.g,c.b,1);
        if(random()>.19){p.y+=.38;crowdMatrices.push(...Matrix.Compose(new Vector3(.8+random()*.3,.8+random()*.3,1),QuaternionY(a),p).toArray());const c=palette[Math.floor(random()*palette.length)];crowdColors.push(c.r,c.g,c.b,1);}
      }
    }
    sector(scene,'canopy',80,92,17,19.3,a0,a1,roof);
    const a=(a0+a1)/2;
    const col=MeshBuilder.CreateCylinder('roof-column',{height:18,diameter:.28,tessellation:8},scene);col.position.set(Math.sin(a)*89*1.08,9,Math.cos(a)*89);col.material=steel;col.freezeWorldMatrix();
    const rail=MeshBuilder.CreateTube('canopy-edge',{path:[new Vector3(Math.sin(a0)*80*1.08,17,Math.cos(a0)*80),new Vector3(Math.sin(a1)*80*1.08,17,Math.cos(a1)*80)],radius:.07,tessellation:6},scene);rail.material=material(scene,'roof-strip-'+s,s%2?'#709d94':'#385e64',.4);
  }
  seat.thinInstanceSetBuffer('matrix',new Float32Array(seatMatrices),16);seat.thinInstanceSetBuffer('color',new Float32Array(seatColors),4);
  spectator.thinInstanceSetBuffer('matrix',new Float32Array(crowdMatrices),16);spectator.thinInstanceSetBuffer('color',new Float32Array(crowdColors),4);
  for(let s=0;s<28;s++) {
    const tex=new DynamicTexture('sponsor-'+s,{width:512,height:64},scene,false), c=(tex.getContext() as CanvasRenderingContext2D);c.fillStyle=s%2?'#113b35':'#15272c';c.fillRect(0,0,512,64);c.fillStyle=s%2?'#bee6bd':'#d3d4be';c.font='bold 25px sans-serif';c.textAlign='center';c.fillText(s%2?'B O U N D A R Y':'THE AGENT ARENA',256,42);tex.update();
    const m=material(scene,'ad-'+s,'#ffffff',.08);m.diffuseTexture=tex;m.emissiveTexture=tex;
    const a=s/28*Math.PI*2, ad=MeshBuilder.CreatePlane('perimeter-board',{width:13.6,height:.95,sideOrientation:Mesh.DOUBLESIDE},scene);
    ad.position.set(Math.sin(a)*63*1.08,.53,Math.cos(a)*63);ad.rotation.y=a;ad.material=m;ad.freezeWorldMatrix();
  }
  const lamp=material(scene,'floodlight-panels','#f5e6c5',3), tower=material(scene,'floodlight-tower','#50636b');
  for(const angle of [.72,2.42,3.86,5.56]) {
    const x=Math.sin(angle)*75*1.08,z=Math.cos(angle)*75;
    for(const dx of [-.35,.35]){const mast=MeshBuilder.CreateCylinder('floodlight-mast',{height:30,diameter:.28,tessellation:8},scene);mast.position.set(x+dx,15,z);mast.material=tower;}
    for(let y=3;y<29;y+=2.5){const brace=MeshBuilder.CreateBox('mast-brace',{width:.9,height:.07,depth:.12},scene);brace.position.set(x,y,z);brace.rotation.z=.4;brace.material=tower;}
    const frame=MeshBuilder.CreateBox('lighting-rig',{width:5.7,height:2.5,depth:.4},scene);frame.position.set(x,30,z);frame.rotation.y=angle;frame.material=tower;
    for(let col=0;col<7;col++)for(let row=0;row<3;row++){const panel=MeshBuilder.CreatePlane('floodlight',{width:.57,height:.5,sideOrientation:Mesh.DOUBLESIDE},scene);panel.position.set(x+Math.cos(angle)*(col-3)*.76,29.2+row*.76,z-Math.sin(angle)*(col-3)*.76);panel.rotation.y=angle;panel.material=lamp;}
  }
  const screenTexture=new DynamicTexture('stadium-screen',{width:1024,height:512},scene,false);
  const screenMat=material(scene,'screen','#ffffff',.6);screenMat.diffuseTexture=screenTexture;screenMat.emissiveTexture=screenTexture;
  const screen=MeshBuilder.CreatePlane('scoreboard-screen',{width:17,height:8.5,sideOrientation:Mesh.DOUBLESIDE},scene);screen.position.set(0,13,-83);screen.material=screenMat;
  const screenFrame=MeshBuilder.CreateBox('screen-frame',{width:18,height:9.5,depth:.5},scene);screenFrame.position.set(0,13,-83.4);screenFrame.material=steel;
  const updateScreen=(score:string,over:string)=>{const c=(screenTexture.getContext() as CanvasRenderingContext2D);c.fillStyle='#10262b';c.fillRect(0,0,1024,512);c.textAlign='center';c.fillStyle='#c8ecbb';c.font='bold 42px sans-serif';c.fillText('BOUNDARY',512,92);c.fillStyle='#faf3da';c.font='bold 152px sans-serif';c.fillText(score,512,300);c.fillStyle='#8daca6';c.font='32px sans-serif';c.fillText('ARCADIA XI   ·   '+over,512,402);screenTexture.update();};
  updateScreen('0 / 0','0.0 OVERS');
  // Combine static architecture by material to avoid hundreds of terrace draws.
  const groups=new Map<StandardMaterial,Mesh[]>();
  for(const mesh of scene.meshes) {
    if(mesh instanceof Mesh && /^(terrace|riser|canopy|roof-column|floodlight-mast|mast-brace|lighting-rig|floodlight)$/.test(mesh.name) && mesh.material instanceof StandardMaterial) {
      const list=groups.get(mesh.material)??[];list.push(mesh);groups.set(mesh.material,list);
    }
  }
  for(const meshes of groups.values()) if(meshes.length>1){const merged=Mesh.MergeMeshes(meshes,true,true);merged?.freezeWorldMatrix();}
  return {updateScreen};
}

import { Quaternion } from '@babylonjs/core/Maths/math.vector';
function QuaternionY(angle:number){return Quaternion.RotationAxis(Vector3.Up(),angle);}
