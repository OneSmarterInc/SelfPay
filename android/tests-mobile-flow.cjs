const fs = require('node:fs');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
(async () => {
  const browser = await chromium.launch({headless:true});
  try {
    for (const width of [360, 393, 430]) {
      const page = await browser.newPage({viewport:{width,height:800}});
      const errors=[];page.on('pageerror',e=>errors.push(e.message));
      const entry={name:'Test Imaging',entity:'Direct operator',checked:'2026-10-03',coverage:'123 Main Street, Cincinnati, OH 45202 513-555-0100',source:'https://example.org',notes:''};
      const offer={id:'test-mri',entry,entry_name:entry.name,mod:'MRI',contrast:'without',scope:'Per body part; confirm ordered exam',type:'fixed',amount:350,included:'Scan and radiologist report',order:'Physician order required',region:'Cincinnati',distance_miles:11,distance_precision:'zip'};
      const offerList=Array.from({length:23},(_,i)=>({...offer,id:'test-mri-'+i,entry:{...entry,name:'Test Imaging '+(i+1)},amount:350+i}));
      await page.route('https://myselfpay.test/**',async route=>{
        const path=new URL(route.request().url()).pathname;
        if(path.startsWith('/api/')) {
          let data={},status=200;
          if(path==='/api/me') {status=401;data={error:'Sign in'};}
          if(path==='/api/guest')data={member:{tenant:'guest',name:'Guest'},csrf:'test'};
          if(path==='/api/catalog')data={entries:[entry],offers:offerList,version:'test'};
          if(path==='/api/guest-usage')data={usage:{}};
          if(path==='/api/directory-summary')data={listing_count:1,state_count:1};
          if(path==='/api/search') {
            const input=route.request().postDataJSON();
            const search=Object.fromEntries(['mod','body','contrast','location','budget','type','sort','radius'].map(key=>[key,input[key]]));
            data={search,offers:offerList,version:'test',resolved_location:{city:'Cincinnati'},program_entries:[{...entry,name:'Test program'}],program_heading:'Programs available in Ohio',nearby_unpriced:[{...entry,name:'Quote facility',distance_miles:5}]};
          }
          return route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
        }
        if(path==='/')return route.fulfill({contentType:'text/html',body:fs.readFileSync('static/index.html','utf8')});
        if(path==='/app.js')return route.fulfill({contentType:'text/javascript',body:fs.readFileSync('static/app.js','utf8')});
        return route.fulfill({status:404,body:''});
      });
      await page.goto('https://myselfpay.test/');
      await page.locator('#welcomeBegin').waitFor();
      const activity=fs.readFileSync('android/app/src/main/java/com/onesmarter/myselfpay/MainActivity.java','utf8');
      const baseCss=JSON.parse(activity.match(/String css=("(?:[^"\\]|\\.)*");/)[1]);
      await page.addStyleTag({content:baseCss+fs.readFileSync('android/app/src/main/assets/mobile-flow.css','utf8')});
      await page.addScriptTag({content:fs.readFileSync('android/app/src/main/assets/mobile-flow.js','utf8')});
      await page.evaluate(()=>document.getElementById('welcomeBegin').click());
      await page.locator('#mod').selectOption('MRI');
      await page.locator('#body').fill('Knee');
      await page.locator('#contrast').selectOption('without');
      await page.locator('#location').fill('Cincinnati, OH');
      fs.mkdirSync('mobile-qa',{recursive:true});
      await page.screenshot({path:`mobile-qa/search-${width}.png`});
      await page.locator('#searchForm button.primary').click();
      await page.locator('#mobileResultCategories').waitFor();
      assert.equal(await page.locator('#searchForm').isVisible(),false);
      assert.equal(await page.locator('.tabs').isVisible(),false);
      assert.equal(await page.locator('#explore').isVisible(),false);
      assert.equal(await page.locator('article.card:visible').count(),10);
      await page.locator('#mobileMoreResults').click();
      assert.equal(await page.locator('article.card:visible').count(),20);
      await page.locator('#mobileResultCategories button').filter({hasText:'Programs'}).click();
      assert.equal(await page.locator('article.card:visible').count(),1);
      await page.locator('article.card:visible summary').click();
      assert.equal(await page.locator('article.card:visible .card-actions a.call').isVisible(),true);
      await page.locator('#mobileResultCategories button').filter({hasText:'Request quote'}).click();
      assert.equal(await page.locator('article.card:visible').count(),1);
      await page.locator('#mobileResultCategories button').filter({hasText:'Offers'}).click();
      assert.equal(await page.locator('article.card:visible').count(),10);
      assert.match(await page.locator('article.card').first().innerText(),/\$350/);
      assert.equal(await page.getByText('Programs available in Ohio',{exact:true}).count(),1);
      assert.equal(await page.getByText('Facilities to contact for a quote',{exact:true}).count(),1,await page.locator('#app').innerText());
      fs.mkdirSync('mobile-qa',{recursive:true});
      await page.screenshot({path:`mobile-qa/results-${width}.png`,fullPage:false});
      await page.evaluate(()=>window.myselfpayOpenSearch());
      assert.equal(await page.locator('#searchForm').isVisible(),true);
      assert.equal(await page.locator('article.card:visible').count(),0);
      assert.equal(await page.locator('#body').inputValue(),'Knee');
      await page.evaluate(()=>window.myselfpayCloseOverlay());
      assert.equal(await page.locator('#searchForm').isVisible(),false);
      await page.locator('#mobileChatButton').click();
      await page.locator('#mobileCloseChat').waitFor();
      assert.equal(await page.locator('#chatForm').isVisible(),true);
      assert.equal(await page.locator('article.card:visible').count(),0);
      await page.screenshot({path:`mobile-qa/chat-${width}.png`});
      await page.locator('#mobileCloseChat').click();
      await page.locator('#mobileChatButton').waitFor();
      await page.locator('[data-select]').first().check();
      await page.locator('#compare').click();
      assert.equal(await page.locator('dialog[open]').count(),1);
      await page.locator('#closeModal').click();
      await page.locator('#clearCompare').click();
      assert.equal(await page.locator('[data-select]').first().isChecked(),false);
      await page.locator('[data-detail]').first().click();
      await page.locator('#back').waitFor();
      assert.match(await page.locator('#app').innerText(),/What the price includes/);
      await page.screenshot({path:`mobile-qa/details-${width}.png`,fullPage:false});
      await page.locator('#back').click();
      await page.locator('#mobileResultCategories').waitFor();
      assert.equal(await page.locator('#body').inputValue(),'Knee');
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      assert.deepEqual(errors,[]);
      await page.close();
    }
    console.log('Search icon, floating chat, compact results, categories, pagination, comparison and details passed at 360, 393 and 430px');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
