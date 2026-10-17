export type V3 = [number, number, number];
export interface Delivery {ball:number; context:string; length:string; line:string; action:string; runs:number; out:boolean; wicket_type:string|null; score:number; speed_kph:number; duration:number; commentary:string; trajectory:{release:V3; bounce:V3; contact:V3; end:V3; arc:number}}
export interface Match {id:string; player_id:string; player_name:string; seed:number; target:number; score:number; wickets:number; won:boolean; events:Delivery[]; policy_version:number; exhibition:boolean}
export interface Player {id:string; name:string; power:number; timing:number; composure:number; version:number; training_balls:number; training_remaining?:number; cost?:number; lessons:{context:string; action:string; samples:number}[]}
export interface Metrics {runs_per_ball:number; wicket_rate:number; utility:number}
export interface Report {id:string; accepted:boolean; samples:number; policy_version:number; before:Metrics; candidate:Metrics; heuristic:Metrics; utility_delta:{mean:number;low:number;high:number}}
