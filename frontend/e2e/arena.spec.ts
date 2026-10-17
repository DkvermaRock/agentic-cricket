import { expect, test } from '@playwright/test';

test('3D exhibition renders, animates, changes camera, and finishes the saved over',async({page},info)=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/');
  await expect(page.locator('canvas')).toHaveAttribute('data-ready','true',{timeout:60_000});
  await expect(page.locator('#scene-loading')).toBeHidden();
  const before=await page.evaluate(()=>(window as any).boundaryDiagnostics());
  expect(before.frames).toBeGreaterThan(2);expect(before.active_meshes).toBeGreaterThan(20);
  await page.screenshot({path:info.outputPath('arena-desktop.png'),fullPage:true});
  await page.getByRole('button',{name:'End-on',exact:true}).click();
  await expect.poll(()=>page.evaluate(()=>(window as any).boundaryDiagnostics().camera)).toBe('end-on');
  await page.getByRole('button',{name:'Play over',exact:true}).click();
  await expect.poll(()=>page.evaluate(()=>(window as any).boundaryDiagnostics().ball[2]),{timeout:15_000}).not.toBe(before.ball[2]);
  await page.getByRole('button',{name:'Pause over',exact:true}).click();
  const paused=await page.evaluate(()=>(window as any).boundaryDiagnostics().ball);
  await page.waitForTimeout(500);
  expect(await page.evaluate(()=>(window as any).boundaryDiagnostics().ball)).toEqual(paused);
  await page.getByRole('button',{name:'Aerial',exact:true}).click();
  await expect.poll(()=>page.evaluate(()=>(window as any).boundaryDiagnostics().camera)).toBe('aerial');
  await page.getByRole('button',{name:'Director',exact:true}).click();
  await page.getByRole('combobox',{name:'Playback speed'}).selectOption('2');
  await page.getByRole('button',{name:'Play over',exact:true}).click();
  await expect(page.locator('#result-overlay')).toBeVisible({timeout:60_000});
  await expect(page.locator('#score')).toHaveText('17/0');
  await expect(page.locator('#overs')).toHaveText('1.0');
  await expect(page.locator('#balls .done, #balls .boundary')).toHaveCount(6);
  await page.getByRole('button',{name:'Watch the replay',exact:true}).click();
  await expect(page.locator('#result-overlay')).toBeHidden();
  await expect(page.locator('#score')).toHaveText('0/0');
  expect(errors).toEqual([]);
});

test('create unique player, learn, record and reload a persistent match',async({page,request},info)=>{
  await page.goto('/');await expect(page.locator('canvas')).toHaveAttribute('data-ready','true',{timeout:60_000});
  await page.getByRole('button',{name:'Create a player',exact:true}).click();
  await page.getByLabel('PLAYER NAME',{exact:true}).fill('Nila Storm');
  await page.getByRole('button',{name:'Create player',exact:true}).click();
  await expect(page.locator('#player-name')).toHaveText('Nila Storm');
  await expect(page.locator('#coins')).toHaveText('54');
  await page.getByRole('button',{name:'Create a player',exact:true}).click();
  await page.getByLabel('PLAYER NAME',{exact:true}).fill(' NILA STORM ');
  await page.getByRole('button',{name:'Create player',exact:true}).click();
  await expect(page.locator('#form-error')).toContainText('already taken');
  await page.getByRole('button',{name:'Close player creation'}).click();
  await page.getByRole('button',{name:'Train 2,000 balls'}).click();
  await expect(page.locator('#practice-count')).toContainText('2,000');
  await expect(page.locator('#learning-report')).toBeVisible();
  const p=(await(await request.get('/api/players')).json()).find((p:any)=>p.name==='Nila Storm');
  expect([p.power,p.timing,p.composure]).toEqual([65,60,55]);
  const history=await(await request.get(`/api/players/${p.id}/matches`)).json();expect(history.length).toBeGreaterThan(0);
  await page.reload();await expect(page.locator('canvas')).toHaveAttribute('data-ready','true',{timeout:60_000});
  await page.getByRole('combobox',{name:'Select player'}).selectOption(p.id);
  await expect(page.locator('#practice-count')).toContainText('2,000');
  await expect(page.locator('#learning-report')).toBeVisible();
  const replay=(await(await request.get(`/api/players/${p.id}/matches`)).json()).find((m:any)=>m.id===history[0].id);
  expect(replay.events).toEqual(history[0].events);
  await page.screenshot({path:info.outputPath('learning.png'),fullPage:true});
});

test('mobile arena fits the viewport and supports the creation controls',async({page},info)=>{
  await page.setViewportSize({width:390,height:844});
  await page.goto('/');await expect(page.locator('canvas')).toHaveAttribute('data-ready','true',{timeout:60_000});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await page.getByRole('button',{name:'Create a player',exact:true}).click();
  await page.locator('#power').fill('95');await page.locator('#timing').fill('95');await page.locator('#composure').fill('95');
  await expect(page.locator('#creation-cost')).toHaveText('100');
  await expect(page.getByRole('button',{name:'Create player',exact:true})).toBeDisabled();
  await page.getByRole('button',{name:'Close player creation'}).click();
  await page.getByRole('button',{name:'Aerial',exact:true}).click();
  await expect(page.locator('#camera-label')).toHaveText('AERIAL CAMERA');
  await page.screenshot({path:info.outputPath('arena-mobile.png'),fullPage:true});
});

test('API failure shows a useful error rather than a false ready state',async({page})=>{
  await page.route('**/api/exhibition',route=>route.fulfill({status:503,json:{detail:'The exhibition is temporarily unavailable.'}}));
  await page.goto('/');
  await expect(page.locator('#notice')).toContainText('temporarily unavailable');
  await expect(page.locator('#scene-loading')).toContainText('could not start');
});
