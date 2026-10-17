import { Color3 } from '@babylonjs/core/Maths/math.color';
import { DynamicTexture } from '@babylonjs/core/Materials/Textures/dynamicTexture';
import { Mesh } from '@babylonjs/core/Meshes/mesh';
import { MeshBuilder } from '@babylonjs/core/Meshes/meshBuilder';
import { Quaternion, Vector3 } from '@babylonjs/core/Maths/math.vector';
import { Scene } from '@babylonjs/core/scene';
import { StandardMaterial } from '@babylonjs/core/Materials/standardMaterial';
import { TransformNode } from '@babylonjs/core/Meshes/transformNode';

export function material(scene: Scene, name: string, color: string, glow = 0): StandardMaterial {
  const m = new StandardMaterial(name, scene);
  m.diffuseColor = Color3.FromHexString(color);
  m.specularColor = new Color3(.08, .08, .08);
  m.emissiveColor = m.diffuseColor.scale(glow);
  return m;
}

function joint(mesh: Mesh, a: Vector3, b: Vector3) {
  const direction = b.subtract(a);
  mesh.position.copyFrom(a.add(b).scale(.5));
  mesh.scaling.y = direction.length();
  direction.normalize();
  const axis = Vector3.Cross(Vector3.Up(), direction);
  mesh.rotationQuaternion = axis.lengthSquared() > .000001
    ? Quaternion.RotationAxis(axis.normalize(), Math.acos(Math.min(1, Math.max(-1, direction.y))))
    : Quaternion.RotationAxis(Vector3.Right(), direction.y > 0 ? 0 : Math.PI);
}

export class Cricketer {
  root: TransformNode;
  body: TransformNode;
  meshes: Mesh[] = [];
  bat: TransformNode;
  private arms: Mesh[][] = [];
  private legs: Mesh[][] = [];
  private hands: Mesh[] = [];
  private shoes: Mesh[] = [];
  private pads: Mesh[] = [];
  private shoulders = [new Vector3(-.28, 1.43, 0), new Vector3(.28, 1.43, 0)];
  private isBatter: boolean;

  constructor(scene: Scene, name: string, kit: string, number: string, batter = false) {
    this.isBatter = batter;
    this.root = new TransformNode(name, scene);
    this.body = new TransformNode(name + '-body', scene); this.body.parent = this.root;
    const jersey = material(scene, name+'-jersey', kit);
    const trousers = material(scene, name+'-trousers', batter ? '#dedbc8' : '#243439');
    const skin = material(scene, name+'-skin', '#ac7657');
    const white = material(scene, name+'-equipment', '#e8e5d9');
    const dark = material(scene, name+'-helmet', '#122b30');
    const rubber = material(scene, name+'-rubber', '#202a2a');
    const metal = material(scene, name+'-grille', '#b1bfc0'); metal.specularColor.set(.7,.7,.7);
    const add = (mesh: Mesh, mat: StandardMaterial, parent = this.body) => {
      mesh.material = mat; mesh.parent = parent; this.meshes.push(mesh); return mesh;
    };
    const torso = add(MeshBuilder.CreateCapsule('shirt', {height:.62, radius:.26, tessellation:14, subdivisions:2}, scene), jersey);
    torso.position.y=1.22; torso.scaling.set(1.08,1,.68);
    const waist = add(MeshBuilder.CreateSphere('waist',{diameter:.42,segments:12},scene),trousers);
    waist.position.y=.94; waist.scaling.set(1,.55,.65);
    const neck = add(MeshBuilder.CreateCylinder('neck',{height:.13,diameter:.14,tessellation:10},scene),skin); neck.position.y=1.55;
    const head = add(MeshBuilder.CreateSphere('head',{diameter:.33,segments:16},scene),skin); head.position.set(0,1.74,-.015); head.scaling.set(.9,1.13,.93);
    const nose = add(MeshBuilder.CreateSphere('nose',{diameter:.065,segments:8},scene),skin); nose.position.set(0,1.72,-.174);
    for (const x of [-.062,.062]) {
      const eye=add(MeshBuilder.CreateSphere('eye',{diameter:.022,segments:6},scene),rubber); eye.position.set(x,1.78,-.15);
    }
    const helmet=add(MeshBuilder.CreateSphere('helmet',{diameter:batter?.41:.35,segments:20,slice:.58},scene),dark);
    helmet.position.set(0,1.79,0); helmet.scaling.z=1.08;
    const brim=add(MeshBuilder.CreateBox('brim',{width:batter?.38:.29,height:.025,depth:.23},scene),dark); brim.position.set(0,1.82,-.17);
    if(batter) {
      for(const y of [1.61,1.68,1.75]) {
        add(MeshBuilder.CreateTube('helmet-grille',{path:[new Vector3(-.19,y,-.12),new Vector3(-.15,y,-.24),new Vector3(.15,y,-.24),new Vector3(.19,y,-.12)],radius:.008,tessellation:6},scene),metal);
      }
      for(const x of [-.15,0,.15]) add(MeshBuilder.CreateTube('helmet-bar',{path:[new Vector3(x,1.59,-.24),new Vector3(x,1.81,-.24)],radius:.007,tessellation:6},scene),metal);
    }
    const numberTexture = new DynamicTexture(name+'-number',{width:128,height:128},scene,false);
    const ctx=(numberTexture.getContext() as CanvasRenderingContext2D); ctx.clearRect(0,0,128,128); ctx.fillStyle='#f1f1de'; ctx.font='bold 68px sans-serif'; ctx.textAlign='center'; ctx.fillText(number,64,88); numberTexture.update(); numberTexture.hasAlpha=true;
    const decalMat = new StandardMaterial(name+'-decal',scene); decalMat.diffuseTexture=numberTexture; decalMat.emissiveColor.set(.3,.3,.3); decalMat.backFaceCulling=false;
    const decal=add(MeshBuilder.CreatePlane('shirt-number',{width:.28,height:.29},scene),decalMat); decal.position.set(0,1.3,.18); decal.rotation.y=Math.PI;
    for(let i=0;i<2;i++) {
      const arm=[add(MeshBuilder.CreateCylinder('sleeve',{height:1,diameter:.16,tessellation:12},scene),jersey),add(MeshBuilder.CreateCylinder('forearm',{height:1,diameter:.11,tessellation:12},scene),skin)]; this.arms.push(arm);
      const hand=add(MeshBuilder.CreateSphere('hand',{diameter:.115,segments:10},scene),batter?white:skin); this.hands.push(hand);
      const leg=[add(MeshBuilder.CreateCylinder('thigh',{height:1,diameter:.205,tessellation:12},scene),trousers),add(MeshBuilder.CreateCylinder('shin',{height:1,diameter:.145,tessellation:12},scene),trousers)]; this.legs.push(leg);
      const shoe=add(MeshBuilder.CreateCapsule('shoe',{height:.29,radius:.077,tessellation:10},scene),white); shoe.rotation.x=Math.PI/2; this.shoes.push(shoe);
      if(batter) {
        const pad=add(MeshBuilder.CreateCapsule('batting-pad',{height:.44,radius:.09,tessellation:12},scene),white); pad.scaling.z=.7; this.pads.push(pad);
        for(let rib=0;rib<3;rib++) {
          const strip=add(MeshBuilder.CreateCapsule('pad-ridge',{height:.37,radius:.013,tessellation:6},scene),white,pad);
          strip.position.set((rib-1)*.045,0,-.081);
        }
      }
    }
    this.bat=new TransformNode(name+'-bat-pivot',scene); this.bat.parent=this.body; this.bat.setEnabled(batter);
    const wood=material(scene,name+'-willow','#d8b17b');
    const blade=add(MeshBuilder.CreateBox('willow-blade',{width:.115,height:.57,depth:.065},scene),wood,this.bat); blade.position.y=-.55; blade.rotation.z=.015;
    const handle=add(MeshBuilder.CreateCylinder('bat-grip',{height:.32,diameter:.035,tessellation:12},scene),rubber,this.bat); handle.position.y=-.12;
    const sticker=add(MeshBuilder.CreateBox('bat-sticker',{width:.085,height:.23,depth:.003},scene),jersey,this.bat); sticker.position.set(0,-.41,-.034);
    this.pose(0,0,0);
  }

  pose(run: number, phase: number, swing: number, bowlingArm?: number) {
    this.body.position.y = Math.abs(Math.sin(phase*2)) * run * .055;
    this.body.rotation.x = run*.13;
    this.body.rotation.y = this.isBatter ? swing*.16 : 0;
    const hands = this.isBatter && run < .1;
    this.bat.position.set(.24,1.13,-.13);
    this.bat.rotation.set(swing,0,-.24);
    for(let i=0;i<2;i++) {
      const side=i===0?-1:1, step=Math.sin(phase+i*Math.PI)*run;
      const hip=new Vector3(side*.145,.91,0);
      const knee=new Vector3(side*.17,.48,-step*.24);
      const ankle=new Vector3(side*(hands?.24:.17),.13,step*.37);
      joint(this.legs[i][0],hip,knee); joint(this.legs[i][1],knee,ankle);
      this.shoes[i].position.copyFrom(ankle.add(new Vector3(0,-.025,-.065)));
      if(this.pads[i]) {this.pads[i].position.copyFrom(knee.add(ankle).scale(.5).add(new Vector3(0,0,-.075))); this.pads[i].rotationQuaternion=this.legs[i][1].rotationQuaternion;}
      let elbow=new Vector3(side*.34,1.1,step*.25), wrist=new Vector3(side*.27,.88,-.06-step*.25);
      if(hands) {
        wrist=new Vector3(.24+side*.025,1.13-(i*.075)*Math.cos(swing),-.13-(i*.075)*Math.sin(swing));
        elbow=new Vector3(side*.32,1.15,-.2-Math.max(0,swing)*.08);
      } else if(bowlingArm!==undefined && i===1) {
        elbow=new Vector3(.24,1.43+Math.cos(bowlingArm)*.3,-Math.sin(bowlingArm)*.3);
        wrist=new Vector3(.2,1.43+Math.cos(bowlingArm)*.65,-Math.sin(bowlingArm)*.65);
      }
      joint(this.arms[i][0],this.shoulders[i],elbow); joint(this.arms[i][1],elbow,wrist); this.hands[i].position.copyFrom(wrist);
    }
  }
}
