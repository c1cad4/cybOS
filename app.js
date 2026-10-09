'use strict';
const categories={all:'Все проекты',system:'Система',intelligence:'Разум и память',network:'Связь и Web',security:'Безопасность',markets:'Рынки и сеть',physical:'Физический мир',experience:'Демонстрации'};
const statuses={planned:'В ПЛАНЕ',orchestrator:'ИНТЕГРАТОР',application:'ПРИЛОЖЕНИЕ',library:'БИБЛИОТЕКА',website:'САЙТ',demo:'ДЕМО',extension:'РАСШИРЕНИЕ',tool:'ИНСТРУМЕНТ','platform-limited':'APPLE SDK','workspace-limited':'UPSTREAM WORKSPACE'};
let projects=[],category='all';
function render(){
 const query=document.getElementById('search').value.trim().toLocaleLowerCase('ru');
 const visible=projects.filter(p=>(category==='all'||p.category===category)&&`${p.name} ${p.role}`.toLocaleLowerCase('ru').includes(query));
 const grid=document.getElementById('projects');grid.replaceChildren();
 for(const p of visible){
  const card=document.createElement('article');card.className='card';
  const top=document.createElement('div');top.className='card-top';
  const title=document.createElement('h3');title.textContent=p.name;
  const status=document.createElement('span');status.className='status';status.textContent=statuses[p.status]||p.status;
  top.append(title,status);
  const role=document.createElement('p');role.textContent=p.role;
  const tag=document.createElement('small');tag.textContent=categories[p.category];
  const link=document.createElement('a');link.href=p.url;link.textContent='Репозиторий и документация ↗';
  card.append(top,role,tag,link);grid.append(card);
 }
 document.getElementById('summary').textContent=`Показано ${visible.length} из ${projects.length} проектов`;
 document.getElementById('empty').hidden=visible.length>0;
}
for(const [key,title]of Object.entries(categories)){const b=document.createElement('button');b.textContent=title;b.setAttribute('aria-pressed',String(key===category));b.addEventListener('click',()=>{category=key;for(const other of document.querySelectorAll('#filters button'))other.setAttribute('aria-pressed',String(other===b));render();});document.getElementById('filters').append(b);}
document.getElementById('search').addEventListener('input',render);
fetch('ecosystem.json').then(r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json();}).then(data=>{projects=data.repositories;render();}).catch(()=>{document.getElementById('summary').textContent='Не удалось загрузить каталог. Запустите страницу через локальный HTTP-сервер.';});
