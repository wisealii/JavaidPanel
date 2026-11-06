"use strict";
(()=>{
const $=id=>document.getElementById(id);
let token="",interval=null,invitation=null;
const status=(msg,bad=false)=>{const el=$("message");el.textContent=msg;el.className=bad?"error":"good"};
const setVisible=visible=>{for(const id of ["create-section","nodes-section"])$(id).classList.toggle("hidden",!visible);$("logout").disabled=!visible;$("refresh").disabled=!visible};
const forget=()=>{token="";$("admin-token").value="";$("login").disabled=false;setVisible(false);clearInterval(interval);interval=null;clearInvite();status("دسترسی موقت مرورگر پاک شد.")};
const clearInvite=()=>{invitation=null;$("invitation").classList.add("hidden");$("invitation-token").textContent="";$("install-command").textContent="";$("expiry").textContent=""};
async function api(path,method="GET",body){
 const headers={Authorization:"Bearer "+token};if(body!==undefined)headers["Content-Type"]="application/json";
 const response=await fetch(path,{method,headers,body:body===undefined?undefined:JSON.stringify(body),cache:"no-store",credentials:"omit",redirect:"error"});
 let result;try{result=await response.json()}catch{throw Error("پاسخ نامعتبر از API")}
 if(!response.ok){if(response.status===401){forget()}throw Error(response.status===401?"توکن مدیر نامعتبر است":result.error||"درخواست ناموفق بود")}
 return result;
}
function td(row,value,cls){const cell=document.createElement("td");cell.textContent=value??"—";if(cls)cell.className=cls;row.appendChild(cell);return cell}
function render(nodes){
 $("count-all").textContent=String(nodes.length);$("count-online").textContent=String(nodes.filter(n=>n.state==="online").length);
 $("count-offline").textContent=String(nodes.filter(n=>n.state==="offline").length);
 const body=$("nodes-body");body.replaceChildren();
 if(!nodes.length){const row=document.createElement("tr");td(row,"هنوز نودی ثبت نشده است.").colSpan=5;body.appendChild(row);return}
 for(const node of nodes){
   const tr=document.createElement("tr");td(tr,node.name);td(tr,node.host,"mono");
   const st=td(tr,node.state);st.className="status "+(node.state==="online"?"online":node.state==="offline"?"offline":node.state==="revoked"?"revoked":"");
   td(tr,node.last_seen?new Date(node.last_seen*1000).toLocaleString("fa-IR"):"—");
   const actions=document.createElement("td");
   if(node.state!=="revoked"){const btn=document.createElement("button");btn.className="tight danger";btn.textContent="ابطال";btn.addEventListener("click",async()=>{
      if(!confirm("دسترسی این نود باطل شود؟ این عملیات قابل برگشت نیست."))return;
      btn.disabled=true;try{await api("/api/v1/nodes/"+encodeURIComponent(node.id)+"/revoke","POST",{});status("دسترسی نود باطل شد.");await refresh()}catch(e){status(e.message,true)}finally{btn.disabled=false}
   });actions.appendChild(btn)} else actions.textContent="باطل‌شده";
   tr.appendChild(actions);body.appendChild(tr);
 }
}
async function refresh(){if(!token)return;try{const data=await api("/api/v1/nodes");render(Array.isArray(data.nodes)?data.nodes:[]);status("فهرست نودها به‌روز شد.")}catch(e){status(e.message,true)}}
function publicOrigin(value){
 const u=new URL(value);if(u.protocol!=="https:"||u.username||u.password||u.search||u.hash||u.pathname!=="/"||!u.hostname||
 !/^[A-Za-z0-9.-]+$/.test(u.hostname)||!u.hostname.includes(".")||u.hostname.includes(".."))throw Error("دامنه باید آدرس HTTPS معتبر، بدون مسیر و پارامتر باشد");
 if(u.port&&(Number(u.port)<1||Number(u.port)>65535))throw Error("پورت نامعتبر است");
 return u.origin;
}
async function clipboard(value){try{await navigator.clipboard.writeText(value);status("در کلیپ‌بورد کپی شد.")}catch{status("کپی خودکار مجاز نیست؛ متن را دستی انتخاب کنید.",true)}}
$("login").addEventListener("click",async()=>{
 const value=$("admin-token").value.trim();if(value.length<32){status("توکن مدیر باید حداقل ۳۲ کاراکتر باشد.",true);return}
 token=value;$("admin-token").value="";$("login").disabled=true;setVisible(true);await refresh();
 clearInterval(interval);interval=setInterval(refresh,15000);
});
$("logout").addEventListener("click",forget);$("refresh").addEventListener("click",refresh);
$("create-form").addEventListener("submit",async ev=>{
 ev.preventDefault();clearInvite();
 try{
  const origin=publicOrigin($("panel-url").value.trim()),ttl=Number($("ttl").value);
  if(!Number.isInteger(ttl)||ttl<1||ttl>30)throw Error("اعتبار توکن باید بین ۱ تا ۳۰ دقیقه باشد");
  $("create-button").disabled=true;
  const r=await api("/api/v1/nodes/enrollments","POST",{name:$("node-name").value.trim(),host:$("node-host").value.trim(),ttl:ttl*60});
  if(!/^[0-9a-fA-F-]{36}$/.test(r.enrollment_id)||typeof r.token!=="string")throw Error("اطلاعات ثبت ناقص است");
  const cmd="curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/node-agent-install.sh | sudo bash -s -- --panel "+origin+" --enrollment-id "+r.enrollment_id;
  invitation={token:r.token,command:cmd};
  $("install-command").textContent=cmd;$("invitation-token").textContent=r.token;
  $("expiry").textContent="انقضا: "+new Date(r.expires_at*1000).toLocaleString("fa-IR");
  $("invitation").classList.remove("hidden");
  status("نود ایجاد شد؛ دستور و توکن را فقط به مدیر VPS نود بدهید.");await refresh();
 }catch(e){status(e.message,true)}finally{$("create-button").disabled=false}
});
$("copy-command").addEventListener("click",()=>{if(invitation)clipboard(invitation.command)});
$("copy-token").addEventListener("click",()=>{if(invitation)clipboard(invitation.token)});
$("hide-token").addEventListener("click",()=>{clearInvite();status("توکن از صفحه پاک شد؛ توکن قبلی از دیتابیس قابل بازیابی نیست.")});
window.addEventListener("pagehide",()=>{token="";clearInvite();});
})();
